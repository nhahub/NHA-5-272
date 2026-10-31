# Business Validation Review - Wide World Importers

Scope: four flagged cases, current OLTP read-only SELECTs, stored procedure definitions read as text, and reload validation of the 16 cleaned CSVs. No cleaning rerun or CSV/database change. Source: `Omar\SQLEXPRESS` / `WideWorldImporters`. This review supplements, rather than rewrites, the original NEEDS REVIEW statuses.

| Case | Recommendation | Conclusion |
|---|---|---|
| 7,538 picked orders without picker ID | KEEP | Explained by sample backorder-splitting logic; individual picker attribution remains unknown. |
| 4,626 negative-profit invoice lines | KEEP | Valid signed stored profit, consistent arithmetic; discount/loss rationale is not established. |
| 167 invoices over 365 days after order | FLAG | Dates align with inherited backorder dates and same-day picking/invoicing. Retain; do not call this invoice processing delay. |
| 227 holdings/movement differences | REQUIRES BUSINESS CONFIRMATION | Neither missing opening balances nor source simulation behavior can be repaired safely from these records. |

## 1. Picked orders without a picker

All **7,538** affected orders have a BackorderOrderID and all **7,538** are invoiced. There are **0** remaining lines with missing picking time or picked quantity different from ordered quantity on these orders.

The stored `DataLoadSimulation.Configuration_ApplyDataLoadSimulationProcedures` definition contains the generated `InvoicePickedOrders` procedure. Its backorder path moves unpicked lines to a new order and marks the original order's picking complete, but does **not** set PickedByPersonID. That is a concrete mechanism consistent with all affected records. The generated procedure is not currently installed as a standalone procedure; we inspected its template, not an execution trace. Reading the definition is not proof of every historical procedure execution.

**KEEP:** do not fill picker IDs with LastEditedBy, salesperson or packer IDs. Those roles are different. These records can support fulfillment/backorder analysis, but not complete employee picking-performance attribution. Retain an unknown-picker category when such attribution is required.

## 2. Negative-profit invoice lines

The **4,626** lines span **18 products**, and **0** are on credit notes. All **4,626** match `Quantity * (UnitPrice - current LastCostPrice)` exactly. The stored invoicing code computes LineProfit using this same formula at invoice creation. Current holdings cost is a corroborating comparison, **not** an independently dated historical cost series.

Four zombie-mask sizes account for 4,114 lines, sold at 18.00 against a current cost of 19.00. The remaining 512 lines concern 14 USB products. Exact negative profit totals **-320493.55** in the dataset's recorded monetary units. No commercial currency or reason for discounting is inferred.

**KEEP:** retain signed profit in later margin calculations. Changing signs, taking absolute values, or deleting these rows would inflate profit. Whether these were intentional promotions, loss leaders or pricing mistakes requires commercial evidence; the available records do not justify correction. Product-level detail appears in the evidence appendix below.

## 3. Long order-to-invoice intervals

All **167** invoices relate to orders referenced by a parent's BackorderOrderID. All **167** child orders retain the parent's OrderDate, all **167** retain the same customer, and all **167** are invoiced on their picking-completion date. Observed intervals are **369 to 1116 days**.

The backorder creation code explicitly copies `o.OrderDate` and `o.ExpectedDeliveryDate`, rather than setting a new order date. This explains why order age can be much longer than the interval between final picking and invoicing. It does not prove actual real-world service delays; these are historical simulated records.

**FLAG:** preserve dates and include a documented backorder/inherited-date qualification in future cycle-time analysis. Distinguish original-demand age, backorder creation time (not reliably supplied by OrderDate), and invoice processing time. Do not replace OrderDate with InvoiceDate or use the 365-day heuristic as an SLA.

Examples:

| InvoiceID | OrderID | ParentOrderID | OrderDate | InvoiceDate | Days |
|---|---|---|---|---|---|
| 69046 | 5645 | 5627 | 2013-04-19 | 2016-05-09 | 1116 |
| 63532 | 2891 | 2818 | 2013-03-01 | 2016-02-08 | 1074 |
| 68104 | 7684 | 7657 | 2013-05-27 | 2016-04-25 | 1064 |
| 60616 | 2595 | 2573 | 2013-02-22 | 2015-12-21 | 1032 |
| 67675 | 10413 | 10344 | 2013-07-11 | 2016-04-18 | 1012 |

## 4. Current holdings versus movement totals

All **227** products differ. The implied opening balance `QuantityOnHand - SUM(movements)` is negative for **9** products, ranging from **-25010638.000** to **1183419.000** across all items. This makes a blanket explanation of ordinary positive opening stock insufficient.

Transaction-side checks agree: **228,265** invoice/product groups have **0** differences between invoiced quantity and stock issues; **8,358** purchase-order/product groups have **0** differences between receipts and received outers multiplied by the current QuantityPerOuter. The latter agreement does not certify historical package conversions for other data versions.

A specific code-level concern exists in the stored generator definition for `ReceivePurchaseOrders`: its holdings update joins PurchaseOrderLines by StockItemID but lacks a restriction to `@PurchaseOrderID`. The following movement INSERT does restrict to that purchase order. Multiple historical purchase lines can also match one holdings row. This can make balance updates and logged movements diverge if this code path executes. This is a **potential simulation implementation defect**, not proof that it caused every observed difference. This generated procedure is also not currently installed standalone; no execution audit or trustworthy opening-balance history was established.

**REQUIRES BUSINESS CONFIRMATION:** keep both sources unchanged. Treat holdings as the provided snapshot, with a reliability caveat, and movements as recorded activity. Do not reconstruct daily availability, turnover, stockout rates or an inventory valuation presented as reconciled from this combination. To resolve it, obtain verified opening balances, complete movement/adjustment history and generator execution provenance. Do not invent balancing transactions.

## 5. Cleaned CSV reload and required schema

**CSV preserves values, not pandas data types.** Full reload tests covered all **16 files and 139 columns**. With the documented loader and explicit type conversion, every column round-tripped exactly; no NULL mask or value changed. Default pandas loading instead left **557,283** literal `\N` cells as text and inferred numeric IDs. It does not automatically restore intended date, nullable Boolean or Decimal types.

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
                        keep_default_na=False, na_values=[r"\N"])
customers["AccountOpenedDate"] = pd.to_datetime(
    customers["AccountOpenedDate"], format="%Y-%m-%d", errors="raise"
)
```

For all fields, this review's script uses the existing `convert_column` and `serialize_column` helpers with the saved schema and verifies exact round-trips. It **does not call run_pipeline or clean_table**. Do not use default numeric inference for money, or coercion that silently turns invalid dates into NULLs.

## Disposition

No CORRECT recommendation is justified. These findings support the individual submission with explicit limitations; they do not certify that the underlying sample is a fully reconciled real-world ledger. Retain the four original statuses as historical pipeline results and attach this review during team comparison. No data, original notebook, cleaning result, manifest or previous report was changed.

Queries, affected IDs, bounded procedure excerpts, all 227 balance comparisons and reload evidence are saved in **business_validation_evidence.json**. The reproducible runner is **business_validation_review.py**. All 48 protected source/profiling/cleaned files passed before/after SHA-256 checks. SQL reads were separate, not a transactionally atomic snapshot. No procedure was executed.

### Evidence appendix: negative-profit products

| StockItemID | Product | Lines | Min price | Max price | Current cost |
|---|---|---|---|---|---|
| 1 | USB missile launcher (Green) | 40 | 2.50 | 3.75 | 9.50 |
| 2 | USB rocket launcher (Gray) | 35 | 2.50 | 3.75 | 9.50 |
| 4 | USB food flash drive - sushi roll | 46 | 3.20 | 4.80 | 12.00 |
| 5 | USB food flash drive - hamburger | 29 | 3.20 | 4.80 | 12.00 |
| 6 | USB food flash drive - hot dog | 39 | 3.20 | 4.80 | 12.00 |
| 7 | USB food flash drive - pizza slice | 31 | 3.20 | 4.80 | 12.00 |
| 8 | USB food flash drive - dim sum 10 drive variety pack | 38 | 24.00 | 36.00 | 88.50 |
| 9 | USB food flash drive - banana | 36 | 3.20 | 4.80 | 12.00 |
| 10 | USB food flash drive - chocolate bar | 41 | 3.20 | 4.80 | 12.00 |
| 11 | USB food flash drive - cookie | 28 | 3.20 | 4.80 | 12.00 |
| 12 | USB food flash drive - donut | 38 | 3.20 | 4.80 | 12.00 |
| 13 | USB food flash drive - shrimp cocktail | 41 | 3.20 | 4.80 | 12.00 |
| 14 | USB food flash drive - fortune cookie | 27 | 3.20 | 4.80 | 12.00 |
| 15 | USB food flash drive - dessert 10 drive variety pack | 43 | 24.00 | 36.00 | 88.50 |
| 142 | Halloween zombie mask (Light Brown) S | 1044 | 18.00 | 18.00 | 19.00 |
| 143 | Halloween zombie mask (Light Brown) M | 1017 | 18.00 | 18.00 | 19.00 |
| 144 | Halloween zombie mask (Light Brown) L | 982 | 18.00 | 18.00 | 19.00 |
| 145 | Halloween zombie mask (Light Brown) XL | 1071 | 18.00 | 18.00 | 19.00 |
