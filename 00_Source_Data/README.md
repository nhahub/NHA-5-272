# Source Data

`CSV_Exports/` holds the 16 raw CSV files exported (SELECT-only) from the SQL Server database `WideWorldImporters` on 2026-10-17, plus:

- [Data_Dictionary.md](CSV_Exports/Data_Dictionary.md): columns, SQL types, keys and how to read the files.
- [Customer_Export_Addendum.md](CSV_Exports/Customer_Export_Addendum.md): the two customer tables.
- `CSV_Export_QA_Report.html`: the export quality check, in Arabic. Download it to view.

The raw files are kept exactly as exported. The Data Dictionary's hash for `Sales_Orders.csv` is outdated because only the CSV formatting changed; its values match SQL Server exactly.

**Not included:** the SQL Server backups `WideWorldImporters-Full.bak` and `WideWorldImportersDW-Standard.bak`. They are Microsoft's public sample files, 54–127 MB each, and can be downloaded from the [official release](https://github.com/microsoft/sql-server-samples/releases/tag/wide-world-importers-v1.0).
