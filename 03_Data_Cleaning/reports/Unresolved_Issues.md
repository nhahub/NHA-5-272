# Remaining Business Questions and Analytical Limitations

The completed focused review resolved the need for data correction in the picker-ID and negative-profit cases: KEEP both. The 167 inherited-date invoices remain FLAGGED for interpretation. No additional values were changed.

## Business confirmation still required

**Warehouse.StockItemHoldings: all 227 discrepancies remain NEEDS REVIEW / REQUIRES BUSINESS CONFIRMATION.** Nine items imply negative opening balances. The generator template has a potential receipt-update scope defect, but historical execution is unproven. Obtain verified opening balances, complete movement/adjustment history and execution provenance before reconciliation. Never fabricate balancing movements or replace current holdings with movement sums.

## Residual questions that do not justify changing values

- Actual picker identity is unknown for 7,538 split orders. Do not substitute audit editors, packers or salespeople.
- The commercial reasons for 4,626 negative-profit lines and independently dated historical costs are unverified. Keep signed profits; do not claim an intentional promotion or pricing error.
- Agree the future cycle-time definition for 167 backorder-linked invoices: inherited OrderDate is not a reliable backorder creation timestamp, and the 365-day threshold is not an SLA.
- Team approval of the unified cleaning approach is pending. This is one member's submission.

## Known analytical limits

- Holdings are current snapshots, not reconciled historical balances. Do not derive defensible historical stockout rates or turnover from unverified balances.
- 2016 is incomplete; supplier timing is synthetic; current reference attributes do not recreate history.
- Purchasing outer packs and sales quantities require explicit package context.
- Optional NULLs, constant columns and statistical outliers are not automatically errors.
- External lookup references passed the saved SQL checks but cannot be revalidated from these 16 CSV files alone. Separate SQL reads were not an atomic snapshot.

See [Business Validation Review](Business_Validation_Review.md), [final dispositions](final_business_disposition.json) and [final handoff](Final_Cleaning_Handoff.md).
