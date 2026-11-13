# README visual system

Original graphics for the official project landing page. No business values are inferred from illustrative charts.

- Palette: navy `#071527`, midnight `#0B1E36`, cyan `#00D4FF`, teal `#00C9A7`, purple `#8B5CF6`, white `#EAF4FF`.
- Three animated moments: supply-chain network, architectural data flow and analytical-domain motifs.
- Each GIF has 40 frames at 100 ms per frame, a shared 128-color palette and an equivalent static PNG. Desktop and mobile compositions are separate.
- README picture sources prefer static PNGs for reduced-motion settings, mobile GIFs on narrow screens and desktop GIFs otherwise. Direct static links remain available if a client ignores media preferences.
- Gold grain and validation graphics are static SVGs with accessible text descriptions in the README.
- Architecture solid stages represent implemented layers; dashed reporting stages are planned. The local test validates the restored snapshot, not a new source extraction or production deployment.

## Reproduce

From the repository root on Windows, using a trusted Python environment with Pillow and installed Segoe UI fonts:

```powershell
python assets/readme/source/render_visuals.py
```

The generator only writes README graphics under `assets/readme/`. It does not read source datasets, connect to SQL Server or modify project implementations. No external logos, stock images or JavaScript embeds are required.
