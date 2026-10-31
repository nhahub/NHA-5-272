"""Independent final review: stdlib CSV/Decimal; no pipeline functions imported.

Compares each emitted value with raw by PK, permitting only the exact C001 cell.
This is a second implementation check, not an independent human sign-off.
"""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import csv
import hashlib
import json

BASE=Path(__file__).resolve().parent      # 03_Data_Cleaning/scripts
REPORTS=BASE.parent/'reports'
ROOT=BASE.parent.parent              # project root


def read(path, key):
    with path.open(encoding='utf-8-sig',newline='') as handle:
        reader=csv.DictReader(handle)
        names=reader.fieldnames
        rows={}
        for row in reader:
            if None in row or None in row.values():
                raise ValueError(f'Malformed CSV: {path}')
            k=row[key]
            if k in ('',r'\N') or k in rows:
                raise ValueError(f'Invalid or duplicate primary key: {path}')
            rows[k]=row
    return names, rows


def verify(write_report=True):
    schema=json.loads((BASE/'cleaning_schema.json').read_text())['datasets']
    manifest=json.loads((REPORTS/'source_to_output_manifest.json').read_text())
    if {x['dataset'] for x in manifest}!=set(schema) or len(manifest)!=16:
        raise ValueError('Not exactly 16 unique output datasets')
    findings=[];changes=[];key_sets={};reference_values={};tax_errors=0;extended_errors=0
    for item in manifest:
        name=item['dataset'];spec=schema[name];key=spec['primary_key']
        source=ROOT/item['source'];output=ROOT/item['output']
        if source.resolve()==output.resolve():
            raise ValueError('Source/output overlap')
        for path,expected in [(source,item['source_sha256']),(output,item['output_sha256'])]:
            if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise ValueError(f'Fingerprint mismatch: {path}')
        columns,raw=read(source,key);out_columns,clean=read(output,key)
        if columns!=out_columns or set(raw)!=set(clean) or len(raw)!=spec['rows']:
            raise ValueError(f'Shape, keys or columns changed: {name}')
        nulls_before=nulls_after=0
        for k,original in raw.items():
            row=clean[k]
            for col in spec['columns']:
                field=col['name'];value=row[field];prior=original[field]
                nulls_before+=prior==r'\N';nulls_after+=value==r'\N'
                if value!=prior:
                    if (name,k,field,prior,value)!=('Warehouse_PackageTypes','13','PackageTypeName','Tub ','Tub'):
                        raise ValueError(f'Unapproved value change: {name} {k} {field}')
                    changes.append([name,k,field,repr(prior),repr(value)])
                if value==r'\N':
                    if not col['nullable']:
                        raise ValueError('NULL in non-nullable column')
                    continue
                if col['sql_type'] in ('decimal','numeric'):
                    number=Decimal(value)
                    if not number.is_finite() or number!=number.quantize(Decimal(1).scaleb(-col['scale'])):
                        raise ValueError('Decimal precision loss')
                if col['sql_type'] in ('date','datetime2','datetime'):
                    datetime.fromisoformat(value) # validation only; exact fractional text was compared above
            if name=='Sales_InvoiceLines':
                base=Decimal(row['Quantity'])*Decimal(row['UnitPrice'])
                expected=(base*Decimal(row['TaxRate'])/100).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
                tax_errors+=expected!=Decimal(row['TaxAmount'])
                extended_errors+=base+Decimal(row['TaxAmount'])!=Decimal(row['ExtendedPrice'])
        if nulls_before!=nulls_after:
            raise ValueError('NULL count changed')
        key_sets[name]=set(clean)
        reference_values[name]={fk['column']:{r[fk['column']] for r in clean.values()} for fk in spec['foreign_keys']}
        findings.append({'dataset':name,'rows':len(clean),'cells_compared':len(clean)*len(columns),
                         'NULL_cells':nulls_after,'status':'PASS'})
    relationships=[]
    for name,spec in schema.items():
        for fk in spec['foreign_keys']:
            if fk['parent'] not in key_sets:
                continue
            missing=reference_values[name][fk['column']]-{r'\N'}-key_sets[fk['parent']]
            if missing:
                raise ValueError(f'Orphan keys: {name}.{fk["column"]}')
            relationships.append(name+'.'+fk['column'])
    if len(changes)!=1 or tax_errors or extended_errors:
        raise ValueError('Unexpected correction count or financial inconsistency')
    latest=json.loads((REPORTS/'latest_run.json').read_text())
    if latest['status']!='COMPLETED':
        raise ValueError('Latest pipeline attempt did not complete')
    report={'status':'PASS','method':'Separate stdlib CSV/Decimal implementation, matched by primary key; no pipeline imports',
            'datasets':findings,'total_cells_compared':sum(x['cells_compared'] for x in findings),
            'changes':changes,'internal_relationships_checked':len(relationships),
            'tax_disagreements':tax_errors,'extended_price_disagreements':extended_errors,
            'limits':'Technical integrity reviewed; business caveats and external lookup scope remain. Not independent human approval.'}
    if write_report:
        (REPORTS/'independent_review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='datasets'},indent=2))
    return report


if __name__=='__main__':
    import sys
    # --check-only: verify everything but do not rewrite independent_review.json.
    verify(write_report='--check-only' not in sys.argv)
