# Wide World Importers — CSV Data Dictionary

DEPI Team 6 · Export-only preparation for a later pandas EDA notebook. No EDA was performed.

- Source: `Omar\SQLEXPRESS` / `WideWorldImporters`; Windows Authentication.
- Source export started: `2026-10-17 13:57:57.831656` (SQL Server local timestamp; timezone is not encoded).
- Export finished: `2026-10-17T13:59:23` (local machine time).
- Scope: all rows from the 14 named current tables, selected columns only. No archive/history tables.
- Extraction used Python, pyodbc and pandas with 10,000-row chunks. All SQL statements were SELECTs.
- Files are ordered by their primary keys. No filtering, deduplication, imputation, derived business metrics or source changes were performed.

## 1. CSV format and how to read it

- Encoding: **UTF-8-SIG** (one UTF-8 BOM at the start of each file).
- Separator: comma. Every field is double-quoted; embedded double quotes are doubled. Embedded commas/newlines remain part of the quoted value.
- SQL NULL is written as the literal marker `\N`. An empty string remains empty. The export checks that no actual string equals this marker.
- Use the read options below: default pandas NA detection can otherwise mistake text such as `NA` for missing data.
- SQL decimal/numeric values are formatted as exact decimal text by SQL Server before extraction. No float conversion or rounding is applied to these values. CSV has no built-in numeric types.
- Read decimal columns as strings when exact precision matters, then use Python `Decimal` if needed. Default float inference can lose exact decimal precision.
- Keep IDs and barcodes as strings initially. This preserves exact key text, nullable references and any leading zeros in barcodes. Use compatible dtypes on both sides of later joins.
- Flags (SQL bit) are exported as `0` or `1`; their NULL marker remains separate where applicable.
- Dates: `YYYY-MM-DD`. Timestamps: ISO 8601 `YYYY-MM-DDTHH:MM:SS[.fraction]`, preserving the SQL Server fractional precision (up to 7 digits for datetime2). A datetimeoffset, if present, retains its offset. Ordinary datetime/datetime2 values do not contain a timezone; none was invented.
- Source SQL types, decimal precision/scale and NULL allowance are listed below. `NULL allowed` describes the schema, not a missing-value profile.

```python
from pathlib import Path
import pandas as pd

# Set this to the CSV_Exports folder on your computer.
folder = Path(r'E:\DEPI\DEPI_Graduation_Project_WideWorldImporters\00_Source_Data\CSV_Exports')
orders = pd.read_csv(folder / 'Sales_Orders.csv',
                     encoding='utf-8-sig', dtype='string',
                     keep_default_na=False, na_values=[r'\N'])
```

This example only loads data. Convert the chosen date/quantity columns explicitly in the later EDA notebook. Do not convert barcode or identifier columns just because they contain digits.

## 2. Export validation

Every file passed: SQL count before/after = fetched rows = pandas-read rows; exact ordered column names; populated and unique primary keys; matching primary-key SHA-256 fingerprints against an independent SQL reread; and a SHA-256 comparison of every serialized field (including NULL versus empty string) before writing and after reading with pandas. UTF-8 decoding was strict and malformed CSV rows were not skipped.

| File | Rows | Columns | Validation |
|---|---:|---:|---|
| `Sales_Orders.csv` | 73,595 | 12 | PASS |
| `Sales_OrderLines.csv` | 231,412 | 12 | PASS |
| `Sales_Invoices.csv` | 70,510 | 16 | PASS |
| `Sales_InvoiceLines.csv` | 228,265 | 13 | PASS |
| `Purchasing_Suppliers.csv` | 13 | 10 | PASS |
| `Purchasing_SupplierCategories.csv` | 9 | 3 | PASS |
| `Purchasing_PurchaseOrders.csv` | 2,074 | 9 | PASS |
| `Purchasing_PurchaseOrderLines.csv` | 8,367 | 12 | PASS |
| `Warehouse_StockItems.csv` | 227 | 17 | PASS |
| `Warehouse_StockItemHoldings.csv` | 227 | 9 | PASS |
| `Warehouse_StockItemTransactions.csv` | 236,667 | 11 | PASS |
| `Warehouse_PackageTypes.csv` | 14 | 3 | PASS |
| `Application_TransactionTypes.csv` | 13 | 3 | PASS |
| `Application_DeliveryMethods.csv` | 10 | 3 | PASS |

The content comparison proves that the exported selected values survived CSV serialization. It is not an EDA or a certification of every business rule. Foreign-key column values were retained and included in the all-field comparison; parent tables outside this export were not exported.

## 3. Table-by-table dictionary

### 3.1 Sales.Orders

- **File:** `Sales_Orders.csv`
- **Rows / exported columns:** 73,595 / 12
- **Business purpose and row meaning:** One customer sales order.
- **Primary key:** `OrderID`
- **Supply chain use:** Study order dates, expected delivery and backorder links.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `OrderID` | `int` | No | Unique identifier for this row. |
| `CustomerID` | `int` | No | Reference to `Sales.Customers.CustomerID`. |
| `SalespersonPersonID` | `int` | No | Reference to `Application.People.PersonID`. Operational person ID only; personal details are excluded. |
| `PickedByPersonID` | `int` | Yes | Reference to `Application.People.PersonID`. Operational person ID only; personal details are excluded. |
| `ContactPersonID` | `int` | No | Reference to `Application.People.PersonID`. Operational person ID only; personal details are excluded. |
| `BackorderOrderID` | `int` | Yes | Reference to `Sales.Orders.OrderID`. Optional link to the related backorder; not a new independent demand measure. |
| `OrderDate` | `date` | No | Date the order was placed. |
| `ExpectedDeliveryDate` | `date` | No | Planned delivery date; not evidence of actual delivery. |
| `IsUndersupplyBackordered` | `bit` | No | Flag showing whether undersupplied quantities should be backordered. |
| `PickingCompletedWhen` | `datetime2(7)` | Yes | Recorded completion timestamp for picking; NULL can indicate incomplete picking. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |
| `LastEditedWhen` | `datetime2(7)` | No | Source audit timestamp of the latest edit; not necessarily the business event date. |

**Foreign keys and related tables**

- `BackorderOrderID` → `Sales.Orders.OrderID` (included in this export).
- `ContactPersonID` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `CustomerID` → `Sales.Customers.CustomerID` (not included; only the reference ID is retained).
- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `PickedByPersonID` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `SalespersonPersonID` → `Application.People.PersonID` (not included; only the reference ID is retained).

**Excluded columns**

- `CustomerPurchaseOrderNumber`: External customer reference; unnecessary for the planned table joins.
- `Comments`: Optional operational free text; can contain unnecessary personal information.
- `DeliveryInstructions`: Free-text delivery instructions may contain personal/location details.
- `InternalComments`: Internal free text; unnecessary and may contain sensitive details.

File SHA-256: `556f983436ed6feb6150a5aa8ca55dd260206fdd7736a1b99095fb52b41ff748`

### 3.2 Sales.OrderLines

- **File:** `Sales_OrderLines.csv`
- **Rows / exported columns:** 231,412 / 12
- **Business purpose and row meaning:** One product line within a customer order.
- **Primary key:** `OrderLineID`
- **Supply chain use:** Explore ordered and picked quantities by product and order.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `OrderLineID` | `int` | No | Unique identifier for this row. |
| `OrderID` | `int` | No | Reference to `Sales.Orders.OrderID`. |
| `StockItemID` | `int` | No | Reference to `Warehouse.StockItems.StockItemID`. |
| `Description` | `nvarchar` | No | Product/line description as recorded for the transaction. |
| `PackageTypeID` | `int` | No | Reference to `Warehouse.PackageTypes.PackageTypeID`. |
| `Quantity` | `int` | No | Recorded line or movement quantity; interpret with the package or transaction type. |
| `UnitPrice` | `decimal(18,2)` | Yes | Recorded selling price per unit in the table's package context. |
| `TaxRate` | `decimal(18,3)` | No | Recorded tax percentage. |
| `PickedQuantity` | `int` | No | Quantity already picked for this sales order line. |
| `PickingCompletedWhen` | `datetime2(7)` | Yes | Recorded completion timestamp for picking; NULL can indicate incomplete picking. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |
| `LastEditedWhen` | `datetime2(7)` | No | Source audit timestamp of the latest edit; not necessarily the business event date. |

**Foreign keys and related tables**

- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `OrderID` → `Sales.Orders.OrderID` (included in this export).
- `PackageTypeID` → `Warehouse.PackageTypes.PackageTypeID` (included in this export).
- `StockItemID` → `Warehouse.StockItems.StockItemID` (included in this export).

**Excluded columns**

None: all source columns are included.

File SHA-256: `841d83aec4359df9904f5f48edf516491315d538d802f3a8519c4394ba194431`

### 3.3 Sales.Invoices

- **File:** `Sales_Invoices.csv`
- **Rows / exported columns:** 70,510 / 16
- **Business purpose and row meaning:** One invoice or credit-note header.
- **Primary key:** `InvoiceID`
- **Supply chain use:** Connect invoiced activity to dates, customers and orders; distinguish credit notes.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `InvoiceID` | `int` | No | Unique identifier for this row. |
| `CustomerID` | `int` | No | Reference to `Sales.Customers.CustomerID`. |
| `BillToCustomerID` | `int` | No | Reference to `Sales.Customers.CustomerID`. |
| `OrderID` | `int` | Yes | Reference to `Sales.Orders.OrderID`. |
| `DeliveryMethodID` | `int` | No | Reference to `Application.DeliveryMethods.DeliveryMethodID`. |
| `ContactPersonID` | `int` | No | Reference to `Application.People.PersonID`. Operational person ID only; personal details are excluded. |
| `AccountsPersonID` | `int` | No | Reference to `Application.People.PersonID`. Operational person ID only; personal details are excluded. |
| `SalespersonPersonID` | `int` | No | Reference to `Application.People.PersonID`. Operational person ID only; personal details are excluded. |
| `PackedByPersonID` | `int` | No | Reference to `Application.People.PersonID`. Operational person ID only; personal details are excluded. |
| `InvoiceDate` | `date` | No | Date of the invoice; not necessarily the delivery date. |
| `IsCreditNote` | `bit` | No | 1 for a credit note, 0 otherwise. Check this before interpreting billed activity. |
| `TotalDryItems` | `int` | No | Header count of dry items; do not repeat and sum it after joining invoice lines. |
| `TotalChillerItems` | `int` | No | Header count of chiller items; do not repeat and sum it after joining invoice lines. |
| `ConfirmedDeliveryTime` | `datetime2(7)` | Yes | Recorded delivery confirmation timestamp; may be NULL. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |
| `LastEditedWhen` | `datetime2(7)` | No | Source audit timestamp of the latest edit; not necessarily the business event date. |

**Foreign keys and related tables**

- `AccountsPersonID` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `BillToCustomerID` → `Sales.Customers.CustomerID` (not included; only the reference ID is retained).
- `ContactPersonID` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `CustomerID` → `Sales.Customers.CustomerID` (not included; only the reference ID is retained).
- `DeliveryMethodID` → `Application.DeliveryMethods.DeliveryMethodID` (included in this export).
- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `OrderID` → `Sales.Orders.OrderID` (included in this export).
- `PackedByPersonID` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `SalespersonPersonID` → `Application.People.PersonID` (not included; only the reference ID is retained).

**Excluded columns**

- `CustomerPurchaseOrderNumber`: External customer reference; unnecessary for the planned table joins.
- `CreditNoteReason`: Free-text explanation; credit-note status is retained without narrative details.
- `Comments`: Optional operational free text; can contain unnecessary personal information.
- `DeliveryInstructions`: Free-text delivery instructions may contain personal/location details.
- `InternalComments`: Internal free text; unnecessary and may contain sensitive details.
- `DeliveryRun`: Operational route label; outside the initial supply chain dataset scope.
- `RunPosition`: Operational route position; outside the initial dataset scope.
- `ReturnedDeliveryData`: Large delivery JSON payload may contain recipient and location details.
- `ConfirmedReceivedBy`: Recipient name; unnecessary personal information.

File SHA-256: `ce9e097934233ff70da0f9d560c6de4b9e6b38a794260e134e7c0b7947be669f`

### 3.4 Sales.InvoiceLines

- **File:** `Sales_InvoiceLines.csv`
- **Rows / exported columns:** 228,265 / 13
- **Business purpose and row meaning:** One product line on an invoice.
- **Primary key:** `InvoiceLineID`
- **Supply chain use:** Explore invoiced quantities, recorded prices, taxes and stored line amounts.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `InvoiceLineID` | `int` | No | Unique identifier for this row. |
| `InvoiceID` | `int` | No | Reference to `Sales.Invoices.InvoiceID`. |
| `StockItemID` | `int` | No | Reference to `Warehouse.StockItems.StockItemID`. |
| `Description` | `nvarchar` | No | Product/line description as recorded for the transaction. |
| `PackageTypeID` | `int` | No | Reference to `Warehouse.PackageTypes.PackageTypeID`. |
| `Quantity` | `int` | No | Recorded line or movement quantity; interpret with the package or transaction type. |
| `UnitPrice` | `decimal(18,2)` | Yes | Recorded selling price per unit in the table's package context. |
| `TaxRate` | `decimal(18,3)` | No | Recorded tax percentage. |
| `TaxAmount` | `decimal(18,2)` | No | Recorded tax amount for the invoice line. |
| `LineProfit` | `decimal(18,2)` | No | Stored source line-profit amount. Its accounting definition must be validated before a profit KPI. |
| `ExtendedPrice` | `decimal(18,2)` | No | Recorded invoice-line amount including tax. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |
| `LastEditedWhen` | `datetime2(7)` | No | Source audit timestamp of the latest edit; not necessarily the business event date. |

**Foreign keys and related tables**

- `InvoiceID` → `Sales.Invoices.InvoiceID` (included in this export).
- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `PackageTypeID` → `Warehouse.PackageTypes.PackageTypeID` (included in this export).
- `StockItemID` → `Warehouse.StockItems.StockItemID` (included in this export).

**Excluded columns**

None: all source columns are included.

File SHA-256: `4bd0b896477780c4cd63626c6d6389e2ae1c68cb336a6ebcdd1245f9a80dfea2`

### 3.5 Purchasing.Suppliers

- **File:** `Purchasing_Suppliers.csv`
- **Rows / exported columns:** 13 / 10
- **Business purpose and row meaning:** One current supplier business record.
- **Primary key:** `SupplierID`
- **Supply chain use:** Group purchasing activity by supplier and supplier category.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `SupplierID` | `int` | No | Unique identifier for this row. |
| `SupplierName` | `nvarchar` | No | Supplier business name. |
| `SupplierCategoryID` | `int` | No | Reference to `Purchasing.SupplierCategories.SupplierCategoryID`. |
| `PrimaryContactPersonID` | `int` | No | Reference to `Application.People.PersonID`. Operational person ID only; personal details are excluded. |
| `AlternateContactPersonID` | `int` | No | Reference to `Application.People.PersonID`. Operational person ID only; personal details are excluded. |
| `DeliveryMethodID` | `int` | Yes | Reference to `Application.DeliveryMethods.DeliveryMethodID`. |
| `DeliveryCityID` | `int` | No | Reference to `Application.Cities.CityID`. |
| `PostalCityID` | `int` | No | Reference to `Application.Cities.CityID`. |
| `PaymentDays` | `int` | No | Supplier payment term in days; not delivery lead time. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |

**Foreign keys and related tables**

- `AlternateContactPersonID` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `DeliveryCityID` → `Application.Cities.CityID` (not included; only the reference ID is retained).
- `DeliveryMethodID` → `Application.DeliveryMethods.DeliveryMethodID` (included in this export).
- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `PostalCityID` → `Application.Cities.CityID` (not included; only the reference ID is retained).
- `PrimaryContactPersonID` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `SupplierCategoryID` → `Purchasing.SupplierCategories.SupplierCategoryID` (included in this export).

**Excluded columns**

- `SupplierReference`: External supplier reference; unnecessary for the planned joins.
- `BankAccountName`: Bank/account information; excluded from analytical exports.
- `BankAccountBranch`: Bank/account information; excluded from analytical exports.
- `BankAccountCode`: Bank/account information; excluded from analytical exports.
- `BankAccountNumber`: Bank/account information; excluded from analytical exports.
- `BankInternationalCode`: Bank/account information; excluded from analytical exports.
- `InternalComments`: Internal free text; unnecessary and may contain sensitive details.
- `PhoneNumber`: Supplier contact information; excluded.
- `FaxNumber`: Supplier contact information; excluded.
- `WebsiteURL`: Contact/web information; unnecessary for this analysis.
- `DeliveryAddressLine1`: Supplier address/postcode; unnecessary location/contact information.
- `DeliveryAddressLine2`: Supplier address/postcode; unnecessary location/contact information.
- `DeliveryPostalCode`: Supplier address/postcode; unnecessary location/contact information.
- `DeliveryLocation`: Spatial supplier location; unnecessary detailed location data.
- `PostalAddressLine1`: Supplier address/postcode; unnecessary location/contact information.
- `PostalAddressLine2`: Supplier address/postcode; unnecessary location/contact information.
- `PostalPostalCode`: Supplier address/postcode; unnecessary location/contact information.
- `ValidFrom`: System-versioning period metadata; current rows are exported without history.
- `ValidTo`: System-versioning period metadata; current rows are exported without history.

File SHA-256: `f16035d8d9584affd1e2e01516ded9a60fe383d70875f9947899cb4f83d729f8`

### 3.6 Purchasing.SupplierCategories

- **File:** `Purchasing_SupplierCategories.csv`
- **Rows / exported columns:** 9 / 3
- **Business purpose and row meaning:** One current supplier category.
- **Primary key:** `SupplierCategoryID`
- **Supply chain use:** Translate category IDs into understandable supplier groups.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `SupplierCategoryID` | `int` | No | Unique identifier for this row. |
| `SupplierCategoryName` | `nvarchar` | No | Readable supplier-category label. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |

**Foreign keys and related tables**

- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).

**Excluded columns**

- `ValidFrom`: System-versioning period metadata; current rows are exported without history.
- `ValidTo`: System-versioning period metadata; current rows are exported without history.

File SHA-256: `bcd8bc0a1f8f82f21b8673addca038f3611aa33039f4d0e3bb4f35f0cbb3118f`

### 3.7 Purchasing.PurchaseOrders

- **File:** `Purchasing_PurchaseOrders.csv`
- **Rows / exported columns:** 2,074 / 9
- **Business purpose and row meaning:** One purchase order sent to a supplier.
- **Primary key:** `PurchaseOrderID`
- **Supply chain use:** Explore supplier activity, purchasing dates and finalization status.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `PurchaseOrderID` | `int` | No | Unique identifier for this row. |
| `SupplierID` | `int` | No | Reference to `Purchasing.Suppliers.SupplierID`. |
| `OrderDate` | `date` | No | Date the order was placed. |
| `DeliveryMethodID` | `int` | No | Reference to `Application.DeliveryMethods.DeliveryMethodID`. |
| `ContactPersonID` | `int` | No | Reference to `Application.People.PersonID`. Operational person ID only; personal details are excluded. |
| `ExpectedDeliveryDate` | `date` | Yes | Planned delivery date; not evidence of actual delivery. |
| `IsOrderFinalized` | `bit` | No | 1 if the purchase order is finalized, 0 otherwise. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |
| `LastEditedWhen` | `datetime2(7)` | No | Source audit timestamp of the latest edit; not necessarily the business event date. |

**Foreign keys and related tables**

- `ContactPersonID` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `DeliveryMethodID` → `Application.DeliveryMethods.DeliveryMethodID` (included in this export).
- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `SupplierID` → `Purchasing.Suppliers.SupplierID` (included in this export).

**Excluded columns**

- `SupplierReference`: External supplier reference; unnecessary for the planned joins.
- `Comments`: Optional operational free text; can contain unnecessary personal information.
- `InternalComments`: Internal free text; unnecessary and may contain sensitive details.

File SHA-256: `4563c934c18da6b401f8a9fe4b5215db630c646a4e4f3d80965c9a62a62e1895`

### 3.8 Purchasing.PurchaseOrderLines

- **File:** `Purchasing_PurchaseOrderLines.csv`
- **Rows / exported columns:** 8,367 / 12
- **Business purpose and row meaning:** One product line within a purchase order.
- **Primary key:** `PurchaseOrderLineID`
- **Supply chain use:** Compare ordered and received outers and review receipt status.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `PurchaseOrderLineID` | `int` | No | Unique identifier for this row. |
| `PurchaseOrderID` | `int` | No | Reference to `Purchasing.PurchaseOrders.PurchaseOrderID`. |
| `StockItemID` | `int` | No | Reference to `Warehouse.StockItems.StockItemID`. |
| `OrderedOuters` | `int` | No | Number of outer packs ordered from the supplier. |
| `Description` | `nvarchar` | No | Product/line description as recorded for the transaction. |
| `ReceivedOuters` | `int` | No | Number of outer packs received for this purchase line. |
| `PackageTypeID` | `int` | No | Reference to `Warehouse.PackageTypes.PackageTypeID`. |
| `ExpectedUnitPricePerOuter` | `decimal(18,2)` | Yes | Expected price for one outer pack; not final actual spending. |
| `LastReceiptDate` | `date` | Yes | Date of the most recent receipt for this purchase line; not a log of every partial receipt. |
| `IsOrderLineFinalized` | `bit` | No | 1 if the purchase line is finalized, 0 otherwise. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |
| `LastEditedWhen` | `datetime2(7)` | No | Source audit timestamp of the latest edit; not necessarily the business event date. |

**Foreign keys and related tables**

- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `PackageTypeID` → `Warehouse.PackageTypes.PackageTypeID` (included in this export).
- `PurchaseOrderID` → `Purchasing.PurchaseOrders.PurchaseOrderID` (included in this export).
- `StockItemID` → `Warehouse.StockItems.StockItemID` (included in this export).

**Excluded columns**

None: all source columns are included.

File SHA-256: `d53891aefd150bf3afcb5d84ab40c952bd57786914cc5bb194a151a9b08a7abe`

### 3.9 Warehouse.StockItems

- **File:** `Warehouse_StockItems.csv`
- **Rows / exported columns:** 227 / 17
- **Business purpose and row meaning:** One current product in the stock catalog.
- **Primary key:** `StockItemID`
- **Supply chain use:** Describe products, supplier links, package settings and item attributes.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `StockItemID` | `int` | No | Unique identifier for this row. |
| `StockItemName` | `nvarchar` | No | Current product name. |
| `SupplierID` | `int` | No | Reference to `Purchasing.Suppliers.SupplierID`. |
| `ColorID` | `int` | Yes | Reference to `Warehouse.Colors.ColorID`. |
| `UnitPackageID` | `int` | No | Reference to `Warehouse.PackageTypes.PackageTypeID`. |
| `OuterPackageID` | `int` | No | Reference to `Warehouse.PackageTypes.PackageTypeID`. |
| `Brand` | `nvarchar` | Yes | Product brand; may be absent or not applicable. |
| `Size` | `nvarchar` | Yes | Product size label; may be absent or not applicable. |
| `LeadTimeDays` | `int` | No | Configured product lead time in days; not observed supplier performance. |
| `QuantityPerOuter` | `int` | No | Current number of units per outer pack; historical conversions may differ. |
| `IsChillerStock` | `bit` | No | 1 for an item requiring chilled storage, 0 otherwise. |
| `Barcode` | `nvarchar` | Yes | Product barcode text. Keep as string to retain leading zeroes. |
| `TaxRate` | `decimal(18,3)` | No | Recorded tax percentage. |
| `UnitPrice` | `decimal(18,2)` | No | Recorded selling price per unit in the table's package context. |
| `RecommendedRetailPrice` | `decimal(18,2)` | Yes | Stored recommended retail price; not necessarily the actual selling price. |
| `TypicalWeightPerUnit` | `decimal(18,3)` | No | Stored typical weight per unit; verify the business unit before physical-volume calculations. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |

**Foreign keys and related tables**

- `ColorID` → `Warehouse.Colors.ColorID` (not included; only the reference ID is retained).
- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `OuterPackageID` → `Warehouse.PackageTypes.PackageTypeID` (included in this export).
- `SupplierID` → `Purchasing.Suppliers.SupplierID` (included in this export).
- `UnitPackageID` → `Warehouse.PackageTypes.PackageTypeID` (included in this export).

**Excluded columns**

- `MarketingComments`: Marketing free text; unnecessary for the requested operational exports.
- `InternalComments`: Internal free text; unnecessary and may contain sensitive details.
- `Photo`: Binary product image; unnecessary for tabular analysis.
- `CustomFields`: Large flexible JSON payload; outside the initial tabular analysis scope.
- `Tags`: Derived JSON/text tags; excluded with flexible product payloads.
- `SearchDetails`: Large derived search text; duplicates product information.
- `ValidFrom`: System-versioning period metadata; current rows are exported without history.
- `ValidTo`: System-versioning period metadata; current rows are exported without history.

File SHA-256: `d6287e348e6df5371b27e72ba5e8ea759a1d45a8fcd0bc8b0f5717058db3851d`

### 3.10 Warehouse.StockItemHoldings

- **File:** `Warehouse_StockItemHoldings.csv`
- **Rows / exported columns:** 227 / 9
- **Business purpose and row meaning:** One current stock-holding record per product.
- **Primary key:** `StockItemID`
- **Supply chain use:** Compare each item's quantity on hand with its own reorder and target levels.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `StockItemID` | `int` | No | Reference to `Warehouse.StockItems.StockItemID`. Also uniquely identifies this row. |
| `QuantityOnHand` | `int` | No | Current recorded stock quantity for this item; not a daily availability history. |
| `BinLocation` | `nvarchar` | No | Warehouse bin code for the item; a storage location, not a personal address. |
| `LastStocktakeQuantity` | `int` | No | Quantity recorded at the most recent stocktake. |
| `LastCostPrice` | `decimal(18,2)` | No | Recorded most recent cost price; not a historical cost series. |
| `ReorderLevel` | `int` | No | Configured stock level used to trigger replenishment review. |
| `TargetStockLevel` | `int` | No | Configured target stock quantity for the item. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |
| `LastEditedWhen` | `datetime2(7)` | No | Source audit timestamp of the latest edit; not necessarily the business event date. |

**Foreign keys and related tables**

- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `StockItemID` → `Warehouse.StockItems.StockItemID` (included in this export).

**Excluded columns**

None: all source columns are included.

File SHA-256: `cf0c0638a954158236ba081bb8a3a63c9b0948e471ea9c3c1dc36e754e72290f`

### 3.11 Warehouse.StockItemTransactions

- **File:** `Warehouse_StockItemTransactions.csv`
- **Rows / exported columns:** 236,667 / 11
- **Business purpose and row meaning:** One stock movement.
- **Primary key:** `StockItemTransactionID`
- **Supply chain use:** Explore receipts, issues and adjustments using their transaction types.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `StockItemTransactionID` | `int` | No | Unique identifier for this row. |
| `StockItemID` | `int` | No | Reference to `Warehouse.StockItems.StockItemID`. |
| `TransactionTypeID` | `int` | No | Reference to `Application.TransactionTypes.TransactionTypeID`. |
| `CustomerID` | `int` | Yes | Reference to `Sales.Customers.CustomerID`. |
| `InvoiceID` | `int` | Yes | Reference to `Sales.Invoices.InvoiceID`. |
| `SupplierID` | `int` | Yes | Reference to `Purchasing.Suppliers.SupplierID`. |
| `PurchaseOrderID` | `int` | Yes | Reference to `Purchasing.PurchaseOrders.PurchaseOrderID`. |
| `TransactionOccurredWhen` | `datetime2(7)` | No | Recorded timestamp of the stock movement. |
| `Quantity` | `decimal(18,3)` | No | Recorded line or movement quantity; interpret with the package or transaction type. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |
| `LastEditedWhen` | `datetime2(7)` | No | Source audit timestamp of the latest edit; not necessarily the business event date. |

**Foreign keys and related tables**

- `CustomerID` → `Sales.Customers.CustomerID` (not included; only the reference ID is retained).
- `InvoiceID` → `Sales.Invoices.InvoiceID` (included in this export).
- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).
- `PurchaseOrderID` → `Purchasing.PurchaseOrders.PurchaseOrderID` (included in this export).
- `StockItemID` → `Warehouse.StockItems.StockItemID` (included in this export).
- `SupplierID` → `Purchasing.Suppliers.SupplierID` (included in this export).
- `TransactionTypeID` → `Application.TransactionTypes.TransactionTypeID` (included in this export).

**Excluded columns**

None: all source columns are included.

File SHA-256: `b916a5d342b866bd5d4049c2d06eaf57e7eda84ef68a0df450badc47e50345c7`

### 3.12 Warehouse.PackageTypes

- **File:** `Warehouse_PackageTypes.csv`
- **Rows / exported columns:** 14 / 3
- **Business purpose and row meaning:** One current packaging type.
- **Primary key:** `PackageTypeID`
- **Supply chain use:** Translate package IDs into labels such as Each or Carton.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `PackageTypeID` | `int` | No | Unique identifier for this row. |
| `PackageTypeName` | `nvarchar` | No | Readable packaging-type label. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |

**Foreign keys and related tables**

- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).

**Excluded columns**

- `ValidFrom`: System-versioning period metadata; current rows are exported without history.
- `ValidTo`: System-versioning period metadata; current rows are exported without history.

File SHA-256: `15cc634cae328f6558384b5138c3e07d4b46238a56e979c11834371b4091405a`

### 3.13 Application.TransactionTypes

- **File:** `Application_TransactionTypes.csv`
- **Rows / exported columns:** 13 / 3
- **Business purpose and row meaning:** One current transaction-type code.
- **Primary key:** `TransactionTypeID`
- **Supply chain use:** Interpret movement types before interpreting positive or negative quantities.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `TransactionTypeID` | `int` | No | Unique identifier for this row. |
| `TransactionTypeName` | `nvarchar` | No | Readable transaction-type label. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |

**Foreign keys and related tables**

- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).

**Excluded columns**

- `ValidFrom`: System-versioning period metadata; current rows are exported without history.
- `ValidTo`: System-versioning period metadata; current rows are exported without history.

File SHA-256: `41c5f541afe24550b8213d5ccdbd00c387ff9165cc400bae9476f41b60f1ca75`

### 3.14 Application.DeliveryMethods

- **File:** `Application_DeliveryMethods.csv`
- **Rows / exported columns:** 10 / 3
- **Business purpose and row meaning:** One current delivery-method code.
- **Primary key:** `DeliveryMethodID`
- **Supply chain use:** Describe delivery methods used on purchase orders, invoices and supplier records.

| Exported column | SQL type | NULL allowed | Meaning |
|---|---|---|---|
| `DeliveryMethodID` | `int` | No | Unique identifier for this row. |
| `DeliveryMethodName` | `nvarchar` | No | Readable delivery-method label. |
| `LastEditedBy` | `int` | No | Reference to `Application.People.PersonID`. Audit editor ID only; no person names/contact details are exported. |

**Foreign keys and related tables**

- `LastEditedBy` → `Application.People.PersonID` (not included; only the reference ID is retained).

**Excluded columns**

- `ValidFrom`: System-versioning period metadata; current rows are exported without history.
- `ValidTo`: System-versioning period metadata; current rows are exported without history.

File SHA-256: `9250f002553e050e322f1ddaba84db1e44880e76976f1af790a70d15ae446009`

## 4. Relationships in simple terms

- A supplier can have many purchase orders. Join `Purchasing_PurchaseOrders.SupplierID` to `Purchasing_Suppliers.SupplierID` to attach the supplier name.
- A purchase order can have several purchase lines. For example, an order header records the supplier and order date; its lines record which products and how many outer packs were ordered. Join on `PurchaseOrderID`.
- A sales order can have several sales lines. `OrderID` repeats in the line file because each line is a separate product line. `OrderLineID` is the unique line key.
- An invoice can have several invoice lines. Use `InvoiceID` to attach its date to each line. `Invoices.OrderID` refers back to an order, but do not assume one invoice per order without checking.
- `StockItemID` connects purchase lines, order lines, invoice lines, holdings and movements to the product catalog. The holdings file has one row per item key.
- `StockItemTransactions.TransactionTypeID` joins to the transaction-type labels. A negative stock issue can be normal; supplier/customer/invoice/order references depend on the movement type.
- Product `UnitPackageID` and `OuterPackageID`, and line `PackageTypeID`, point to `Warehouse.PackageTypes`. OrderedOuters means outer packs; do not add them directly to sales units. Current QuantityPerOuter is not automatically the historical conversion.
- SupplierCategoryID joins suppliers to category names. DeliveryMethodID joins the relevant headers/suppliers to delivery-method labels.
- Person, customer, city and color IDs are kept where they are declared foreign keys. Their parent tables are outside the requested 14 files. A retained ID does not provide the missing name/details.

## 5. Join and interpretation cautions

- When joining lines to a header, use a many-to-one relationship and verify that the number of line rows is unchanged.
- Do not directly combine order lines with invoice lines through order headers and then sum both. Multiple lines on each side can multiply rows. Aggregate each dataset to the intended level first.
- Header totals such as TotalDryItems must not be repeatedly summed after a header-to-line join.
- StockItemHoldings is current stock, not historical daily availability. A current balance cannot establish historical stockout rates.
- LastReceiptDate is the last receipt date; measuring supplier delivery performance requires definitions for partial receipts and finalized orders.
- Current temporal tables were read without FOR SYSTEM_TIME. The exports do not reconstruct historical product/supplier attributes.
- These files come from historical sample data. Export time is not the latest business transaction date.
- The exports use separate SELECTs and are not one atomic snapshot of all tables. Counts and keys were reread successfully, but concurrent changes that preserve row counts/keys cannot be ruled out. Use an unchanged training database for a consistent repeat export.
- Precision-preserving CSV quoting is not spreadsheet formula sanitization. Use pandas for these source extracts; source text was not altered with prefixes.
- Existing notebooks, reports, HTML explanations and .bak files were checked with SHA-256 before and after export and remain unchanged.
- No new notebook, EDA, cleaning, ETL or dashboard was created. This export stage ends here, pending team approval.
