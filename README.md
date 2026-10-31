# Wide World Importers — Supply Chain Analytics & Business Intelligence

**DEPI — Digital Egypt Pioneers Initiative · Professional Data Analyst Track · Team 6**

An end-to-end analytics and business intelligence project on Microsoft's **Wide World Importers** sample: a wholesale distributor's sales, customer, inventory and purchasing operations. The project turns operational SQL Server data into validated, analysis-ready datasets and, in later phases, a custom dimensional model and Power BI reports.

> **Status (31 Oct 2026):** planning documents, data export, data understanding and one member's full data cleaning are complete. EDA, the data warehouse, ETL and Power BI have **not started yet** — see [Current progress](#current-progress).

## Business problem

Sales, customer, inventory and purchasing data live in separate operational tables with their own grains, status codes and history. Answering simple management questions consistently — revenue and profit by customer or product, stock movement, supplier purchasing — needs clear metric definitions and data whose quality has been checked. Without that, reports built directly on the operational tables can double-count, mix grains or hide data-quality issues.

## Objectives

- Understand the source tables, relationships, business rules and data quality.
- Produce clean, validated, reproducible datasets without inventing or deleting data.
- Design a custom dimensional (star schema) model for selected KPIs.
- Build repeatable ETL with validation and logging.
- Deliver three Power BI report pages: Executive Overview, Sales & Customers, and Inventory & Purchasing, with KPIs reconciled against SQL.

Full details: [Project Proposal](01_Project_Planning_and_Documentation/1_Project_Planning_and_Management/01_Project_Proposal.docx).

## Dataset

- **Source:** SQL Server database **`WideWorldImporters`** (the full OLTP sample, not the `WideWorldImportersDW` warehouse sample, which is used only as a design reference). Microsoft sample data: synthetic and historical (2013 – May 2016).
- **Exported:** 16 tables, **852,074 rows, 139 columns**, as CSV files in [`00_Source_Data/CSV_Exports/`](00_Source_Data/CSV_Exports/):
  - **Sales:** Orders, OrderLines, Invoices, InvoiceLines, Customers, CustomerCategories
  - **Purchasing:** PurchaseOrders, PurchaseOrderLines, Suppliers, SupplierCategories
  - **Warehouse:** StockItems, StockItemHoldings, StockItemTransactions, PackageTypes
  - **Application:** TransactionTypes, DeliveryMethods
- **Format:** UTF-8 with BOM, every field quoted, `\N` = SQL NULL. Read them as described in the [Data Dictionary](00_Source_Data/CSV_Exports/Data_Dictionary.md); default `pd.read_csv` settings misread NULLs and money values.
- Personal-data tables (e.g. `Application.People`) were deliberately **not** exported.

## Tools

| Area | Tools |
|---|---|
| Source database | Microsoft SQL Server (Express), SSMS, T-SQL (read-only queries) |
| Data preparation | Python 3.14, pandas 3.0, pyodbc, Jupyter |
| Validation | Python `unittest`, an independent standard-library verifier, read-only SQL reconciliation |
| Planned modeling and reporting | Custom star schema in SQL Server, Power BI Desktop, Power Query, DAX |
| Collaboration | GitHub |

## Repository structure

```
├── 01_Project_Planning_and_Documentation/   DEPI documentation sections 1–3 (.docx)
│   ├── 1_Project_Planning_and_Management/   proposal, plan & timeline, roles, risks, success measures
│   ├── 2_Literature_Review/                 references, alternatives, evaluation and improvements
│   └── 3_Requirements_Gathering/            stakeholders, user stories, use cases, functional & non-functional requirements
├── 00_Source_Data/
│   └── CSV_Exports/                         the 16 raw CSV exports + Data Dictionary, Customer Addendum, export QA report
└── 03_Data_Cleaning/                        individual cleaning submission v1.0.0
    ├── scripts/                             cleaning pipeline, schema, typed loader, tests, verifiers
    ├── cleaned_data/1.0.0/                  the 16 cleaned CSV files
    └── reports/                             decision log, quality and business validation reports, manifest
```

## Current progress

| Phase | Status |
|---|---|
| 1. Project Planning & Management | Documented ([folder](01_Project_Planning_and_Documentation/1_Project_Planning_and_Management/)) |
| 2. Literature Review | Documented ([folder](01_Project_Planning_and_Documentation/2_Literature_Review/)). No written instructor evaluation has been received yet; none is claimed. |
| 3. Requirements Gathering | Documented ([folder](01_Project_Planning_and_Documentation/3_Requirements_Gathering/)) |
| Database restore and CSV export (16 tables) | Completed; export checked cell by cell against SQL Server |
| Data Understanding & Profiling | Completed. **The notebooks are still being finalized and will be uploaded later.** |
| Data Cleaning (one member's individual submission, v1.0.0) | Completed and verified. **The cleaning notebook will be uploaded later**; the scripts, cleaned data and reports are included now. |
| Team comparison and approval of one unified clean dataset | Not done yet |
| EDA, System Analysis & Design, Data Warehouse & ETL, Power BI, Testing, Final Presentation | Not started |

## Data cleaning — verified results (v1.0.0)

- **No rows or columns removed.** 852,074 rows and 10,486,934 cells in, the same out.
- **All 557,283 NULL values kept.** They carry meaning (for example "no backorder" or "picking not finished"), so filling them would invent data.
- **0 duplicate rows**, and 0 duplicate or missing primary keys.
- **30 foreign-key relationships checked with 0 orphans**, plus 28 references to tables outside the export, checked with read-only SQL.
- **One value corrected:** a trailing space in package type 13 (`"Tub "` → `"Tub"`).
- **Data types fixed** without changing any value: dates, integer quantities, exact `Decimal` money values and true/false flags (52 columns).
- **Four business findings kept and documented, not "fixed":**
  - 7,538 picked orders without a picker ID: KEEP.
  - 4,626 negative-profit invoice lines: KEEP.
  - 167 invoices more than 365 days after the order (backorders keep the original order date): FLAG.
  - 227 stock holdings that differ from movement totals: needs business confirmation.

  See the [Business Validation Review](03_Data_Cleaning/reports/Business_Validation_Review.md).

Start with the [Final Cleaning Handoff](03_Data_Cleaning/reports/Final_Cleaning_Handoff.md) and the [Cleaning Decision Log](03_Data_Cleaning/reports/Cleaning_Decision_Log.md).

## How to reproduce

Requirements: Windows, Python 3.14. SQL Server is needed only for the optional source checks.

```powershell
git clone https://github.com/nhahub/NHA-5-272.git
cd NHA-5-272
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r 03_Data_Cleaning/requirements.txt

# 16 regression tests of the cleaning rules
.\.venv\Scripts\python.exe 03_Data_Cleaning/scripts/test_cleaning_pipeline.py
# independent check: raw vs cleaned, cell by cell (expects status PASS and exactly one change)
.\.venv\Scripts\python.exe 03_Data_Cleaning/scripts/verify_cleaned_outputs.py --check-only
```

Load cleaned tables with their correct types:

```python
import sys
sys.path.insert(0, "03_Data_Cleaning/scripts")
from load_cleaned_data import load_table
orders = load_table("Sales_Orders")   # typed and SHA-256 checked
```

**Optional, needs the database.** Restore `WideWorldImporters-Full.bak` from the [official Microsoft release](https://github.com/microsoft/sql-server-samples/releases/tag/wide-world-importers-v1.0). Then run `03_Data_Cleaning/scripts/verify_sql_source.py`, which only reads (SELECT-only). It connects to `OMAR\SQLEXPRESS`, so change the server name in the script for your machine.

## Next phases

1. Compare the six members' cleaning submissions and approve one unified dataset.
2. Exploratory Data Analysis on the approved dataset.
3. System Analysis & Design: star schema, ERD, data-flow and ETL design (due 6 Nov 2026).
4. ETL into a custom data warehouse with SQL reconciliation tests.
5. Power BI: three report pages with validated KPIs.
6. Testing, final report and presentation (due 4 Dec 2026).

## Team

| Member | Role |
|---|---|
| Omar Mahmoud Sophy Rezk | Team Leader & Project Integration |
| Ahmed Saleh Abdelzaher | Data Engineering & ETL |
| Sara Mostafa Abdelhafiz | Data Analysis & Data Quality |
| Abdelrahman Mohammed Fathy | SQL & Data Warehouse |
| Samir Magdy Yacoub | Power BI & DAX |
| Ola Abdelkader Mahmoud Mohamed | Business Analysis & Documentation |

## Not included in this repository

- **Jupyter notebooks** (Data Understanding, Profiling and Data Cleaning): still being finalized; they will be uploaded later.
- **SQL Server backups** (`.bak`, 54–127 MB each): they are Microsoft's public files, available from the official release linked above.
- Personal study guides, archived earlier versions, local environments and temporary files.

The data is Microsoft's synthetic sample, so findings describe the sample and not a real company.
