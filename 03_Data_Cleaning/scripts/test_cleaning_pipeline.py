"""Small regression tests for dangerous conversion and validation edge cases."""
import io
import json
import unittest
import tempfile
from pathlib import Path
import hashlib
from unittest.mock import patch
from decimal import Decimal
import pandas as pd
from cleaning_pipeline import HERE, convert_column, serialize_column, clean_table, check_relationships, csv_bytes


class CleaningTests(unittest.TestCase):
    def spec(self, name, kind, nullable=True, scale=0, precision=18):
        return dict(name=name,sql_type=kind,nullable=nullable,scale=scale,precision=precision,max_length=100)

    def test_exact_money(self):
        s=pd.Series(['9999999999999999.99','0.10',pd.NA],dtype='string')
        spec=self.spec('Amount','decimal',scale=2)
        converted=convert_column(s,spec)
        self.assertEqual(converted[0],Decimal('9999999999999999.99'))
        self.assertTrue(serialize_column(converted,spec).equals(s))

    def test_reject_excess_scale_and_overflow(self):
        for value in ['1.001','10000000000000000.00','NaN','Infinity','1e2']:
            with self.assertRaises(ValueError):
                convert_column(pd.Series([value],dtype='string'),self.spec('Amount','decimal',scale=2))

    def test_reject_bad_integer_and_overflow(self):
        for value in ['1.1','2147483648','1e2',' 2']:
            with self.assertRaises((ValueError,TypeError)):
                convert_column(pd.Series([value],dtype='string'),self.spec('Quantity','int'))

    def test_identifier_stays_text(self):
        s=pd.Series(['13',pd.NA],dtype='string')
        self.assertTrue(convert_column(s,self.spec('SupplierID','int')).equals(s))

    def test_bad_date_is_not_null(self):
        with self.assertRaises(ValueError):
            convert_column(pd.Series(['2016-02-30'],dtype='string'),self.spec('OrderDate','date'))

    def test_timestamp_seven_digits(self):
        s=pd.Series(['2016-01-01T12:00:00.1234567',pd.NA],dtype='string')
        spec=self.spec('When','datetime2')
        self.assertTrue(serialize_column(convert_column(s,spec),spec).equals(s))

    def test_invalid_bit(self):
        with self.assertRaises(ValueError):
            convert_column(pd.Series(['2'],dtype='string'),self.spec('Status','bit'))

    def test_required_null_rejected(self):
        with self.assertRaises(ValueError):
            convert_column(pd.Series([pd.NA],dtype='string'),self.spec('Name','nvarchar',False))

    def test_null_empty_na_unicode_and_quotes_roundtrip(self):
        source=pd.DataFrame({'text':pd.Series([pd.NA,'','NA','NULL','a,b','a"b','مرحبا'],dtype='string')})
        reread=pd.read_csv(io.BytesIO(csv_bytes(source)),encoding='utf-8-sig',dtype='string',keep_default_na=False,na_values=[r'\N'])
        self.assertTrue(source.equals(reread))

    def test_c001_only_and_idempotent(self):
        spec=json.loads((HERE/'cleaning_schema.json').read_text())['datasets']['Warehouse_PackageTypes']
        raw=pd.DataFrame({'PackageTypeID':['13','14'],'PackageTypeName':['Tub ','Outer Box'],'LastEditedBy':['1','1']},dtype='string')
        before=raw.copy(deep=True)
        clean,text,audit=clean_table('Warehouse_PackageTypes',raw,spec)
        self.assertTrue(raw.equals(before))
        self.assertEqual(text.PackageTypeName.tolist(),['Tub','Outer Box'])
        self.assertEqual(sum(x['value_corrections'] for x in audit),1)
        self.assertTrue(clean_table('Warehouse_PackageTypes',text,spec)[1].equals(text))

    def test_unapproved_whitespace_correction_rejected(self):
        spec=json.loads((HERE/'cleaning_schema.json').read_text())['datasets']['Warehouse_PackageTypes']
        raw=pd.DataFrame({'PackageTypeID':['14'],'PackageTypeName':[' Box '],'LastEditedBy':['1']},dtype='string')
        with self.assertRaises(ValueError):
            clean_table('Warehouse_PackageTypes',raw,spec)

    def test_duplicate_and_missing_keys_rejected(self):
        spec=json.loads((HERE/'cleaning_schema.json').read_text())['datasets']['Warehouse_PackageTypes']
        for keys in [['13','13'],['13',pd.NA]]:
            raw=pd.DataFrame({'PackageTypeID':keys,'PackageTypeName':['Tub ','Box'],'LastEditedBy':['1','1']},dtype='string')
            with self.assertRaises(ValueError):
                clean_table('Warehouse_PackageTypes',raw,spec)

    def test_orphan_and_join_multiplication_detected(self):
        schema={'child':{'foreign_keys':[{'column':'ParentID','parent':'parent','parent_key':'ID'}]},'parent':{'foreign_keys':[]}}
        tables={'child':pd.DataFrame({'ParentID':['1',pd.NA,'9']},dtype='string'),'parent':pd.DataFrame({'ID':['1','1']},dtype='string')}
        result=check_relationships(tables,schema)[0]
        self.assertEqual(result['orphans'],1)
        self.assertFalse(result['parent_unique'])
        self.assertEqual(result['status'],'FAIL')

    def test_source_change_blocks_exports(self):
        from cleaning_pipeline import run_pipeline
        with tempfile.TemporaryDirectory() as temporary:
            from pathlib import Path
            base=Path(temporary)
            (base/'raw').mkdir()
            spec=json.loads((HERE/'cleaning_schema.json').read_text())['datasets']['Warehouse_PackageTypes']
            # Deliberately different bytes from the verified source fingerprint.
            (base/'raw/Warehouse_PackageTypes.csv').write_text('bad input',encoding='utf-8')
            (base/'cleaning_schema.json').write_text(json.dumps({'datasets':{'Warehouse_PackageTypes':spec}}))
            with patch('cleaning_pipeline.HERE',base),patch('cleaning_pipeline.RAW',base/'raw'),                 patch('cleaning_pipeline.REPORTS',base/'reports'),patch('cleaning_pipeline.RERUN_REPORTS',base/'reports/automated_rerun'):
                result=run_pipeline(export=True,output_root=base/'outputs')
            self.assertEqual(result['summary'].iloc[0]['status'],'FAIL')
            self.assertFalse((base/'outputs').exists())
            self.assertFalse((base/'reports/automated_rerun').exists())
            self.assertEqual(json.loads((base/'reports/latest_run.json').read_text())['status'],'FAIL')

    def test_manifest_paths_are_portable(self):
        from cleaning_pipeline import ROOT, REPORTS
        for item in json.loads((REPORTS/'source_to_output_manifest.json').read_text()):
            for field in ('source','output'):
                self.assertFalse(Path(item[field]).is_absolute(),item[field])
                self.assertTrue((ROOT/item[field]).is_file(),item[field])

    def test_typed_loader_matches_loading_schema(self):
        from load_cleaned_data import load_table
        from cleaning_pipeline import REPORTS
        expected=pd.read_csv(REPORTS/'Cleaned_CSV_Loading_Schema.csv',encoding='utf-8-sig',dtype='string')
        for name in ['Warehouse_PackageTypes','Warehouse_StockItems']:
            frame=load_table(name)
            rows=expected[expected.dataset==name]
            self.assertEqual({c:str(frame[c].dtype) for c in frame},dict(zip(rows.column,rows.required_dtype)))
        self.assertEqual(load_table('Warehouse_PackageTypes').set_index('PackageTypeID').loc['13','PackageTypeName'],'Tub')
        items=load_table('Warehouse_StockItems')
        self.assertTrue(all(isinstance(x,Decimal) for x in items.UnitPrice))
        self.assertEqual(str(items.Barcode.dtype),'string')
        self.assertEqual(int(items.Barcode.isna().sum()),219)


if __name__=='__main__':
    unittest.main(verbosity=2)
