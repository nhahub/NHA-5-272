# Wide World Importers — Supply Chain Analytics & Business Intelligence

**DEPI — Digital Egypt Pioneers Initiative · Professional Data Analyst Track · Team 6**

An end-to-end analytics and business intelligence project on Microsoft's **Wide World Importers** sample: a wholesale distributor's sales, customer, inventory and purchasing operations. The project turns operational SQL Server data into validated, analysis-ready datasets and, in later phases, a custom dimensional model and Power BI reports.

> **Current milestone: INDIVIDUAL CLEANING SUBMISSIONS IN PROGRESS — TEAM CONSOLIDATION PENDING.** Data Understanding and Profiling have been completed individually. No unified team cleaning approach or cleaned dataset has been approved.

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

```text
README.md                                project overview and current submission status
00_Source_Data/CSV_Exports/               16 raw CSVs, Data Dictionary, Customer Addendum and export QA
01_Project_Planning_and_Documentation/
    1_Project_Planning_and_Management/    proposal, planning and team roles
    2_Literature_Review/                  literature and lecturer review
    3_Requirements_Gathering/             requirements documentation
```

## Current progress

| Phase | Status |
|---|---|
| 1. Project Planning & Management | Documented ([folder](01_Project_Planning_and_Documentation/1_Project_Planning_and_Management/)) |
| 2. Literature Review | Documented ([folder](01_Project_Planning_and_Documentation/2_Literature_Review/)). No written instructor evaluation has been received yet; none is claimed. |
| 3. Requirements Gathering | Documented ([folder](01_Project_Planning_and_Documentation/3_Requirements_Gathering/)) |
| Database restore and CSV export (16 tables) | Completed; export checked cell by cell against SQL Server |
| Data Understanding & Profiling | Completed individually; notebooks are being finalized and are not included in this submission. |
| Individual Data Cleaning | All six members independently work on the full agreed 16-dataset scope. One member has completed and validated an individual candidate; other individual submissions are being prepared. |
| Team comparison and consolidation | Pending. No unified cleaning approach or cleaned dataset has been approved. |
| EDA, Data Warehouse, ETL and Power BI | Not completed; future work after approval of the unified dataset. |
| Final testing, documentation and presentation | Pending. |

## Cleaning submission and approval

All six team members independently perform full Data Cleaning. Their results will be compared and consolidated into one approved cleaned dataset before the remaining project tasks are distributed.

The team will compare documented data scopes, cleaning decisions, reproducible code and before/after validation. Conflicting decisions and unresolved business questions must be reviewed before approval. Original raw datasets remain unchanged.

The individual cleaning candidate is retained in the member's original local project for team comparison. It is not the team's final implementation and is excluded from the current official submission. Official cleaned datasets, cleaning notebooks, code and reports will be published only after team review and approval.

## Access the current submission

Use the [Data Dictionary](00_Source_Data/CSV_Exports/Data_Dictionary.md) for raw CSV columns, keys, NULL handling and loading conventions. The [planning documentation](01_Project_Planning_and_Documentation/) contains the first three required documentation sections.

The original SQL Server OLTP backup is available from the [official Microsoft release](https://github.com/microsoft/sql-server-samples/releases/tag/wide-world-importers-v1.0). Select `WideWorldImporters-Full.bak`, not the separate warehouse backup.

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

- **Jupyter notebooks:** none are included in the current submission. Individual Data Understanding and Profiling notebooks are being finalized; team cleaning notebooks require review and approval before publication.
- **Individual cleaning code, candidate cleaned datasets and reports:** excluded until team comparison and approval of a unified implementation.
- **SQL Server backups** (`.bak`, 54–127 MB each): they are Microsoft's public files, available from the official release linked above.
- Personal study guides, archived earlier versions, local environments and temporary files.

The data is Microsoft's synthetic sample, so findings describe the sample and not a real company.
