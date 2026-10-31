# Wide World Importers — Data Cleaning v1.0.0 (individual submission)

One team member's full-dataset cleaning submission for the 16 agreed **WideWorldImporters OLTP** CSV exports, ready for comparison with the other five members. It is **not** the team's approved unified dataset. No EDA, warehouse loading or Power BI work is included.

**Start here:** the [Final Cleaning Handoff](reports/Final_Cleaning_Handoff.md). The cleaning notebook (`01_Full_Data_Cleaning.ipynb`, the same cleaning in short plain-pandas cells) is still being finalized by the team and **will be uploaded later**; this submission contains the scripts, the cleaned datasets and the validation reports. Where the reports mention the notebook, it refers to that upcoming file.

## Folder layout

```
03_Data_Cleaning/
├── README.md                     this file
├── requirements.txt              package versions of the verified run
├── scripts/
│   ├── cleaning_pipeline.py      the cleaning implementation (single source of truth)
│   ├── cleaning_schema.json      frozen scope: columns, SQL types, keys, row counts, raw SHA-256 locks
│   ├── load_cleaned_data.py      reusable typed loader for later stages
│   ├── test_cleaning_pipeline.py 16 regression tests
│   ├── verify_cleaned_outputs.py independent stdlib verifier (no pipeline imports)
│   ├── verify_sql_source.py      optional read-only SQL reconciliation
│   └── business_validation_review.py  optional read-only SQL business review runner
├── cleaned_data/1.0.0/           the 16 cleaned candidate CSVs
└── reports/                      curated decision log, quality reports, review, manifest, evidence
```

## How to run (from the repository root, PowerShell)

Create the environment once: `python -m venv .venv` then `.\.venv\Scripts\python.exe -m pip install -r 03_Data_Cleaning/requirements.txt`.

```powershell
.\.venv\Scripts\python.exe 03_Data_Cleaning/scripts/test_cleaning_pipeline.py
.\.venv\Scripts\python.exe 03_Data_Cleaning/scripts/verify_cleaned_outputs.py --check-only
# Optional, needs SQL Server access (SELECT-only, no writes):
.\.venv\Scripts\python.exe 03_Data_Cleaning/scripts/verify_sql_source.py
```

The notebook will be added later; the tests and the verifier above already check the published cleaned files.

**Re-exporting** (`python .../scripts/cleaning_pipeline.py`) is only needed for a deliberate new run. It refuses to overwrite an existing cleaned CSV with different bytes, updates `reports/latest_run.json`, and writes its automatically generated reports to a new `reports/automated_rerun/` folder — it never replaces the curated, business-reviewed reports. `business_validation_review.py` follows the same rule.

## Decisions

Only **C001** corrects a business value: PackageTypeID `13`, PackageTypeName `"Tub "` → `"Tub"`. **C002–C005** validate and convert dates (19 columns), integer measures (14), exact decimals (14) and bits (5) in memory. IDs, `LastEditedBy` and barcodes stay strings (P001, 86 columns). Every converted column must serialize back to exactly the source text; no silent coercion, rounding, NULL filling or row deletion occurs. Dates have no assumed timezone.

NULL decisions follow the Data Dictionary/Addendum and workflow evidence, not missingness alone. Negative stock movements, negative profit and IQR flags remain unchanged. Statistical IQR uses temporary floats only for flags; money uses `Decimal`.

Business review dispositions: picker IDs (7,538) **KEEP**, negative profit (4,626) **KEEP**, long-interval invoices (167) **FLAG**, holdings vs movements (227) **REQUIRES BUSINESS CONFIRMATION**. See [Business Validation Review](reports/Business_Validation_Review.md).

## Output and loading contract

CSV settings: UTF-8-SIG, comma separator, every field quoted, LF line endings, `\N` for SQL NULL. Empty strings and text such as `NA` remain distinct. **CSV does not retain pandas types** — use the loader:

```python
import sys
sys.path.insert(0, "03_Data_Cleaning/scripts")   # from the project root
from load_cleaned_data import load_table, load_all
orders = load_table("Sales_Orders")        # typed, SHA-256 checked against the manifest
```

Manual equivalent for reading text: `pd.read_csv(path, encoding="utf-8-sig", dtype="string", keep_default_na=False, na_values=[r"\N"])`, then apply the per-column types in [Cleaned_CSV_Loading_Schema.csv](reports/Cleaned_CSV_Loading_Schema.csv). Never use default float inference for financial columns.

Status meanings: **PASS** — technical tests pass and no designated business question; **NEEDS REVIEW** — technical tests pass, values preserved, a documented business question remains (initial pipeline status; final dispositions are in the manifest and `final_business_disposition.json`); **FAIL** — critical conversion, schema, fingerprint, key or relationship failure (no outputs published).

## Scope boundaries

Read the original Data Dictionary, Customer Export Addendum and CSV QA report in `00_Source_Data/CSV_Exports`. `Sales_Orders.csv`'s documented hash differs only through CSV quoting/newlines; a full SQL comparison matched all values. Do not replace that raw file to make the old hash match.

Current holdings are a snapshot; movement sums do not establish historical balances. Purchasing outers differ from sales units. Supplier timings are synthetic, 2016 is partial, and current attributes cannot reconstruct history. The independent verifier is a second implementation, not a second person's approval.
