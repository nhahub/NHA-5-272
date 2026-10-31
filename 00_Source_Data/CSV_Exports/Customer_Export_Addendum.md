# Customer Export Addendum — DEPI Graduation Project

## Scope and provenance

Two customer reference tables were added to connect existing sales/movement records to customers and support later customer-category demand segmentation. This stage performs export verification only, with no EDA, cleaning, imputation, deduplication, derived columns, ETL or notebook creation.

- Verified source: `Omar\SQLEXPRESS` / `WideWorldImporters` (Full OLTP), Windows Authentication.
- Extraction started: `2026-10-17 15:06:25.112308` (SQL Server local timestamp; timezone not encoded).
- Validation completed: `2026-10-17T15:06:26` (local machine time).
- Both source tables are system-versioned; only current rows were read, without FOR SYSTEM_TIME or archive tables.
- Python, pyodbc and pandas were used. All database commands were read-only SELECTs. No database restore, schema change or source write was performed.
- The original **Claude QA report, CSV_Export_QA_Report.html, covers the original 14 CSVs**. It was not updated. This addendum independently documents and validates the two new CSVs and the five requested links to the working dataset.
- The original Data_Dictionary.md remains unchanged. Its original references to Customers being absent describe the earlier 14-file scope; this addendum records the addition.

## New exports

| File | Source | Rows | Columns | Result |
|---|---|---:|---:|---|
| `Sales_Customers.csv` | `Sales.Customers` | 663 | 4 | PASS |
| `Sales_CustomerCategories.csv` | `Sales.CustomerCategories` | 8 | 2 | PASS |

## Sales.Customers

Primary key: `CustomerID`. All values are populated and unique. Records are ordered by the original numeric SQL primary key.

| Column (export order) | SQL type | SQL NULL allowed | Exported NULLs | Empty strings | Definition |
|---|---|---|---:|---:|---|
| `CustomerID` | `int` | No | 0 | 0 | Unique customer identifier; joins to customer references on orders, invoices and stock movements. |
| `CustomerCategoryID` | `int` | No | 0 | 0 | Customer category identifier; links to Sales.CustomerCategories. In that table it is the primary key. |
| `BuyingGroupID` | `int` | Yes | 261 | 0 | Optional buying-group identifier; links to Sales.BuyingGroups, which is deliberately not exported. |
| `AccountOpenedDate` | `date` | No | 0 | 0 | Calendar date the customer account was opened. It is not a transaction or invoice date. |

**Foreign keys exported:**

- `BuyingGroupID` → `Sales.BuyingGroups.BuyingGroupID`.
- `CustomerCategoryID` → `Sales.CustomerCategories.CustomerCategoryID`.

**Excluded source columns (verified from metadata):**

- `CustomerName`: Customer name deliberately excluded; customer ID is sufficient for joins.
- `BillToCustomerID`: Not one of the four/two explicitly approved reference columns; not needed for this addition.
- `PrimaryContactPersonID`: Contact/person reference excluded by the approved privacy-minimal scope.
- `AlternateContactPersonID`: Contact/person reference excluded by the approved privacy-minimal scope.
- `DeliveryMethodID`: Not one of the four/two explicitly approved reference columns; not needed for this addition.
- `DeliveryCityID`: Address/geographic information; not needed for category segmentation.
- `PostalCityID`: Address/geographic information; not needed for category segmentation.
- `CreditLimit`: Credit, payment or account administration information outside the approved scope.
- `StandardDiscountPercentage`: Not one of the four/two explicitly approved reference columns; not needed for this addition.
- `IsStatementSent`: Credit, payment or account administration information outside the approved scope.
- `IsOnCreditHold`: Credit, payment or account administration information outside the approved scope.
- `PaymentDays`: Credit, payment or account administration information outside the approved scope.
- `PhoneNumber`: Contact information; not needed for the requested analysis.
- `FaxNumber`: Contact information; not needed for the requested analysis.
- `DeliveryRun`: Not one of the four/two explicitly approved reference columns; not needed for this addition.
- `RunPosition`: Not one of the four/two explicitly approved reference columns; not needed for this addition.
- `WebsiteURL`: Contact information; not needed for the requested analysis.
- `DeliveryAddressLine1`: Address/geographic information; not needed for category segmentation.
- `DeliveryAddressLine2`: Address/geographic information; not needed for category segmentation.
- `DeliveryPostalCode`: Address/geographic information; not needed for category segmentation.
- `DeliveryLocation`: Address/geographic information; not needed for category segmentation.
- `PostalAddressLine1`: Address/geographic information; not needed for category segmentation.
- `PostalAddressLine2`: Address/geographic information; not needed for category segmentation.
- `PostalPostalCode`: Address/geographic information; not needed for category segmentation.
- `LastEditedBy`: Audit information outside the approved minimal reference scope.
- `ValidFrom`: Temporal period metadata; only current analytical reference rows were requested.
- `ValidTo`: Temporal period metadata; only current analytical reference rows were requested.

**Read-only extraction query:**

```sql
SELECT CONVERT(varchar(20),src.[CustomerID]) AS [CustomerID], CONVERT(varchar(20),src.[CustomerCategoryID]) AS [CustomerCategoryID], CONVERT(varchar(20),src.[BuyingGroupID]) AS [BuyingGroupID], CONVERT(varchar(10),src.[AccountOpenedDate],23) AS [AccountOpenedDate] FROM Sales.Customers AS src ORDER BY src.[CustomerID];
```

**Independent comparison query (native SQL types):**

```sql
SELECT [CustomerID], [CustomerCategoryID], [BuyingGroupID], [AccountOpenedDate] FROM Sales.Customers ORDER BY [CustomerID];
```

File SHA-256: `c6ef6e87e53ef38cb603a507a4d3bc727ba60b5c2339ceb92c572340450b8341`


## Sales.CustomerCategories

Primary key: `CustomerCategoryID`. All values are populated and unique. Records are ordered by the original numeric SQL primary key.

| Column (export order) | SQL type | SQL NULL allowed | Exported NULLs | Empty strings | Definition |
|---|---|---|---:|---:|---|
| `CustomerCategoryID` | `int` | No | 0 | 0 | Customer category identifier; links to Sales.CustomerCategories. In that table it is the primary key. |
| `CustomerCategoryName` | `nvarchar(50)` | No | 0 | 0 | Readable category label used for customer segmentation. |

**Foreign keys exported:**

None. The category identifier is the primary key referenced by Customers.

**Excluded source columns (verified from metadata):**

- `LastEditedBy`: Audit information outside the approved minimal reference scope.
- `ValidFrom`: Temporal period metadata; only current analytical reference rows were requested.
- `ValidTo`: Temporal period metadata; only current analytical reference rows were requested.

**Read-only extraction query:**

```sql
SELECT CONVERT(varchar(20),src.[CustomerCategoryID]) AS [CustomerCategoryID], src.[CustomerCategoryName] FROM Sales.CustomerCategories AS src ORDER BY src.[CustomerCategoryID];
```

**Independent comparison query (native SQL types):**

```sql
SELECT [CustomerCategoryID], [CustomerCategoryName] FROM Sales.CustomerCategories ORDER BY [CustomerCategoryID];
```

File SHA-256: `5f646d90f3135cba2c738e985d3b38dff639eb4d4c59ff8cea9602ce28a8a67a`

## Validation results

- **PASS — schema:** requested columns, order, types and primary keys were checked before writing. No schema mismatch was found.
- **PASS — complete SQL comparison:** every CSV cell was compared to a separate native-type SQL read, in numeric primary-key order. There were zero differing cells, missing rows or extra rows. Counts before and after extraction matched.
- **PASS — keys:** primary keys are non-NULL, unique and equal to the independent SQL keys; all exported reference IDs preserve their source values.
- **PASS — NULLs/dates/text:** per-column NULL counts match SQL; NULL stays distinct from empty text; account dates match native SQL dates; category text is preserved exactly.
- **PASS — encoding/parsing:** UTF-8-SIG with exactly one BOM; all fields quoted; comma separator; quotes escaped by doubling. Both pandas and Python csv parsed all records without ignored errors. A byte-equivalent quote-all serialization check passed.
- **Unicode coverage:** 0 exported cells contain non-ASCII characters. Exact Unicode string comparison and strict UTF-8 decoding passed for all actual values. If this count is zero, non-ASCII sample coverage is **NOT VERIFIED** because no such source value exists in the approved columns; no synthetic records were added.

## Relationship validation

The checks below used the actual existing CSV foreign-key columns and the newly validated reference data. Each left join enforced `validate="many_to_one"`; parent keys were unique and non-NULL. NULL child references were counted separately and were not treated as orphans. Counts were also compared with independent SELECT/LEFT JOIN aggregates in SQL Server.

| Child reference | Parent key | Child rows | NULL references | Matched non-NULL | Orphans | Rows after left join |
|---|---|---:|---:|---:|---:|---:|
| `Sales.Customers.CustomerCategoryID` | `Sales.CustomerCategories.CustomerCategoryID` | 663 | 0 | 663 | 0 | 663 |
| `Sales.Orders.CustomerID` | `Sales.Customers.CustomerID` | 73,595 | 0 | 73,595 | 0 | 73,595 |
| `Sales.Invoices.CustomerID` | `Sales.Customers.CustomerID` | 70,510 | 0 | 70,510 | 0 | 70,510 |
| `Sales.Invoices.BillToCustomerID` | `Sales.Customers.CustomerID` | 70,510 | 0 | 70,510 | 0 | 70,510 |
| `Warehouse.StockItemTransactions.CustomerID` | `Sales.Customers.CustomerID` | 236,667 | 8,402 | 228,265 | 0 | 236,667 |

All five relationships passed: zero orphan references and zero row multiplication. Many child rows may reference one parent; this does not imply one-to-one relationships.

**Buying groups:** `Sales.Customers.BuyingGroupID → Sales.BuyingGroups.BuyingGroupID` is a declared foreign key. A read-only SQL check found 261 legitimate NULL references and 0 orphan non-NULL references among 663 customers. BuyingGroups was not exported, as instructed. Its absence is a scope limitation, not a broken source relationship; CSV-only group-name joins remain unavailable.

## Original-file integrity evidence

SHA-256 was recorded before extraction and recalculated after all export and relationship checks. All 14 original CSVs, Data_Dictionary.md and CSV_Export_QA_Report.html are byte-for-byte unchanged. No original dataset was re-exported. Existing analytical deliverables and backups were not opened, reviewed or modified in this task.

| Protected file | SHA-256 before | SHA-256 after | Result |
|---|---|---|---|
| `Application_DeliveryMethods.csv` | `9250f002553e050e322f1ddaba84db1e44880e76976f1af790a70d15ae446009` | `9250f002553e050e322f1ddaba84db1e44880e76976f1af790a70d15ae446009` | UNCHANGED |
| `Application_TransactionTypes.csv` | `41c5f541afe24550b8213d5ccdbd00c387ff9165cc400bae9476f41b60f1ca75` | `41c5f541afe24550b8213d5ccdbd00c387ff9165cc400bae9476f41b60f1ca75` | UNCHANGED |
| `Purchasing_PurchaseOrderLines.csv` | `d53891aefd150bf3afcb5d84ab40c952bd57786914cc5bb194a151a9b08a7abe` | `d53891aefd150bf3afcb5d84ab40c952bd57786914cc5bb194a151a9b08a7abe` | UNCHANGED |
| `Purchasing_PurchaseOrders.csv` | `4563c934c18da6b401f8a9fe4b5215db630c646a4e4f3d80965c9a62a62e1895` | `4563c934c18da6b401f8a9fe4b5215db630c646a4e4f3d80965c9a62a62e1895` | UNCHANGED |
| `Purchasing_SupplierCategories.csv` | `bcd8bc0a1f8f82f21b8673addca038f3611aa33039f4d0e3bb4f35f0cbb3118f` | `bcd8bc0a1f8f82f21b8673addca038f3611aa33039f4d0e3bb4f35f0cbb3118f` | UNCHANGED |
| `Purchasing_Suppliers.csv` | `f16035d8d9584affd1e2e01516ded9a60fe383d70875f9947899cb4f83d729f8` | `f16035d8d9584affd1e2e01516ded9a60fe383d70875f9947899cb4f83d729f8` | UNCHANGED |
| `Sales_InvoiceLines.csv` | `4bd0b896477780c4cd63626c6d6389e2ae1c68cb336a6ebcdd1245f9a80dfea2` | `4bd0b896477780c4cd63626c6d6389e2ae1c68cb336a6ebcdd1245f9a80dfea2` | UNCHANGED |
| `Sales_Invoices.csv` | `ce9e097934233ff70da0f9d560c6de4b9e6b38a794260e134e7c0b7947be669f` | `ce9e097934233ff70da0f9d560c6de4b9e6b38a794260e134e7c0b7947be669f` | UNCHANGED |
| `Sales_OrderLines.csv` | `841d83aec4359df9904f5f48edf516491315d538d802f3a8519c4394ba194431` | `841d83aec4359df9904f5f48edf516491315d538d802f3a8519c4394ba194431` | UNCHANGED |
| `Sales_Orders.csv` | `556f983436ed6feb6150a5aa8ca55dd260206fdd7736a1b99095fb52b41ff748` | `556f983436ed6feb6150a5aa8ca55dd260206fdd7736a1b99095fb52b41ff748` | UNCHANGED |
| `Warehouse_PackageTypes.csv` | `15cc634cae328f6558384b5138c3e07d4b46238a56e979c11834371b4091405a` | `15cc634cae328f6558384b5138c3e07d4b46238a56e979c11834371b4091405a` | UNCHANGED |
| `Warehouse_StockItemHoldings.csv` | `cf0c0638a954158236ba081bb8a3a63c9b0948e471ea9c3c1dc36e754e72290f` | `cf0c0638a954158236ba081bb8a3a63c9b0948e471ea9c3c1dc36e754e72290f` | UNCHANGED |
| `Warehouse_StockItems.csv` | `d6287e348e6df5371b27e72ba5e8ea759a1d45a8fcd0bc8b0f5717058db3851d` | `d6287e348e6df5371b27e72ba5e8ea759a1d45a8fcd0bc8b0f5717058db3851d` | UNCHANGED |
| `Warehouse_StockItemTransactions.csv` | `b916a5d342b866bd5d4049c2d06eaf57e7eda84ef68a0df450badc47e50345c7` | `b916a5d342b866bd5d4049c2d06eaf57e7eda84ef68a0df450badc47e50345c7` | UNCHANGED |
| `Data_Dictionary.md` | `0cc2937df96da0d9cdafaa0b35c0494ce10670aac32f2950d6777282aaec8623` | `0cc2937df96da0d9cdafaa0b35c0494ce10670aac32f2950d6777282aaec8623` | UNCHANGED |
| `CSV_Export_QA_Report.html` | `9b715d883a0aef87c1d9f6d2962c6c5b83787a14469dceb606de80e443dfbbf6` | `9b715d883a0aef87c1d9f6d2962c6c5b83787a14469dceb606de80e443dfbbf6` | UNCHANGED |

> **Identity note (2026-10-31):** the project-team wording in the headers of this addendum, `Data_Dictionary.md` and `CSV_Export_QA_Report.html` was corrected after export (the team has six members and no official team number). No data, schema or validation content changed; the hashes recorded above describe those files at export time.

## Safe pandas loading and category join

SQL NULL is the exact marker `\N`. Empty strings remain empty. IDs are loaded as strings on both sides of a join to avoid accidental type mismatch or numeric coercion. Dates are stored as `YYYY-MM-DD`; no time or timezone was invented. The following example only loads and joins the two reference files; it does not perform EDA.

```python
from pathlib import Path
import pandas as pd

folder = Path(r'E:\DEPI\DEPI_Graduation_Project_WideWorldImporters\00_Source_Data\CSV_Exports')
options = dict(encoding='utf-8-sig', dtype='string',
               keep_default_na=False, na_values=[r'\N'])
customers = pd.read_csv(folder / 'Sales_Customers.csv', **options)
categories = pd.read_csv(folder / 'Sales_CustomerCategories.csv', **options)
customer_reference = customers.merge(
    categories, on='CustomerCategoryID', how='left', validate='many_to_one'
)
assert len(customer_reference) == len(customers)
assert customer_reference['CustomerCategoryName'].notna().all()
```

Use `CustomerID` to join this reference to Orders.CustomerID, Invoices.CustomerID or Invoices.BillToCustomerID. For invoice segmentation, choose explicitly whether the question concerns the customer or the billed customer. Preserve NULL stock-movement customer references when joining.

## Limitations and completion

- These SELECTs were separate reads, not a transactionally consistent snapshot. Counts and complete selected values matched across the two reads; concurrent changes between reads cannot be ruled out in general.
- The 14 original CSVs were not re-exported or fully re-audited. Their prior independent Claude QA remains the authority for their complete source comparisons. This task verified their hashes and the requested customer relationships.
- BuyingGroup labels and other excluded attributes cannot be analyzed from these two new files. Other original QA warnings about historical inventory, synthetic supplier timings and missing optional lookup tables remain outside this addition.
- Current customer categories do not reconstruct historical category changes.
- There are exactly 16 CSV files after this addition. All are readable by pandas; the original 14 retain their earlier QA status and the two additions pass this addendum's checks. They are ready for the approved future CSV-based EDA scope with the documented limitations.
- No notebook, EDA, ETL or Power BI work was started. Stop here pending approval.
