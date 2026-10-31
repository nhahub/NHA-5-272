"""WWI cleaning v1: conservative corrections, exact types, gated CSV exports.

Run with the project .venv: python 03_Data_Cleaning/scripts/cleaning_pipeline.py
No SQL writes or raw CSV writes occur. See cleaning_schema.json for the frozen scope.

The curated v1.0.0 reports in ../reports/ (with the business-review dispositions)
are never rewritten: a rerun writes its automated reports to reports/automated_rerun/.
"""
from pathlib import Path
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import csv
import hashlib
import io
import json
import platform
import re

import pandas as pd

VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent              # 03_Data_Cleaning/scripts
WORKSPACE = HERE.parent                             # 03_Data_Cleaning
ROOT = WORKSPACE.parent                              # project root
RAW = ROOT / "00_Source_Data" / "CSV_Exports"
CLEANED = WORKSPACE / "cleaned_data"
REPORTS = WORKSPACE / "reports"
RERUN_REPORTS = REPORTS / "automated_rerun"


def project_path(path):
    """Portable manifest path: relative to the project root when inside it."""
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    return pd.read_csv(path, encoding="utf-8-sig", dtype="string",
                       keep_default_na=False, na_values=[r"\N"])


def require(condition, message):
    # Unlike assert, this guard also operates with python -O.
    if not condition:
        raise ValueError(message)


def convert_column(series, spec):
    """Reject invalid representations; never coerce unexpected text to NULL."""
    kind, name = spec["sql_type"], spec["name"]
    present = series.dropna()
    if not spec["nullable"]:
        require(series.notna().all(), f"{name}: NULL in required column")
    if kind == "int":
        require(present.str.fullmatch(r"-?(0|[1-9][0-9]*)").all(), f"{name}: invalid integer text")
        values = pd.to_numeric(series, errors="raise").astype("Int64")
        require(values.dropna().between(-2147483648, 2147483647).all(), f"{name}: outside SQL int range")
        # All primary/foreign identifiers remain string, including audit references.
        return series.copy() if name.endswith("ID") or name == "LastEditedBy" else values
    if kind == "bit":
        require(present.isin(["0", "1"]).all(), f"{name}: invalid bit")
        return series.map({"0": False, "1": True}).astype("boolean")
    if kind in ("decimal", "numeric"):
        scale, precision = spec["scale"], spec["precision"]
        require(present.str.fullmatch(r"-?\d+(\.\d+)?").all(), f"{name}: invalid decimal text")
        values = []
        for value in series:
            if pd.isna(value):
                values.append(pd.NA)
                continue
            number = Decimal(value)
            require(number.is_finite(), f"{name}: non-finite decimal")
            require(number == number.quantize(Decimal(1).scaleb(-scale)), f"{name}: excess decimal scale")
            require(abs(number) < Decimal(10) ** (precision - scale), f"{name}: decimal overflow")
            values.append(number)
        return pd.Series(values, index=series.index, name=name, dtype=object)
    if kind in ("date", "datetime2", "datetime"):
        pattern = r"\d{4}-\d{2}-\d{2}" if kind == "date" else r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,7})?"
        require(present.str.fullmatch(pattern).all(), f"{name}: unexpected date representation")
        fmt = "%Y-%m-%d" if kind == "date" else "ISO8601"
        return pd.to_datetime(series, format=fmt, errors="raise").astype("datetime64[ns]")
    require(kind in ("nvarchar", "varchar"), f"Unsupported SQL type: {kind}")
    if spec["max_length"] != -1:
        limit = spec["max_length"]
        lengths = present.map(lambda value: len(value.encode("utf-16-le")) if kind == "nvarchar" else len(value.encode("utf-8")))
        require(lengths.le(limit).all(), f"{name}: text exceeds SQL length")
    return series.copy()


def serialize_column(series, spec):
    """Return precision-preserving text; CSV does not itself retain pandas types."""
    kind = spec["sql_type"]
    if kind in ("decimal", "numeric"):
        return series.map(lambda x: pd.NA if pd.isna(x) else format(x, f'.{spec["scale"]}f')).astype("string")
    if kind == "bit":
        return series.map({False: "0", True: "1"}).astype("string")
    if kind == "date":
        return series.dt.strftime("%Y-%m-%d").astype("string")
    if kind in ("datetime2", "datetime"):
        def timestamp_text(x):
            if pd.isna(x):
                return pd.NA
            text = x.isoformat()
            return text.rstrip("0").rstrip(".") if "." in text else text
        return series.map(timestamp_text).astype("string")
    return series.astype("string")


def clean_table(name, raw, spec):
    """C001 changes a value; C002-C005 change in-memory types only."""
    key = spec["primary_key"]
    require(list(raw.columns) == [c["name"] for c in spec["columns"]], f"{name}: unexpected columns/order")
    require(raw[key].notna().all() and raw[key].is_unique, f"{name}: missing/duplicate primary key")
    require(not raw.duplicated().any(), f"{name}: duplicate full records")
    clean, text = raw.copy(), raw.copy()
    audit = []
    for col in spec["columns"]:
        field = col["name"]
        source = raw[field]
        changed = source.copy()
        rule = "P001"
        if name == "Warehouse_PackageTypes" and field == "PackageTypeName":
            changed = source.str.strip()
            mask = ~(source.eq(changed) | (source.isna() & changed.isna()))
            ids = raw.loc[mask.fillna(False), key].tolist()
            require(ids in ([], ["13"]), "C001: unexpected records need separate review")
            if ids:
                require(source[mask].item() == "Tub " and changed[mask].item() == "Tub", "C001: unexpected value")
            require(changed.dropna().is_unique, "C001: label collision")
            rule = "C001"
        typed = convert_column(changed, col)
        roundtrip = serialize_column(typed, col)
        require(roundtrip.equals(changed), f"{name}.{field}: conversion loses values or precision")
        require(source.isna().equals(typed.isna()), f"{name}.{field}: NULL mask changed")
        require(typed.index.equals(raw.index), f"{name}.{field}: row identity changed")
        clean[field], text[field] = typed, roundtrip
        if rule != "C001":
            if col["sql_type"] in ("date", "datetime2", "datetime"):
                rule = "C002"
            elif col["sql_type"] in ("decimal", "numeric"):
                rule = "C004"
            elif col["sql_type"] == "bit":
                rule = "C005"
            elif str(typed.dtype) == "Int64":
                rule = "C003"
        value_changes = ~(source.eq(roundtrip) | (source.isna() & roundtrip.isna()))
        audit.append({"dataset": name, "column": field, "rule": rule,
                      "sql_type": col["sql_type"], "before_dtype": str(source.dtype), "after_dtype": str(typed.dtype),
                      "converted_nonnull": int(source.notna().sum()) if str(source.dtype) != str(typed.dtype) else 0,
                      "value_corrections": int(value_changes.fillna(False).sum()),
                      "affected_ids": raw.loc[value_changes.fillna(False), key].tolist(),
                      "before_examples": [repr(v) for v in source[value_changes.fillna(False)].head(5)],
                      "after_examples": [repr(v) for v in roundtrip[value_changes.fillna(False)].head(5)],
                      "nulls_before": int(source.isna().sum()), "nulls_after": int(typed.isna().sum()),
                      "validation": "PASS: roundtrip, NULL mask and row identity",
                      "date_min": str(typed.min()) if col["sql_type"] in ("date", "datetime2", "datetime") else None,
                      "date_max": str(typed.max()) if col["sql_type"] in ("date", "datetime2", "datetime") else None})
    require(clean.shape == raw.shape, f"{name}: shape changed")
    require(clean[key].equals(raw[key]), f"{name}: primary keys changed")
    # One whole-table assertion covers all unrelated values, not just samples.
    expected = raw.copy()
    if name == "Warehouse_PackageTypes":
        expected["PackageTypeName"] = expected["PackageTypeName"].str.strip()
    require(text.equals(expected), f"{name}: unrelated values changed")
    return clean, text, audit


def check_relationships(tables, schema):
    rows = []
    for name, spec in schema.items():
        for fk in spec["foreign_keys"]:
            field, parent, pk = fk["column"], fk["parent"], fk["parent_key"]
            child = tables[name][field]
            if parent not in tables:
                rows.append({"dataset": name, "column": field, "parent": parent,
                             "nulls": int(child.isna().sum()), "orphans": None,
                             "status": "NOT VERIFIED: parent outside CSV scope"})
                continue
            parent_keys = tables[parent][pk]
            bad = child.notna() & ~child.isin(parent_keys)
            unique = parent_keys.notna().all() and parent_keys.is_unique
            # A unique right key makes a left join preserve the child row count.
            rows.append({"dataset": name, "column": field, "parent": parent,
                         "nulls": int(child.isna().sum()), "orphans": int(bad.sum()),
                         "parent_unique": bool(unique), "child_rows": len(child),
                         "status": "PASS" if unique and not bad.any() else "FAIL"})
    return rows


def business_review(tables, schema):
    """Record concerns; do not change plausible business values."""
    findings = []
    def record(name, rule, mask, reason, review=False):
        table = tables[name]
        mask = pd.Series(mask, index=table.index).fillna(False)
        count = int(mask.sum())
        findings.append({"dataset": name, "check": rule, "affected_rows": count,
                         "status": "NEEDS REVIEW" if review and count else "PASS",
                         "decision": "PRESERVE", "reason": reason,
                         "example_ids": table.loc[mask, schema[name]["primary_key"]].head(10).tolist()})
    for name, table in tables.items():
        for col in schema[name]["columns"]:
            field, kind = col["name"], col["sql_type"]
            s = table[field]
            if s.isna().any():
                record(name, f"Optional NULL: {field}", s.isna(), "Retained under SQL nullable schema; status/transaction context checked separately. No imputation.")
            if s.nunique(dropna=False) == 1:
                record(name, f"Constant column: {field}", pd.Series(True,index=table.index), "Constant in this sample; keep schema and values.")
            if kind in ("nvarchar", "varchar"):
                record(name, f"Remaining outer whitespace: {field}", s.notna() & s.ne(s.str.strip()), "No blanket text rewrite; review semantics before changing additional text.", True)
                record(name, f"Empty text: {field}", s.eq(""), "Empty text is distinct from NULL; retain pending context.", True)
    o=tables['Sales_Orders']; ol=tables['Sales_OrderLines']; inv=tables['Sales_Invoices']; il=tables['Sales_InvoiceLines']
    po=tables['Purchasing_PurchaseOrders']; pl=tables['Purchasing_PurchaseOrderLines']; st=tables['Warehouse_StockItemTransactions']; h=tables['Warehouse_StockItemHoldings']
    record('Sales_Orders','Picked timestamp without picker',o.PickingCompletedWhen.notna() & o.PickedByPersonID.isna(), 'Backorder association is evidence, not proof of why picker ID is absent; retain and seek business interpretation.',True)
    record('Sales_Orders','No picking timestamp',o.PickingCompletedWhen.isna(),'Do not fabricate completion; distinguish open/backorder state.')
    record('Sales_Invoices','No delivery timestamp',inv.ConfirmedDeliveryTime.isna(),'Incomplete delivery evidence near sample cutoff; retain, exclude only from metrics that require actual delivery.')
    record('Purchasing_PurchaseOrderLines','Zero receipts',pl.ReceivedOuters.eq(0),'Open/unfinished lines can have zero receipt and NULL last receipt date.')
    record('Purchasing_PurchaseOrderLines','Receipt status contradiction',(pl.ReceivedOuters.eq(0)&pl.LastReceiptDate.notna()) | (pl.ReceivedOuters.gt(0)&pl.LastReceiptDate.isna()) | (pl.IsOrderLineFinalized & pl.ReceivedOuters.eq(0)), 'Investigate status and receipt history; never invent a receipt.',True)
    record('Purchasing_PurchaseOrderLines','Received exceeds ordered',pl.ReceivedOuters.gt(pl.OrderedOuters),'Could be over-receipt; preserve pending review.',True)
    record('Sales_OrderLines','Picked exceeds quantity',ol.PickedQuantity.gt(ol.Quantity),'Inspect order-line semantics before changing.',True)
    record('Sales_InvoiceLines','Negative line profit',il.LineProfit.lt(0),'Stored loss is not corruption. Retain exact value; commercial reason unverified.',True)
    record('Warehouse_StockItemTransactions','Negative movement',st.Quantity.lt(0),'Stock Issue and Stocktake Adjustment quantities are signed; retained.')
    record('Warehouse_StockItemTransactions','Zero movement',st.Quantity.eq(0),'Zero stocktake adjustment can mean no adjustment needed; preserve.')
    record('Warehouse_StockItemTransactions','Movement sign/type conflict', (st.TransactionTypeID.eq('10') & st.Quantity.ge(0)) | (st.TransactionTypeID.eq('11') & st.Quantity.le(0)) | ~st.TransactionTypeID.isin(['10','11','12']), 'Expected current sample: issue negative, receipt positive, stocktake either sign/zero; new types require interpretation.',True)
    for name, a,b in [('Sales_Orders','ExpectedDeliveryDate','OrderDate'),('Purchasing_PurchaseOrders','ExpectedDeliveryDate','OrderDate'),('Sales_Invoices','ConfirmedDeliveryTime','InvoiceDate')]:
        record(name, f'{a} before {b}',tables[name][a].lt(tables[name][b]),'Invalid-looking chronology; preserve and investigate.',True)
    invoice_order_dates=inv.OrderID.map(o.set_index('OrderID').OrderDate)
    record('Sales_Invoices','Invoice before order',inv.InvoiceDate.lt(invoice_order_dates),'No header/line fan-out; mapped unique order date.',True)
    record('Sales_Invoices','Order-to-invoice delay over 365 days',inv.InvoiceDate.sub(invoice_order_dates).dt.days.gt(365),'Review heuristic, not a business SLA. Keep historical dates; no assumed correction.',True)
    record('Purchasing_PurchaseOrderLines','Receipt before order',pl.LastReceiptDate.lt(pl.PurchaseOrderID.map(po.set_index('PurchaseOrderID').OrderDate)),'Last receipt date is not a full partial-receipt history.',True)
    record('Warehouse_StockItemHoldings','Target below reorder',h.TargetStockLevel.lt(h.ReorderLevel),'Configuration relationship requires review; do not alter targets automatically.',True)
    for name,fields in {'Sales_OrderLines':['Quantity','PickedQuantity','UnitPrice'], 'Sales_InvoiceLines':['Quantity','UnitPrice','TaxAmount','ExtendedPrice'], 'Purchasing_PurchaseOrderLines':['OrderedOuters','ReceivedOuters','ExpectedUnitPricePerOuter'], 'Warehouse_StockItems':['QuantityPerOuter','LeadTimeDays','UnitPrice','RecommendedRetailPrice','TypicalWeightPerUnit','TaxRate'], 'Warehouse_StockItemHoldings':['QuantityOnHand','LastStocktakeQuantity','LastCostPrice','ReorderLevel','TargetStockLevel']}.items():
        for field in fields:
            record(name,f'Negative {field}',tables[name][field].lt(0),'Review in field/package/credit context; no automatic replacement.',True)
    # Exact Decimal arithmetic, using SQL-compatible commercial rounding.
    expected_tax=(il.Quantity.astype(object)*il.UnitPrice*il.TaxRate/Decimal('100')).map(lambda x:x.quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
    expected_extended=il.Quantity.astype(object)*il.UnitPrice+il.TaxAmount
    record('Sales_InvoiceLines','Tax arithmetic disagreement',il.TaxAmount.ne(expected_tax),'Exact line tax check at two decimals; review any disagreement.',True)
    record('Sales_InvoiceLines','Extended price disagreement',il.ExtendedPrice.ne(expected_extended),'ExtendedPrice compared with Quantity * UnitPrice + TaxAmount, exact decimals.',True)
    # A balance mismatch is a limitation, not a request to alter either dataset.
    movements=st.groupby('StockItemID').Quantity.sum()
    record('Warehouse_StockItemHoldings','Movement sum differs from snapshot',h.QuantityOnHand.ne(h.StockItemID.map(movements)),'Opening balances/complete history not established. Do not reconstruct inventory or force equality.',True)
    return findings


def outlier_review(tables, schema):
    """Float is used ONLY for exploratory IQR flags; never for stored money."""
    result=[]
    tests=[('Sales_OrderLines','Quantity',['StockItemID','PackageTypeID']),
           ('Sales_InvoiceLines','Quantity',['StockItemID','PackageTypeID']),
           ('Purchasing_PurchaseOrderLines','OrderedOuters',['StockItemID','PackageTypeID']),
           ('Purchasing_PurchaseOrderLines','ReceivedOuters',['StockItemID','PackageTypeID']),
           ('Purchasing_PurchaseOrderLines','ExpectedUnitPricePerOuter',['StockItemID','PackageTypeID']),
           ('Warehouse_StockItemHoldings','QuantityOnHand',[])]
    for name,col,groups in tests:
        table=tables[name]; values=table[col].astype(float)
        for scope in ['pooled'] + (['product/package'] if groups else []):
            if scope=='pooled':
                q1,q3=values.quantile(.25),values.quantile(.75); eligible=pd.Series(True,index=values.index)
            else:
                g=values.groupby([table[k] for k in groups]);q1=g.transform('quantile',q=.25);q3=g.transform('quantile',q=.75)
                eligible=g.transform('count').ge(4) # fewer than four observations: not assessed
            iqr=q3-q1;mask=eligible & (values.lt(q1-1.5*iqr) | values.gt(q3+1.5*iqr))
            examples=[]
            for idx in table.index[mask][:10]:
                first=q1.loc[idx] if isinstance(q1,pd.Series) else q1
                third=q3.loc[idx] if isinstance(q3,pd.Series) else q3
                examples.append({'id':table.loc[idx,schema[name]['primary_key']],
                                 'value':str(table.loc[idx,col]),
                                 'group':{g:str(table.loc[idx,g]) for g in groups},
                                 'Q1':float(first),'Q3':float(third),
                                 'lower':float(first-1.5*(third-first)),
                                 'upper':float(third+1.5*(third-first))})
            result.append({'dataset':name,'column':col,'scope':scope,'eligible_rows':int(eligible.sum()),
                           'flagged_rows':int(mask.sum()),'percent_of_all_rows':round(float(mask.mean()*100),4),
                           'example_ids':table.loc[mask,schema[name]['primary_key']].head(10).tolist(),
                           'examples':examples,
                           'decision':'PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error'})
    return result


def csv_bytes(frame):
    return frame.to_csv(index=False,na_rep=r'\N',quoting=csv.QUOTE_ALL,lineterminator='\n').encode('utf-8-sig')


def markdown_table(rows, columns):
    lines=['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|']
    for row in rows:
        lines.append('| '+' | '.join(str(row.get(c,'' )).replace('|','/').replace('\n',' ') for c in columns)+' |')
    return '\n'.join(lines)


def run_pipeline(export=True, output_root=None):
    schema=json.loads((HERE/'cleaning_schema.json').read_text(encoding='utf-8'))['datasets']
    latest=REPORTS/'latest_run.json'
    if export:
        latest.parent.mkdir(parents=True,exist_ok=True)
        latest.write_text(json.dumps({'status':'RUNNING','version':VERSION}),encoding='utf-8')
    raw={};clean={};texts={};audit=[];failures={}
    for name,spec in schema.items():
        try:
            path=RAW/(name+'.csv')
            require(sha256(path)==spec['sha256'], f'{name}: source fingerprint changed; reconcile before cleaning')
            raw[name]=read_csv(path)
            require(len(raw[name])==spec['rows'], f'{name}: source count changed')
            clean[name],texts[name],steps=clean_table(name,raw[name],spec)
            audit.extend(steps)
        except Exception as exc:
            failures[name]=str(exc)
    # Missing tables make cross-table validation incomplete. Fail closed for exports.
    if failures:
        report={'version':VERSION,'failures':failures,'exported':False}
        if export:
            latest.write_text(json.dumps({'status':'FAIL',**report},indent=2),encoding='utf-8')
        return {'report':report,'raw':raw,'clean':clean,'summary':pd.DataFrame([{'dataset':n,'status':'FAIL' if n in failures else 'NEEDS REVIEW','reason':failures.get(n,'Cross-table validation blocked')} for n in schema])}
    raw_fk=check_relationships(raw,schema);fk=check_relationships(texts,schema)
    require(raw_fk==fk,'Relationships changed during transformation')
    business=business_review(clean,schema);outliers=outlier_review(clean,schema)
    summary=[]
    for name,spec in schema.items():
        r,t=raw[name],texts[name];key=spec['primary_key']
        failed_fk=[x for x in fk if x['dataset']==name and x['status']=='FAIL']
        review=[x for x in business if x['dataset']==name and x['status']=='NEEDS REVIEW']
        status='FAIL' if failed_fk else 'NEEDS REVIEW' if review else 'PASS'
        summary.append({'dataset':name,'rows_before':len(r),'rows_after':len(t),'columns_before':len(r.columns),'columns_after':len(t.columns),
                        'missing_before':int(r.isna().sum().sum()),'missing_after':int(t.isna().sum().sum()),
                        'duplicate_rows_before':int(r.duplicated().sum()),'duplicate_rows_after':int(t.duplicated().sum()),
                        'duplicate_pk_before':int(r[key].duplicated().sum()),'duplicate_pk_after':int(t[key].duplicated().sum()),
                        'missing_pk_before':int(r[key].isna().sum()),'missing_pk_after':int(t[key].isna().sum()),
                        'value_corrections':sum(x['value_corrections'] for x in audit if x['dataset']==name),
                        'critical_validation':'FAIL' if failed_fk else 'PASS','status':status,'review_findings':len(review)})
    report={'version':VERSION,'environment':{'python':platform.python_version(),'pandas':pd.__version__},
            'schema_sha256':sha256(HERE/'cleaning_schema.json'),'pipeline_sha256':sha256(__file__),
            'summary':summary,'column_validation':audit,'relationships':fk,'business_checks':business,'outliers':outliers,
            'scope_limitations':['Current reference rows only; no historical temporal reconstruction.',
             '2016 is incomplete; expected dates may extend beyond last observed transaction.',
             'Supplier timing patterns are synthetic, not demonstrated supplier performance.',
             'Purchasing outers differ from sales package quantities; no implicit unit conversion.',
             'External lookup FKs not validated in CSV-only reruns; see read-only SQL source evidence.',
             'NEEDS REVIEW retains source-supported values and passes technical integrity; not final business approval.']}
    # All-source hashes and raw frames are rechecked before any outputs are published.
    for name,spec in schema.items():
        require(sha256(RAW/(name+'.csv'))==spec['sha256'],'Raw file changed during run')
        require(raw[name].equals(read_csv(RAW/(name+'.csv'))),'Raw DataFrame changed')
    if export:
        destination=Path(output_root) if output_root else CLEANED/VERSION
        require(destination.resolve()!=RAW.resolve() and RAW.resolve() not in destination.resolve().parents,
                'Output destination must never be the raw source directory')
        if any(row['critical_validation']=='FAIL' for row in summary):
            latest.write_text(json.dumps({'status':'FAIL','reason':'Foreign-key validation failed; no outputs from this run'},indent=2),encoding='utf-8')
            return {'raw':raw,'clean':clean,'serialized':texts,'report':report,'summary':pd.DataFrame(summary)}
        # Immutable run directory: if a pipeline/input changes, use a new version.
        destination.mkdir(parents=True,exist_ok=True)
        manifest=[]
        for row in summary:
            name=row['dataset'];spec=schema[name]
            if row['critical_validation']!='PASS':
                continue
            data=csv_bytes(texts[name]);path=destination/(name+'.csv')
            # Validate serialized bytes before writing and compare every field afterwards.
            reread=pd.read_csv(io.BytesIO(data),encoding='utf-8-sig',dtype='string',keep_default_na=False,na_values=[r'\N'])
            require(reread.equals(texts[name]),f'{name}: CSV roundtrip failed')
            if path.exists():
                require(path.read_bytes()==data,f'Refusing to overwrite different existing output: {path}')
            else:
                path.write_bytes(data)
            require(read_csv(path).equals(texts[name]),f'{name}: disk reread failed')
            manifest.append({'dataset':name,'source':project_path(RAW/(name+'.csv')),
                             'output':project_path(path),'source_sha256':spec['sha256'],'output_sha256':sha256(path),
                             'rows':len(texts[name]),'columns':len(texts[name].columns),'primary_key':spec['primary_key'],
                             'version':VERSION,'pipeline_sha256':report['pipeline_sha256'],'schema_sha256':report['schema_sha256'],
                             'critical_validation':row['critical_validation'],'status':row['status'],
                             'value_corrections':row['value_corrections']})
        report['manifest']=manifest
        # Automated reports only; the curated, business-reviewed reports stay untouched.
        folder=RERUN_REPORTS;folder.mkdir(parents=True,exist_ok=True)
        (folder/'quality_results.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
        (folder/'source_to_output_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        pd.DataFrame(audit).to_csv(folder/'column_validation.csv',index=False,encoding='utf-8-sig')
        pd.DataFrame(fk).to_csv(folder/'relationship_validation.csv',index=False,encoding='utf-8-sig')
        (folder/'Before_After_Quality_Report.md').write_text('# Before / After Data Quality Report\n\nVersion '+VERSION+'; raw-source preservation and every-field roundtrips passed. Status is scoped to the tests below, not a declaration of error-free business data.\n\n'+markdown_table(summary,['dataset','rows_before','rows_after','missing_before','missing_after','duplicate_pk_after','value_corrections','critical_validation','status'])+'\n\n## Business checks\n\n'+markdown_table(business,['dataset','check','affected_rows','status','reason'])+'\n\n## IQR investigation (all values retained)\n\n'+markdown_table(outliers,['dataset','column','scope','eligible_rows','flagged_rows','decision'])+'\n\n## Limitations\n\n'+'\n'.join('- '+x for x in report['scope_limitations']),encoding='utf-8')
        (folder/'Cleaning_Decision_Log.md').write_text('# Cleaning Decision Log\n\n- C001: strip PackageTypeName only; exactly ID 13 changes from `"Tub "` to `"Tub"`.\n- C002: parse all exported dates/timestamps, reject invalid values; no timezone inferred.\n- C003: measures stored as nullable Int64; ID columns stay strings.\n- C004: SQL decimals become Python Decimal, validated against SQL precision/scale; no binary floating-point money.\n- C005: SQL bits become nullable boolean with strict 0/1 validation.\n- P001: preserve all other values, raw NULLs, primary and foreign keys.\n\nAll C002-C005 conversions have zero business-value corrections and exact serialization roundtrips. Each column has a policy and result in column_validation.csv. Individual rows with a business concern stay unchanged.\n\n## Preserved findings\n\n'+markdown_table([x for x in business if x['affected_rows']],['dataset','check','affected_rows','decision','reason'])+'\n\nAll pooled and product/package IQR flags are preserved; see quality report for counts. No deduplication, row deletion, NULL filling, outlier capping, or inventory balancing was performed.',encoding='utf-8')
        unresolved=[x for x in business if x['status']=='NEEDS REVIEW']
        (folder/'Unresolved_Issues.md').write_text('# Unresolved Business Decisions\n\nThese are retained source values, not proven data corruption. NEEDS REVIEW outputs have passed technical validation but require team discussion before unified approval.\n\n'+markdown_table(unresolved,['dataset','check','affected_rows','reason','example_ids'])+'\n\n'+'\n'.join('- '+x for x in report['scope_limitations'])+'\n- Outlier removal has no evidence-based authorization; grouped flags alone are insufficient.\n- Missing BuyingGroupID means not recorded/not applicable; do not claim known group membership.\n- Sales_Orders raw byte hash differs from its old dictionary due only to quoting/newlines; selected source values were reconciled.\n',encoding='utf-8')
        latest.write_text(json.dumps({'status':'COMPLETED','version':VERSION,'exported_datasets':len(manifest),
                                     'critical_validation':'PASS','business_review_required':any(x['status']=='NEEDS REVIEW' for x in summary)},indent=2),encoding='utf-8')
    return {'raw':raw,'clean':clean,'serialized':texts,'report':report,'summary':pd.DataFrame(summary)}


if __name__=='__main__':
    result=run_pipeline()
    print(result['summary'].to_string(index=False))
    if 'failures' in result['report'] or (result['summary'].get('critical_validation',pd.Series(['FAIL']))=='FAIL').any():
        raise SystemExit('Critical validation failed; consult result. Failed datasets are not exported.')
