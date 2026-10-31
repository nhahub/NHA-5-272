# Final Independent Quality Review

This review used a separate standard-library CSV/Decimal implementation (`verify_cleaned_outputs.py`), not the cleaning functions. It is an independent implementation check and self-review, not an external human approval.

## Verified results

- All 16 output files independently compared to raw by primary key: **10,486,934 cells** checked.
- Exactly one allowed difference: Warehouse.PackageTypes, PackageTypeID 13, PackageTypeName `"Tub "` to `"Tub"`.
- No rows or columns lost; raw NULL masks and key identities preserved.
- All 30 in-scope FK relationships pass with unique parent keys and no orphan references.
- Exact Decimal invoice tax and extended-price arithmetic: zero disagreements.
- Separate read-only SQL reconciliation: all 16 raw projections match current source values, with 28 outside-scope FK checks and zero orphans.
- Fourteen automated tests pass, including invalid-conversion, duplicate-key, orphan, precision, NULL/text, C001 idempotence and changed-source export blocking tests.
- Output bytes are deterministic: the initial pipeline export and subsequent full notebook run reproduced identical files; differing existing output bytes would have stopped the run.
- Notebook executed sequentially: 18 code cells, no saved traceback errors. Outputs and notebook structure were inspected programmatically; no browser/notebook-viewer visual test was performed.
- All pre-existing protected project files are unchanged; see source_integrity.json. Only the cleaning notebook was extended. No source CSV or SQL table was written.

## Business conclusions and limits

Technical validation passed for all 16 datasets. Overall statuses are 12 PASS and 4 NEEDS REVIEW. Preserved questions concern 7,538 picked orders without picker IDs, 4,626 negative-profit lines, 167 invoices more than 365 days after their order, and 227 holdings records whose movement sum is not the current snapshot. These are not proven corruption. All IQR flags, optional NULLs, negative stock movements and original date values were retained.

Only PackageTypeName C001 changes a source business value. C002-C005 change in-memory representations, not business values; CSV is text and requires explicit types on reload. Full-column roundtrips guard precision, dates and NULLs. IDs/barcodes remain text.

Separate SQL reads are not an atomic snapshot. Non-exported references need the SQL evidence for verification; an offline CSV-only run reports them as NOT VERIFIED rather than inventing parent records. Source agreement does not prove that every underlying business record is logically correct.

Candidate outputs are ready for comparison with the other five team members, subject to documented review items. They are not yet the team's approved unified dataset.


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


## Addendum — re-verification after reorganization (2026-10-27)

The statements above describe the original review (18-cell notebook, 14 tests). After the workspace moved to `05_Data_Analysis/01_Data_Cleaning/`, the checks were rerun: `verify_cleaned_outputs.py` passed (10,486,934 cells, only the C001 difference, 30 internal relationships, 0 tax / extended-price disagreements); 16 regression tests passed; `verify_sql_source.py` reproduced byte-identical SQL evidence; and the new [main notebook](../01_Full_Data_Cleaning.ipynb) executed with 21 code cells and no errors. A separate cell-by-cell pandas re-implementation in the notebook gave the same result. This remains self-review by one submission, not another person's approval.

## Addendum — second relocation (2026-10-27)

The workspace now lives at `03_Data_Cleaning/`. The path named in the previous addendum is historical. All checks were rerun from the new location; see [../../docs/MIGRATION_RECORD.md](../../docs/MIGRATION_RECORD.md).
