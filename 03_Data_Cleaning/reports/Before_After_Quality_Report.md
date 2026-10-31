# Before / After Data Quality Report

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

Version 1.0.0; raw-source preservation and every-field roundtrips passed. Status is scoped to the tests below, not a declaration of error-free business data.

| dataset | rows_before | rows_after | missing_before | missing_after | duplicate_pk_after | value_corrections | critical_validation | status |
|---|---|---|---|---|---|---|---|---|
| Application_DeliveryMethods | 10 | 10 | 0 | 0 | 0 | 0 | PASS | PASS |
| Application_TransactionTypes | 13 | 13 | 0 | 0 | 0 | 0 | PASS | PASS |
| Purchasing_PurchaseOrderLines | 8367 | 8367 | 9 | 9 | 0 | 0 | PASS | PASS |
| Purchasing_PurchaseOrders | 2074 | 2074 | 0 | 0 | 0 | 0 | PASS | PASS |
| Purchasing_SupplierCategories | 9 | 9 | 0 | 0 | 0 | 0 | PASS | PASS |
| Purchasing_Suppliers | 13 | 13 | 4 | 4 | 0 | 0 | PASS | PASS |
| Sales_CustomerCategories | 8 | 8 | 0 | 0 | 0 | 0 | PASS | PASS |
| Sales_Customers | 663 | 663 | 261 | 261 | 0 | 0 | PASS | PASS |
| Sales_InvoiceLines | 228265 | 228265 | 0 | 0 | 0 | 0 | PASS | NEEDS REVIEW |
| Sales_Invoices | 70510 | 70510 | 84 | 84 | 0 | 0 | PASS | NEEDS REVIEW |
| Sales_OrderLines | 231412 | 231412 | 3147 | 3147 | 0 | 0 | PASS | PASS |
| Sales_Orders | 73595 | 73595 | 79765 | 79765 | 0 | 0 | PASS | NEEDS REVIEW |
| Warehouse_PackageTypes | 14 | 14 | 0 | 0 | 0 | 1 | PASS | PASS |
| Warehouse_StockItemHoldings | 227 | 227 | 0 | 0 | 0 | 0 | PASS | NEEDS REVIEW |
| Warehouse_StockItems | 227 | 227 | 591 | 591 | 0 | 0 | PASS | PASS |
| Warehouse_StockItemTransactions | 236667 | 236667 | 473422 | 473422 | 0 | 0 | PASS | PASS |

## Business checks

| dataset | check | affected_rows | status | reason |
|---|---|---|---|---|
| Application_DeliveryMethods | Remaining outer whitespace: DeliveryMethodName | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Application_DeliveryMethods | Empty text: DeliveryMethodName | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Application_TransactionTypes | Remaining outer whitespace: TransactionTypeName | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Application_TransactionTypes | Empty text: TransactionTypeName | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Purchasing_PurchaseOrderLines | Remaining outer whitespace: Description | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Purchasing_PurchaseOrderLines | Empty text: Description | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Purchasing_PurchaseOrderLines | Optional NULL: LastReceiptDate | 9 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Purchasing_PurchaseOrders | Constant column: ContactPersonID | 2074 | PASS | Constant in this sample; keep schema and values. |
| Purchasing_SupplierCategories | Remaining outer whitespace: SupplierCategoryName | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Purchasing_SupplierCategories | Empty text: SupplierCategoryName | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Purchasing_Suppliers | Remaining outer whitespace: SupplierName | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Purchasing_Suppliers | Empty text: SupplierName | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Purchasing_Suppliers | Optional NULL: DeliveryMethodID | 4 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Purchasing_Suppliers | Constant column: LastEditedBy | 13 | PASS | Constant in this sample; keep schema and values. |
| Sales_CustomerCategories | Remaining outer whitespace: CustomerCategoryName | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Sales_CustomerCategories | Empty text: CustomerCategoryName | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Sales_Customers | Optional NULL: BuyingGroupID | 261 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_InvoiceLines | Remaining outer whitespace: Description | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Sales_InvoiceLines | Empty text: Description | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Sales_Invoices | Constant column: DeliveryMethodID | 70510 | PASS | Constant in this sample; keep schema and values. |
| Sales_Invoices | Constant column: IsCreditNote | 70510 | PASS | Constant in this sample; keep schema and values. |
| Sales_Invoices | Optional NULL: ConfirmedDeliveryTime | 84 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_OrderLines | Remaining outer whitespace: Description | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Sales_OrderLines | Empty text: Description | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Sales_OrderLines | Optional NULL: PickingCompletedWhen | 3147 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_Orders | Optional NULL: PickedByPersonID | 10623 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_Orders | Optional NULL: BackorderOrderID | 66057 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_Orders | Constant column: IsUndersupplyBackordered | 73595 | PASS | Constant in this sample; keep schema and values. |
| Sales_Orders | Optional NULL: PickingCompletedWhen | 3085 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_PackageTypes | Remaining outer whitespace: PackageTypeName | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Warehouse_PackageTypes | Empty text: PackageTypeName | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Warehouse_PackageTypes | Constant column: LastEditedBy | 14 | PASS | Constant in this sample; keep schema and values. |
| Warehouse_StockItemHoldings | Remaining outer whitespace: BinLocation | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Warehouse_StockItemHoldings | Empty text: BinLocation | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Warehouse_StockItems | Remaining outer whitespace: StockItemName | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Warehouse_StockItems | Empty text: StockItemName | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Warehouse_StockItems | Optional NULL: ColorID | 99 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItems | Optional NULL: Brand | 209 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItems | Remaining outer whitespace: Brand | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Warehouse_StockItems | Empty text: Brand | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Warehouse_StockItems | Optional NULL: Size | 64 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItems | Remaining outer whitespace: Size | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Warehouse_StockItems | Empty text: Size | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Warehouse_StockItems | Optional NULL: Barcode | 219 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItems | Remaining outer whitespace: Barcode | 0 | PASS | No blanket text rewrite; review semantics before changing additional text. |
| Warehouse_StockItems | Empty text: Barcode | 0 | PASS | Empty text is distinct from NULL; retain pending context. |
| Warehouse_StockItems | Constant column: LastEditedBy | 227 | PASS | Constant in this sample; keep schema and values. |
| Warehouse_StockItemTransactions | Optional NULL: CustomerID | 8402 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItemTransactions | Optional NULL: InvoiceID | 8402 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItemTransactions | Optional NULL: SupplierID | 228309 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Warehouse_StockItemTransactions | Optional NULL: PurchaseOrderID | 228309 | PASS | Retained under SQL nullable schema; status/transaction context checked separately. No imputation. |
| Sales_Orders | Picked timestamp without picker | 7538 | NEEDS REVIEW | Backorder association is evidence, not proof of why picker ID is absent; retain and seek business interpretation. |
| Sales_Orders | No picking timestamp | 3085 | PASS | Do not fabricate completion; distinguish open/backorder state. |
| Sales_Invoices | No delivery timestamp | 84 | PASS | Incomplete delivery evidence near sample cutoff; retain, exclude only from metrics that require actual delivery. |
| Purchasing_PurchaseOrderLines | Zero receipts | 9 | PASS | Open/unfinished lines can have zero receipt and NULL last receipt date. |
| Purchasing_PurchaseOrderLines | Receipt status contradiction | 0 | PASS | Investigate status and receipt history; never invent a receipt. |
| Purchasing_PurchaseOrderLines | Received exceeds ordered | 0 | PASS | Could be over-receipt; preserve pending review. |
| Sales_OrderLines | Picked exceeds quantity | 0 | PASS | Inspect order-line semantics before changing. |
| Sales_InvoiceLines | Negative line profit | 4626 | NEEDS REVIEW | Stored loss is not corruption. Retain exact value; commercial reason unverified. |
| Warehouse_StockItemTransactions | Negative movement | 228286 | PASS | Stock Issue and Stocktake Adjustment quantities are signed; retained. |
| Warehouse_StockItemTransactions | Zero movement | 4 | PASS | Zero stocktake adjustment can mean no adjustment needed; preserve. |
| Warehouse_StockItemTransactions | Movement sign/type conflict | 0 | PASS | Expected current sample: issue negative, receipt positive, stocktake either sign/zero; new types require interpretation. |
| Sales_Orders | ExpectedDeliveryDate before OrderDate | 0 | PASS | Invalid-looking chronology; preserve and investigate. |
| Purchasing_PurchaseOrders | ExpectedDeliveryDate before OrderDate | 0 | PASS | Invalid-looking chronology; preserve and investigate. |
| Sales_Invoices | ConfirmedDeliveryTime before InvoiceDate | 0 | PASS | Invalid-looking chronology; preserve and investigate. |
| Sales_Invoices | Invoice before order | 0 | PASS | No header/line fan-out; mapped unique order date. |
| Sales_Invoices | Order-to-invoice delay over 365 days | 167 | NEEDS REVIEW | Review heuristic, not a business SLA. Keep historical dates; no assumed correction. |
| Purchasing_PurchaseOrderLines | Receipt before order | 0 | PASS | Last receipt date is not a full partial-receipt history. |
| Warehouse_StockItemHoldings | Target below reorder | 0 | PASS | Configuration relationship requires review; do not alter targets automatically. |
| Sales_OrderLines | Negative Quantity | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Sales_OrderLines | Negative PickedQuantity | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Sales_OrderLines | Negative UnitPrice | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Sales_InvoiceLines | Negative Quantity | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Sales_InvoiceLines | Negative UnitPrice | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Sales_InvoiceLines | Negative TaxAmount | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Sales_InvoiceLines | Negative ExtendedPrice | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Purchasing_PurchaseOrderLines | Negative OrderedOuters | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Purchasing_PurchaseOrderLines | Negative ReceivedOuters | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Purchasing_PurchaseOrderLines | Negative ExpectedUnitPricePerOuter | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItems | Negative QuantityPerOuter | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItems | Negative LeadTimeDays | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItems | Negative UnitPrice | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItems | Negative RecommendedRetailPrice | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItems | Negative TypicalWeightPerUnit | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItems | Negative TaxRate | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItemHoldings | Negative QuantityOnHand | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItemHoldings | Negative LastStocktakeQuantity | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItemHoldings | Negative LastCostPrice | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItemHoldings | Negative ReorderLevel | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Warehouse_StockItemHoldings | Negative TargetStockLevel | 0 | PASS | Review in field/package/credit context; no automatic replacement. |
| Sales_InvoiceLines | Tax arithmetic disagreement | 0 | PASS | Exact line tax check at two decimals; review any disagreement. |
| Sales_InvoiceLines | Extended price disagreement | 0 | PASS | ExtendedPrice compared with Quantity * UnitPrice + TaxAmount, exact decimals. |
| Warehouse_StockItemHoldings | Movement sum differs from snapshot | 227 | NEEDS REVIEW | Opening balances/complete history not established. Do not reconstruct inventory or force equality. |

## IQR investigation (all values retained)

| dataset | column | scope | eligible_rows | flagged_rows | decision |
|---|---|---|---|---|---|
| Sales_OrderLines | Quantity | pooled | 231412 | 14428 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |
| Sales_OrderLines | Quantity | product/package | 231412 | 0 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |
| Sales_InvoiceLines | Quantity | pooled | 228265 | 13907 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |
| Sales_InvoiceLines | Quantity | product/package | 228265 | 29 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |
| Purchasing_PurchaseOrderLines | OrderedOuters | pooled | 8367 | 0 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |
| Purchasing_PurchaseOrderLines | OrderedOuters | product/package | 8139 | 0 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |
| Purchasing_PurchaseOrderLines | ReceivedOuters | pooled | 8367 | 0 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |
| Purchasing_PurchaseOrderLines | ReceivedOuters | product/package | 8139 | 0 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |
| Purchasing_PurchaseOrderLines | ExpectedUnitPricePerOuter | pooled | 8367 | 2592 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |
| Purchasing_PurchaseOrderLines | ExpectedUnitPricePerOuter | product/package | 8139 | 0 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |
| Warehouse_StockItemHoldings | QuantityOnHand | pooled | 227 | 11 | PRESERVE: distribution flag only; mixed products and zero-IQR groups are not proof of error |

## Limitations

- Current reference rows only; no historical temporal reconstruction.
- 2016 is incomplete; expected dates may extend beyond last observed transaction.
- Supplier timing patterns are synthetic, not demonstrated supplier performance.
- Purchasing outers differ from sales package quantities; no implicit unit conversion.
- External lookup FKs not validated in CSV-only reruns; see read-only SQL source evidence.
- NEEDS REVIEW retains source-supported values and passes technical integrity; not final business approval.