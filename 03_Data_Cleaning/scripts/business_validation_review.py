"""Focused read-only business review. Does not run cleaning or alter CSV outputs.

The reviewed, hash-bound v1.0.0 record lives in ../reports/. A rerun writes its
regenerated review, evidence and loading schema to reports/automated_rerun/ so the
reviewed record (referenced by final_business_disposition.json) is never replaced.
"""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import sys
import pandas as pd
import pyodbc
from cleaning_pipeline import convert_column, serialize_column

BASE=Path(__file__).resolve().parent      # 03_Data_Cleaning/scripts
WORKSPACE=BASE.parent
ROOT=WORKSPACE.parent                       # project root
REPORTS=WORKSPACE/'reports'/'automated_rerun'
QUERIES={
 'picker_orders': """SELECT o.OrderID,o.BackorderOrderID,o.OrderDate,o.PickingCompletedWhen,
 o.PickedByPersonID,i.InvoiceID,i.InvoiceDate
 FROM Sales.Orders o LEFT JOIN Sales.Invoices i ON i.OrderID=o.OrderID
 WHERE o.PickingCompletedWhen IS NOT NULL AND o.PickedByPersonID IS NULL ORDER BY o.OrderID""",
 'picker_line_exceptions': """SELECT COUNT_BIG(*) exceptions FROM Sales.OrderLines l JOIN Sales.Orders o ON o.OrderID=l.OrderID
 WHERE o.PickingCompletedWhen IS NOT NULL AND o.PickedByPersonID IS NULL
 AND (l.PickingCompletedWhen IS NULL OR l.PickedQuantity<>l.Quantity)""",
 'all_backorders': 'SELECT OrderID,BackorderOrderID FROM Sales.Orders WHERE BackorderOrderID IS NOT NULL',
 'negative_lines': """SELECT il.InvoiceLineID,il.InvoiceID,il.StockItemID,il.Quantity,il.UnitPrice,il.LineProfit,
 h.LastCostPrice,si.StockItemName,i.IsCreditNote,i.InvoiceDate
 FROM Sales.InvoiceLines il JOIN Warehouse.StockItemHoldings h ON h.StockItemID=il.StockItemID
 JOIN Warehouse.StockItems si ON si.StockItemID=il.StockItemID
 JOIN Sales.Invoices i ON i.InvoiceID=il.InvoiceID WHERE il.LineProfit<0 ORDER BY il.InvoiceLineID""",
 'long_invoices': """SELECT i.InvoiceID,o.OrderID,p.OrderID ParentOrderID,o.CustomerID,p.CustomerID ParentCustomerID,
 o.OrderDate,p.OrderDate ParentOrderDate,i.InvoiceDate,o.PickingCompletedWhen,
 DATEDIFF(day,o.OrderDate,i.InvoiceDate) Days
 FROM Sales.Invoices i JOIN Sales.Orders o ON o.OrderID=i.OrderID
 LEFT JOIN Sales.Orders p ON p.BackorderOrderID=o.OrderID
 WHERE DATEDIFF(day,o.OrderDate,i.InvoiceDate)>365 ORDER BY Days DESC,i.InvoiceID""",
 'holdings': """WITH movements AS (SELECT StockItemID,SUM(Quantity) MovementTotal,
 MIN(TransactionOccurredWhen) FirstMovement,MAX(TransactionOccurredWhen) LastMovement
 FROM Warehouse.StockItemTransactions GROUP BY StockItemID)
 SELECT h.StockItemID,h.QuantityOnHand,m.MovementTotal,h.QuantityOnHand-m.MovementTotal ImpliedOpening,
 h.LastEditedWhen,m.FirstMovement,m.LastMovement
 FROM Warehouse.StockItemHoldings h JOIN movements m ON m.StockItemID=h.StockItemID ORDER BY h.StockItemID""",
 'issue_reconciliation': """WITH a AS (SELECT InvoiceID,StockItemID,SUM(Quantity) q FROM Sales.InvoiceLines GROUP BY InvoiceID,StockItemID),
 b AS (SELECT InvoiceID,StockItemID,-SUM(Quantity) q FROM Warehouse.StockItemTransactions WHERE TransactionTypeID=10 GROUP BY InvoiceID,StockItemID)
 SELECT COUNT_BIG(*) compared_groups,SUM(CASE WHEN a.q=b.q THEN 0 ELSE 1 END) disagreements
 FROM a FULL JOIN b ON a.InvoiceID=b.InvoiceID AND a.StockItemID=b.StockItemID""",
 'receipt_reconciliation': """WITH a AS (SELECT p.PurchaseOrderID,p.StockItemID,SUM(CONVERT(bigint,p.ReceivedOuters)*s.QuantityPerOuter) q
 FROM Purchasing.PurchaseOrderLines p JOIN Warehouse.StockItems s ON s.StockItemID=p.StockItemID
 WHERE p.ReceivedOuters>0 GROUP BY p.PurchaseOrderID,p.StockItemID),
 b AS (SELECT PurchaseOrderID,StockItemID,SUM(Quantity) q FROM Warehouse.StockItemTransactions WHERE TransactionTypeID=11 GROUP BY PurchaseOrderID,StockItemID)
 SELECT COUNT_BIG(*) compared_groups,SUM(CASE WHEN a.q=b.q THEN 0 ELSE 1 END) disagreements
 FROM a FULL JOIN b ON a.PurchaseOrderID=b.PurchaseOrderID AND a.StockItemID=b.StockItemID""",
 'movement_types': """SELECT t.TransactionTypeID,t.TransactionTypeName,COUNT_BIG(*) records,SUM(s.Quantity) total_quantity,
 SUM(CASE WHEN s.Quantity=0 THEN 1 ELSE 0 END) zeros
 FROM Warehouse.StockItemTransactions s JOIN Application.TransactionTypes t ON t.TransactionTypeID=s.TransactionTypeID
 GROUP BY t.TransactionTypeID,t.TransactionTypeName ORDER BY t.TransactionTypeID""",
 'module': "SELECT definition FROM sys.sql_modules WHERE object_id=OBJECT_ID('DataLoadSimulation.Configuration_ApplyDataLoadSimulationProcedures')",
 'runtime_procedures': "SELECT SCHEMA_NAME(schema_id) schema_name,name FROM sys.procedures WHERE SCHEMA_NAME(schema_id)='DataLoadSimulation' ORDER BY name"
}


def table(rows,columns):
    return '\n'.join(['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|']+
                     ['| '+' | '.join(str(row[c]).replace('|','/') for c in columns)+' |' for row in rows])


def main():
    protected={p:hashlib.sha256(p.read_bytes()).hexdigest() for folder in [ROOT/'00_Source_Data',ROOT/'02_Data_Understanding',WORKSPACE/'cleaned_data']
               for p in folder.rglob('*') if p.is_file()}
    driver=next((d for d in ['ODBC Driver 18 for SQL Server','ODBC Driver 17 for SQL Server'] if d in pyodbc.drivers()),None)
    if not driver:
        raise RuntimeError('No supported ODBC driver')
    connection=pyodbc.connect('DRIVER={'+driver+r'};SERVER=OMAR\SQLEXPRESS;DATABASE=WideWorldImporters;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;ApplicationIntent=ReadOnly',autocommit=True,timeout=20)
    connection.timeout=120
    cursor=connection.cursor()
    server,database=cursor.execute('SELECT @@SERVERNAME,DB_NAME()').fetchone()
    if database!='WideWorldImporters':raise ValueError('Wrong database')
    evidence={'server':server,'database':database,'queries':QUERIES,'sql':{}}
    try:
        for name,sql in QUERIES.items():
            cursor.execute(sql)
            names=[c[0] for c in cursor.description]
            evidence['sql'][name]=[dict(zip(names,tuple(row))) for row in cursor.fetchall()]
    finally:
        connection.close()
    module=evidence['sql'].pop('module')[0]['definition'].replace('\r','')
    evidence['module_sha256']=hashlib.sha256(module.encode()).hexdigest()
    snippets={}
    for name,marker,length in [('backorder_split','-- create the backorder order',1900),
                               ('profit_formula','Quantity, UnitPrice, TaxRate, TaxAmount, LineProfit, ExtendedPrice',1100),
                               ('receipt_update','SET sih.QuantityOnHand +=',1650)]:
        pos=module.index(marker)
        declaration=module.rfind('CREATE PROCEDURE',0,pos)
        snippets[name]={'generated_procedure':module[declaration:module.index('\n',declaration)],'definition_excerpt':module[pos:pos+length]}
    evidence['module_excerpts']=snippets
    orders=evidence['sql']['picker_orders'];negative=evidence['sql']['negative_lines'];long=evidence['sql']['long_invoices'];hold=evidence['sql']['holdings']
    assert len({r['OrderID'] for r in orders})==len(orders)==7538
    assert len({r['InvoiceID'] for r in long})==len(long)==167
    assert len(negative)==4626 and len(hold)==227
    cost_matches=sum(r['LineProfit']==r['Quantity']*(r['UnitPrice']-r['LastCostPrice']) for r in negative)
    products=[]
    for item in sorted({r['StockItemID'] for r in negative}):
        subset=[r for r in negative if r['StockItemID']==item]
        products.append({'StockItemID':item,'Product':subset[0]['StockItemName'],'Lines':len(subset),
                         'Min price':min(r['UnitPrice'] for r in subset),'Max price':max(r['UnitPrice'] for r in subset),
                         'Current cost':subset[0]['LastCostPrice']})
    evidence['summary']={'picker_orders':len(orders),'picker_with_backorder':sum(r['BackorderOrderID'] is not None for r in orders),
       'picker_invoiced':sum(r['InvoiceID'] is not None for r in orders),'negative_lines':len(negative),
       'negative_products':len(products),'profit_formula_matches':cost_matches,'negative_credit_lines':sum(r['IsCreditNote'] for r in negative),
       'negative_profit_total':sum(r['LineProfit'] for r in negative),'long_invoices':len(long),
       'delay_min':min(r['Days'] for r in long),'delay_max':max(r['Days'] for r in long),
       'long_backorders':sum(r['ParentOrderID'] is not None for r in long),
       'long_inherited_date':sum(r['ParentOrderDate']==r['OrderDate'] for r in long),
       'long_same_customer':sum(r['ParentCustomerID']==r['CustomerID'] for r in long),
       'long_invoice_on_pick_day':sum(r['PickingCompletedWhen'].date()==r['InvoiceDate'] for r in long),
       'holdings_mismatches':sum(r['QuantityOnHand']!=r['MovementTotal'] for r in hold),
       'negative_implied_opening':sum(r['ImpliedOpening']<0 for r in hold),
       'min_implied_opening':min(r['ImpliedOpening'] for r in hold),'max_implied_opening':max(r['ImpliedOpening'] for r in hold)}
    schema=json.loads((BASE/'cleaning_schema.json').read_text())['datasets']
    loading=[];defaults=[];hashes={}
    # Reload only: convert_column does not run cleaning, export, or SQL access.
    for name,spec in schema.items():
        path=WORKSPACE/'cleaned_data/1.0.0'/f'{name}.csv'
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        raw=pd.read_csv(path,encoding='utf-8-sig',dtype='string',keep_default_na=False,na_values=[r'\N'])
        default=pd.read_csv(path,encoding='utf-8-sig')
        defaults.append({'dataset':name,'rows':len(raw),'correct_NULL_cells':int(raw.isna().sum().sum()),
                         'literal_NULL_markers_with_default_loading':int(default.astype('string').eq(r'\N').sum().sum()),
                         'default_primary_key_dtype':str(default[spec['primary_key']].dtype)})
        for col in spec['columns']:
            field=col['name'];typed=convert_column(raw[field],col)
            if not serialize_column(typed,col).equals(raw[field]):raise ValueError(f'{name}.{field}: reload roundtrip failed')
            loading.append({'dataset':name,'column':field,'SQL_type':col['sql_type'],'precision':col['precision'],
                            'scale':col['scale'],'nullable':col['nullable'],'default_dtype':str(default[field].dtype),
                            'required_dtype':str(typed.dtype),'object_semantics':'Decimal' if col['sql_type'] in ('decimal','numeric') else '',
                            'reload_validation':'PASS'})
        # Match the specific case IDs with cleaned CSVs; do not change them.
        if name=='Sales_Orders':
            ids=set(raw.loc[raw.PickingCompletedWhen.notna()&raw.PickedByPersonID.isna(),'OrderID'])
            assert ids=={str(r['OrderID']) for r in orders}
        if name=='Sales_InvoiceLines':
            ids=set(raw.loc[raw.LineProfit.map(Decimal).lt(0),'InvoiceLineID'])
            assert ids=={str(r['InvoiceLineID']) for r in negative}
        print('Reload checked',name,flush=True)
    evidence['reload_default_behavior']=defaults
    evidence['loading_columns_checked']=len(loading)
    evidence['cleaned_file_hashes']=hashes
    # Independently confirm the two multi-table cases against the cleaned files.
    def load_case(name):
        return pd.read_csv(WORKSPACE/'cleaned_data/1.0.0'/f'{name}.csv',encoding='utf-8-sig',dtype='string',keep_default_na=False,na_values=[r'\N'])
    order_dates=load_case('Sales_Orders').set_index('OrderID').OrderDate
    invoices=load_case('Sales_Invoices').set_index('InvoiceID')
    delays=(pd.to_datetime(invoices.InvoiceDate)-pd.to_datetime(invoices.OrderID.map(order_dates))).dt.days
    assert set(invoices.index[delays>365])=={str(row['InvoiceID']) for row in long}
    holdings=load_case('Warehouse_StockItemHoldings').set_index('StockItemID')
    movements=load_case('Warehouse_StockItemTransactions')
    movements['Quantity']=movements.Quantity.map(Decimal)
    totals=movements.groupby('StockItemID').Quantity.sum()
    for row in hold:
        item=str(row['StockItemID'])
        assert Decimal(holdings.loc[item,'QuantityOnHand'])==Decimal(str(row['QuantityOnHand']))
        assert totals.loc[item]==row['MovementTotal']
    evidence['cleaned_case_checks']={'picker_order_ids':'PASS','negative_profit_line_ids':'PASS',
                                    'long_invoice_ids':'PASS','all_227_holdings_and_movement_totals':'PASS'}
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in protected.items())
    evidence['protected_files_unchanged']=len(protected)
    REPORTS.mkdir(parents=True,exist_ok=True)
    (REPORTS/'business_validation_evidence.json').write_text(json.dumps(evidence,indent=2,default=str),encoding='utf-8')
    pd.DataFrame(loading).to_csv(REPORTS/'Cleaned_CSV_Loading_Schema.csv',index=False,encoding='utf-8-sig')
    s=evidence['summary'];receipt=evidence['sql']['receipt_reconciliation'][0];issue=evidence['sql']['issue_reconciliation'][0]
    report=f'''# Business Validation Review - Wide World Importers

Scope: four flagged cases, current OLTP read-only SELECTs, stored procedure definitions read as text, and reload validation of the 16 cleaned CSVs. No cleaning rerun or CSV/database change. Source: `{server}` / `{database}`. This review supplements, rather than rewrites, the original NEEDS REVIEW statuses.

| Case | Recommendation | Conclusion |
|---|---|---|
| 7,538 picked orders without picker ID | KEEP | Explained by sample backorder-splitting logic; individual picker attribution remains unknown. |
| 4,626 negative-profit invoice lines | KEEP | Valid signed stored profit, consistent arithmetic; discount/loss rationale is not established. |
| 167 invoices over 365 days after order | FLAG | Dates align with inherited backorder dates and same-day picking/invoicing. Retain; do not call this invoice processing delay. |
| 227 holdings/movement differences | REQUIRES BUSINESS CONFIRMATION | Neither missing opening balances nor source simulation behavior can be repaired safely from these records. |

## 1. Picked orders without a picker

All **{s['picker_with_backorder']:,}** affected orders have a BackorderOrderID and all **{s['picker_invoiced']:,}** are invoiced. There are **{evidence['sql']['picker_line_exceptions'][0]['exceptions']}** remaining lines with missing picking time or picked quantity different from ordered quantity on these orders.

The stored `DataLoadSimulation.Configuration_ApplyDataLoadSimulationProcedures` definition contains the generated `InvoicePickedOrders` procedure. Its backorder path moves unpicked lines to a new order and marks the original order's picking complete, but does **not** set PickedByPersonID. That is a concrete mechanism consistent with all affected records. The generated procedure is not currently installed as a standalone procedure; we inspected its template, not an execution trace. Reading the definition is not proof of every historical procedure execution.

**KEEP:** do not fill picker IDs with LastEditedBy, salesperson or packer IDs. Those roles are different. These records can support fulfillment/backorder analysis, but not complete employee picking-performance attribution. Retain an unknown-picker category when such attribution is required.

## 2. Negative-profit invoice lines

The **{s['negative_lines']:,}** lines span **{s['negative_products']} products**, and **{s['negative_credit_lines']}** are on credit notes. All **{s['profit_formula_matches']:,}** match `Quantity * (UnitPrice - current LastCostPrice)` exactly. The stored invoicing code computes LineProfit using this same formula at invoice creation. Current holdings cost is a corroborating comparison, **not** an independently dated historical cost series.

Four zombie-mask sizes account for 4,114 lines, sold at 18.00 against a current cost of 19.00. The remaining 512 lines concern 14 USB products. Exact negative profit totals **{s['negative_profit_total']}** in the dataset's recorded monetary units. No commercial currency or reason for discounting is inferred.

**KEEP:** retain signed profit in later margin calculations. Changing signs, taking absolute values, or deleting these rows would inflate profit. Whether these were intentional promotions, loss leaders or pricing mistakes requires commercial evidence; the available records do not justify correction. Product-level detail appears in the evidence appendix below.

## 3. Long order-to-invoice intervals

All **{s['long_backorders']}** invoices relate to orders referenced by a parent's BackorderOrderID. All **{s['long_inherited_date']}** child orders retain the parent's OrderDate, all **{s['long_same_customer']}** retain the same customer, and all **{s['long_invoice_on_pick_day']}** are invoiced on their picking-completion date. Observed intervals are **{s['delay_min']} to {s['delay_max']} days**.

The backorder creation code explicitly copies `o.OrderDate` and `o.ExpectedDeliveryDate`, rather than setting a new order date. This explains why order age can be much longer than the interval between final picking and invoicing. It does not prove actual real-world service delays; these are historical simulated records.

**FLAG:** preserve dates and include a documented backorder/inherited-date qualification in future cycle-time analysis. Distinguish original-demand age, backorder creation time (not reliably supplied by OrderDate), and invoice processing time. Do not replace OrderDate with InvoiceDate or use the 365-day heuristic as an SLA.

Examples:

{table(long[:5],['InvoiceID','OrderID','ParentOrderID','OrderDate','InvoiceDate','Days'])}

## 4. Current holdings versus movement totals

All **{s['holdings_mismatches']}** products differ. The implied opening balance `QuantityOnHand - SUM(movements)` is negative for **{s['negative_implied_opening']}** products, ranging from **{s['min_implied_opening']}** to **{s['max_implied_opening']}** across all items. This makes a blanket explanation of ordinary positive opening stock insufficient.

Transaction-side checks agree: **{issue['compared_groups']:,}** invoice/product groups have **{issue['disagreements']}** differences between invoiced quantity and stock issues; **{receipt['compared_groups']:,}** purchase-order/product groups have **{receipt['disagreements']}** differences between receipts and received outers multiplied by the current QuantityPerOuter. The latter agreement does not certify historical package conversions for other data versions.

A specific code-level concern exists in the stored generator definition for `ReceivePurchaseOrders`: its holdings update joins PurchaseOrderLines by StockItemID but lacks a restriction to `@PurchaseOrderID`. The following movement INSERT does restrict to that purchase order. Multiple historical purchase lines can also match one holdings row. This can make balance updates and logged movements diverge if this code path executes. This is a **potential simulation implementation defect**, not proof that it caused every observed difference. This generated procedure is also not currently installed standalone; no execution audit or trustworthy opening-balance history was established.

**REQUIRES BUSINESS CONFIRMATION:** keep both sources unchanged. Treat holdings as the provided snapshot, with a reliability caveat, and movements as recorded activity. Do not reconstruct daily availability, turnover, stockout rates or an inventory valuation presented as reconciled from this combination. To resolve it, obtain verified opening balances, complete movement/adjustment history and generator execution provenance. Do not invent balancing transactions.

## 5. Cleaned CSV reload and required schema

**CSV preserves values, not pandas data types.** Full reload tests covered all **16 files and {len(loading)} columns**. With the documented loader and explicit type conversion, every column round-tripped exactly; no NULL mask or value changed. Default pandas loading instead left **{sum(x['literal_NULL_markers_with_default_loading'] for x in defaults):,}** literal `\\N` cells as text and inferred numeric IDs. It does not automatically restore intended date, nullable Boolean or Decimal types.

| Field class | Required in-memory representation |
|---|---|
| Primary/foreign IDs, LastEditedBy, barcodes and other text | pandas string |
| Integer measures | nullable Int64 |
| SQL bit flags | nullable boolean, accept only 0/1 |
| SQL decimal/numeric | Python Decimal in object columns, with SQL precision/scale checks |
| SQL date/datetime2 | datetime64[ns], strict format validation; no invented timezone |

The exact per-column mapping is in **Cleaned_CSV_Loading_Schema.csv** and the existing **cleaning_schema.json**. Decimal columns display `object` in pandas; their values are Decimal, not ordinary strings or binary floats. SQL date columns use midnight timestamps in memory and `YYYY-MM-DD` when serialized.

Safe loading example (from the project root):

```python
from pathlib import Path
import pandas as pd

path = Path("03_Data_Cleaning/cleaned_data/1.0.0/Sales_Customers.csv")
customers = pd.read_csv(path, encoding="utf-8-sig", dtype="string",
                        keep_default_na=False, na_values=[r"\\N"])
customers["AccountOpenedDate"] = pd.to_datetime(
    customers["AccountOpenedDate"], format="%Y-%m-%d", errors="raise"
)
```

For all fields, this review's script uses the existing `convert_column` and `serialize_column` helpers with the saved schema and verifies exact round-trips. It **does not call run_pipeline or clean_table**. Do not use default numeric inference for money, or coercion that silently turns invalid dates into NULLs.

## Disposition

No CORRECT recommendation is justified. These findings support the individual submission with explicit limitations; they do not certify that the underlying sample is a fully reconciled real-world ledger. Retain the four original statuses as historical pipeline results and attach this review during team comparison. No data, original notebook, cleaning result, manifest or previous report was changed.

Queries, affected IDs, bounded procedure excerpts, all 227 balance comparisons and reload evidence are saved in **business_validation_evidence.json**. The reproducible runner is **business_validation_review.py**. All {len(protected)} protected source/profiling/cleaned files passed before/after SHA-256 checks. SQL reads were separate, not a transactionally atomic snapshot. No procedure was executed.

### Evidence appendix: negative-profit products

{table(products,['StockItemID','Product','Lines','Min price','Max price','Current cost'])}
'''
    (REPORTS/'Business_Validation_Review.md').write_text(report,encoding='utf-8')
    print(json.dumps(evidence['summary'],indent=2,default=str))
    print('Loading schema columns',len(loading),'Protected files unchanged',len(protected))


if __name__=='__main__':
    main()
