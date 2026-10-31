# Workflow diagram source (Mermaid)

This is the original Mermaid version of the project workflow, kept for reference and editing. The main [README](../README.md) shows static SVG versions instead (`assets/readme/workflow-diagram.svg` and `workflow-diagram-mobile.svg`), because Mermaid does not render in every GitHub view, notably on mobile.

```mermaid
flowchart LR
    subgraph S["Source"]
        A[("SQL Server<br/>WideWorldImporters OLTP")] --> B["CSV export<br/>16 tables"]
    end
    subgraph P["Preparation"]
        C["Data understanding<br/>and profiling"] --> D["Individual cleaning<br/>6 member submissions"]
        D --> E{"Team review and<br/>consolidation"}
        E --> F[("Approved unified<br/>dataset")]
    end
    subgraph R["Analytics and BI"]
        G["Exploratory<br/>data analysis"] --> H[("Star schema<br/>data warehouse")]
        H --> I["Power BI<br/>3 report pages"]
    end
    B --> C
    F --> G
    F -->|ETL| H

    classDef done fill:#0F766E,stroke:#2DD4BF,color:#FFFFFF
    classDef active fill:#0E7490,stroke:#22D3EE,color:#FFFFFF,stroke-width:3px
    classDef planned fill:#1E293B,stroke:#64748B,color:#E2E8F0,stroke-dasharray:5 4
    class A,B,C done
    class D active
    class E,F,G,H,I planned
```

Teal: completed. Cyan: in progress. Dashed: pending or planned.
