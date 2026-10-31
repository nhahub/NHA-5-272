# Final Individual Data Cleaning Handoff

**Ready for comparison with the other five team members, with documented limitations.** This is not the approved unified team dataset. Scope: 16 agreed WideWorldImporters OLTP CSV datasets, cleaning version 1.0.0; no EDA, ETL or warehouse loading.

## Delivered result

- 16 candidate cleaned CSVs: `../cleaned_data/1.0.0/`.
- All 852,074 records retained across different table grains; no rows or columns removed.
- Exactly one business-value correction: PackageTypeID 13, `"Tub "` to `"Tub"` (C001).
- C002-C005 validate/convert dates, integer measures, exact decimals and bits without changing business values. IDs and barcodes stay strings.
- All 557,283 missing cells preserved; no automatic NULL filling, deduplication, outlier removal or profit/sign changes.
- Main notebook: [`01_Full_Data_Cleaning.ipynb`](../01_Full_Data_Cleaning.ipynb) (21 code cells, executed 2026-10-27, read-only). The original 18-code-cell notebook is preserved in `../archive/pre_reorganization_v1.0.0/`.

## Evidence

Initial checks: zero duplicate/missing primary keys, 30 CSV-scope foreign-key checks passed, 28 outside-scope SQL reference checks passed, exact financial arithmetic matched. Separate implementation compared 10,486,934 output cells to raw and found only C001. Fourteen regression tests passed. See the final documentation validation receipt for checks rerun during this handoff.

| Dataset | Rows | Technical validation | Final disposition |
|---|---:|---|---|
| Application_DeliveryMethods | 10 | PASS | KEEP: no additional business-review exception |
| Application_TransactionTypes | 13 | PASS | KEEP: no additional business-review exception |
| Purchasing_PurchaseOrderLines | 8367 | PASS | KEEP: no additional business-review exception |
| Purchasing_PurchaseOrders | 2074 | PASS | KEEP: no additional business-review exception |
| Purchasing_SupplierCategories | 9 | PASS | KEEP: no additional business-review exception |
| Purchasing_Suppliers | 13 | PASS | KEEP: no additional business-review exception |
| Sales_CustomerCategories | 8 | PASS | KEEP: no additional business-review exception |
| Sales_Customers | 663 | PASS | KEEP: no additional business-review exception |
| Sales_InvoiceLines | 228265 | PASS | KEEP |
| Sales_Invoices | 70510 | PASS | FLAG |
| Sales_OrderLines | 231412 | PASS | KEEP: no additional business-review exception |
| Sales_Orders | 73595 | PASS | KEEP |
| Warehouse_PackageTypes | 14 | PASS | KEEP: no additional business-review exception |
| Warehouse_StockItemHoldings | 227 | PASS | REQUIRES BUSINESS CONFIRMATION |
| Warehouse_StockItems | 227 | PASS | KEEP: no additional business-review exception |
| Warehouse_StockItemTransactions | 236667 | PASS | KEEP: no additional business-review exception |

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

## Files for team comparison

- [Notebook](../01_Full_Data_Cleaning.ipynb), [pipeline](../scripts/cleaning_pipeline.py), [run instructions](../README.md), [dependency versions](../requirements.txt).
- [Decision log](Cleaning_Decision_Log.md), [before/after report](Before_After_Quality_Report.md), [business review](Business_Validation_Review.md), [unresolved questions](Unresolved_Issues.md).
- [Source/output manifest](source_to_output_manifest.json): row counts, unchanged data hashes, original execution code/schema hashes and final dispositions.
- [Column loading schema](Cleaned_CSV_Loading_Schema.csv), [SQL schema](../scripts/cleaning_schema.json), [final review record](final_business_disposition.json), [typed loader](../scripts/load_cleaned_data.py).
- [Independent check](Independent_Quality_Review.md) and [machine-readable evidence](independent_review.json).

Compare source fingerprints, scope, correction rules, retained exceptions, counts and output values by primary key. Byte differences caused solely by CSV quoting or line endings are not business-value differences. Missing source lookups or incomplete periods must not be silently filled.

## Still unresolved

Inventory reconciliation for all 227 items requires business confirmation. Actual picker identities, historical cost provenance and loss rationale remain unknown. Future cycle-time definitions and the team's unified cleaning approval remain decisions to make. Nothing here authorizes inventing values or starting later analysis phases.

## Documentation finalization checks

All 14 existing regression tests passed again. The independent output checker re-compared all 10,486,934 cells and found only C001. Manifest/file/code/schema fingerprints and all local document links passed checks; 52 protected files remained unchanged. Notebook code and saved outputs were preserved, not re-executed. See [validation receipt](final_documentation_validation.json). No SQL access or full cleaning rerun occurred.

## Reorganization and re-verification (2026-10-27)

The cleaning workspace moved from `05_Data_Analysis/` to `05_Data_Analysis/01_Data_Cleaning/` (scripts in `scripts/`, reports in `reports/`). No cleaned value, cleaning rule or schema changed: all 16 output CSVs keep their manifest SHA-256 values, and `cleaning_schema.json` keeps its recorded hash. Code changes are limited to paths, portable relative manifest paths, a `--check-only` verifier mode, a new typed loader, and one defect fix: an export rerun previously regenerated and **overwrote** this curated record (including the manifest's final dispositions). Reruns now write to `automated_rerun/`. Details and hashes: [MIGRATION_RECORD](../archive/MIGRATION_RECORD.md).

Re-verified after the move: 16/16 regression tests (14 original + 2 new), the independent verifier (10,486,934 cells, only C001), a live read-only SQL reconciliation (16/16 tables, 0 differences, 28/28 outside-scope references), a full export rerun (byte-identical outputs and identical results in every report section), a business-review rerun (identical evidence), and a read-only Run All of the main notebook.

## Second relocation (2026-10-27)

The workspace was later promoted from `05_Data_Analysis/01_Data_Cleaning/` to the top-level phase folder `03_Data_Cleaning/`, and the later phases were renumbered (see [../../docs/MIGRATION_RECORD.md](../../docs/MIGRATION_RECORD.md)). Only locations changed: no cleaned value, rule or schema changed, and the 16 output CSVs keep their manifest SHA-256 values. The manifest's `output` paths were updated to the new project-relative location; the paths named in the section above are historical.
