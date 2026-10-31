# Cleaning Decision Log

## Final business disposition (verified follow-up)

This section incorporates [Business Validation Review](Business_Validation_Review.md). It supersedes the initial request to investigate the first three cases **for cleaning decisions**, not their source values. The original execution statuses in quality_results.json remain historical evidence: 12 PASS and 4 NEEDS REVIEW. All 16 passed technical validation. Final dispositions are separate fields in the manifest and final_business_disposition.json.

| Dataset / affected records | Classification | Final decision | Evidence and remaining constraint |
|---|---|---|---|
| Sales_Orders / 7538 | Resolved for cleaning; intentionally preserved | KEEP | All have backorder links and invoices; splitting template completes picking without assigning picker. Actual picker identity remains unknown; no employee-performance attribution. |
| Sales_InvoiceLines / 4626 | Resolved for cleaning; intentionally preserved | KEEP | 18 products; all match signed profit arithmetic using current recorded cost; no credit notes. Historical cost provenance and commercial discount/loss rationale are not established. |
| Sales_Invoices / 167 | Flagged analytical limitation | FLAG | All are linked backorders with inherited order dates, invoiced on picking day; intervals 369-1116 days. Agree cycle-time definition; do not interpret original-demand age as invoice-processing delay. |
| Warehouse_StockItemHoldings / 227 | Unresolved business confirmation | REQUIRES BUSINESS CONFIRMATION | All differ from movements; nine implied opening balances are negative. Potential receipt-template scope defect, historical execution unproven. Obtain reliable opening balances, complete movement/adjustment history and generator provenance; do not force reconciliation. |

**No additional correction is justified.** KEEP resolves whether to change the data; it does not establish the real picker identity or why a commercial loss occurred. FLAG means retain dates with an analytical qualification. The 227 inventory discrepancies remain **NEEDS REVIEW / REQUIRES BUSINESS CONFIRMATION**. Stored generator templates explain possible mechanisms, not proven historical executions.

All optional NULLs, signed stock movements, negative profits and IQR flags remain preserved. No invented dates, employee IDs, balancing entries, caps or replacements were added.

## Required loading contract

CSV stores text, not pandas data types. Use UTF-8-SIG, `dtype="string"`, `keep_default_na=False`, and `na_values=[r"\N"]`. Only the literal `\N` is SQL NULL; preserve empty strings and ordinary text such as `NA`. Default loading left 557,283 NULL markers as text in the verified reload test.

- IDs, foreign keys, LastEditedBy, barcodes and other text: pandas string.
- Integer measures: nullable Int64; validate rather than silently coerce.
- SQL bits: nullable boolean after strict 0/1 validation.
- Monetary and other SQL decimals: Python Decimal objects; preserve the SQL precision/scale. Do not use floating-point inference for financial calculations.
- Dates/timestamps: strict datetime64[ns] parsing; date-only values serialize as YYYY-MM-DD, timestamps as ISO 8601. No timezone is inferred.

All 139 columns passed exact typed reload/serialization checks. See [Cleaned_CSV_Loading_Schema.csv](Cleaned_CSV_Loading_Schema.csv) and [cleaning_schema.json](../scripts/cleaning_schema.json) for column-specific definitions. The `convert_column` and `serialize_column` helpers can load/validate types without running cleaning; do not call `run_pipeline` just to read the output.

## Initial cleaning-run evidence (retained)

- C001: strip PackageTypeName only; exactly ID 13 changes from `"Tub "` to `"Tub"`.
- C002: parse all exported dates/timestamps, reject invalid values; no timezone inferred.
- C003: measures stored as nullable Int64; ID columns stay strings.
- C004: SQL decimals become Python Decimal, validated against SQL precision/scale; no binary floating-point money.
- C005: SQL bits become nullable boolean with strict 0/1 validation.
- P001: preserve all other values, raw NULLs, primary and foreign keys.

All C002-C005 conversions have zero business-value corrections and exact serialization roundtrips. Each column has a policy and result in column_validation.csv. Individual rows with a business concern stay unchanged.

## Preserved findings

| dataset | check | affected_rows | decision | reason |
|---|---|---|---|---|
| Purchasing_PurchaseOrderLines | Optional NULL: LastReceiptDate | 9 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Purchasing_PurchaseOrders | Constant column: ContactPersonID | 2074 | PRESERVE | Constant in this sample; keep schema and values. |
| Purchasing_Suppliers | Optional NULL: DeliveryMethodID | 4 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Purchasing_Suppliers | Constant column: LastEditedBy | 13 | PRESERVE | Constant in this sample; keep schema and values. |
| Sales_Customers | Optional NULL: BuyingGroupID | 261 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_Invoices | Constant column: DeliveryMethodID | 70510 | PRESERVE | Constant in this sample; keep schema and values. |
| Sales_Invoices | Constant column: IsCreditNote | 70510 | PRESERVE | Constant in this sample; keep schema and values. |
| Sales_Invoices | Optional NULL: ConfirmedDeliveryTime | 84 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_OrderLines | Optional NULL: PickingCompletedWhen | 3147 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_Orders | Optional NULL: PickedByPersonID | 10623 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_Orders | Optional NULL: BackorderOrderID | 66057 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_Orders | Constant column: IsUndersupplyBackordered | 73595 | PRESERVE | Constant in this sample; keep schema and values. |
| Sales_Orders | Optional NULL: PickingCompletedWhen | 3085 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_PackageTypes | Constant column: LastEditedBy | 14 | PRESERVE | Constant in this sample; keep schema and values. |
| Warehouse_StockItems | Optional NULL: ColorID | 99 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItems | Optional NULL: Brand | 209 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItems | Optional NULL: Size | 64 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItems | Optional NULL: Barcode | 219 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItems | Constant column: LastEditedBy | 227 | PRESERVE | Constant in this sample; keep schema and values. |
| Warehouse_StockItemTransactions | Optional NULL: CustomerID | 8402 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItemTransactions | Optional NULL: InvoiceID | 8402 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItemTransactions | Optional NULL: SupplierID | 228309 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItemTransactions | Optional NULL: PurchaseOrderID | 228309 | PRESERVE | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_Orders | Picked timestamp without picker | 7538 | PRESERVE | Backorder association is evidence, not proof of why picker ID is absent; retain and seek business interpretation. |
| Sales_Orders | No picking timestamp | 3085 | PRESERVE | Do not fabricate completion; distinguish open/backorder state. |
| Sales_Invoices | No delivery timestamp | 84 | PRESERVE | Incomplete delivery evidence near sample cutoff; retain, exclude only from metrics that require actual delivery. |
| Purchasing_PurchaseOrderLines | Zero receipts | 9 | PRESERVE | Open/unfinished lines can have zero receipt and NULL last receipt date. |
| Sales_InvoiceLines | Negative line profit | 4626 | PRESERVE | Stored loss is not corruption. Retain exact value; commercial reason unverified. |
| Warehouse_StockItemTransactions | Negative movement | 228286 | PRESERVE | Stock Issue and Stocktake Adjustment quantities are signed; retained. |
| Warehouse_StockItemTransactions | Zero movement | 4 | PRESERVE | Zero stocktake adjustment can mean no adjustment needed; preserve. |
| Sales_Invoices | Order-to-invoice delay over 365 days | 167 | PRESERVE | Review heuristic, not a business SLA. Keep historical dates; no assumed correction. |
| Warehouse_StockItemHoldings | Movement sum differs from snapshot | 227 | PRESERVE | Opening balances/complete history not established. Do not reconstruct inventory or force equality. |

All pooled and product/package IQR flags are preserved; see quality report for counts. No deduplication, row deletion, NULL filling, outlier capping, or inventory balancing was performed.