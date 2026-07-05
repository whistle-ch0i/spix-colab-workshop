# Manuscript Link

The live notebook is not a full paper rebuild. It is the small version we can run
in a workshop room. The full panel reproduction stays with the manuscript
analysis package.

Primary reference files:

- `manifest/panel_manifest.tsv`
- `manifest/package_verification.tsv`
- `reports/`
- `plots/main/`
- `plots/supplementary/`

## Run Live

These parts are small enough for the Colab notebook.

| Manuscript result | Workshop analogue | Why it is appropriate |
|---|---|---|
| Fig2A: Visium HD multiscale SPIX segmentation | Run SPIX segmentation at 48, 96, 192, and 384 um | Same count/coordinate to embedding image to SLIC-style SPIX route, but on a bounded ROI |
| Fig3A and sFig9: scale-response SVG trajectories | Compute multiscale Moran's I and plot top-gene trajectories | Same SVG ranking concept; smaller gene/spot set for live execution |
| Fig3B and sFig8: native and SPIX expression maps | Plot native expression beside segment-averaged expression for representative genes | Same visual interpretation logic without requiring full-section raw data |
| Fig5A-F concept: expression contrast is not spatial organization | Plot mean expression versus peak multiscale Moran's I in one ROI | Concept demo only; does not replace paired NAT/CRC analysis |

Simple way to phrase it during the workshop:

> We are running the same SPIX analysis idea on a small public Visium HD ROI, so
> everyone can finish the workflow during the session.

## Show As Reference

These are important paper results, but they belong in the full local pipeline,
not in the live Colab run.

| Manuscript result | Reason not to run in free Colab | Reference route |
|---|---|---|
| Full Fig1B MOSTA multiscale segmentation | Large Stereo-seq input and long 16-scale run | `Fig1B` entries in `manifest/panel_manifest.tsv` |
| Fig2D-G SPATCH/Grid metrics | Six-sample raw SPATCH workflow plus H&E/CODEX inputs | `intermediates/spatch_all_metrics_full/` and main plots |
| Fig3E/F and sFig10/sFig11 ontology panels | Target-matched manuscript-frozen ontology tables; online resources can drift | `ontology_target_0608` tables and manifests |
| Fig4 hotspot and LIANA analyses | Dense hotspot route, permutation controls, and LIANA environment are too heavy | `Fig4A-F` entries in `manifest/panel_manifest.tsv` |
| Fig5A-G paired P5 NAT/CRC analysis | Requires two full Visium HD sections and paired scale-gain workflow | `visiumhd_p5_scale_gain_manifest.tsv` and Fig5 plots |
| sFig17-sFig19 cross-slide validation | Target-matched multislide route and saved CellTypist context inputs | `sFig17_19_multislide_intermediate_audit.tsv` and related manifests |

## Acceptance Criteria

- The notebook runs top-to-bottom with `N_JOBS=2`.
- The compact `.h5ad` checksum matches the manifest.
- Segment counts are positive and decrease at coarser scales.
- Moran rank and score tables are non-empty.
- The notebook reports best-scale counts and representative genes.
- Native versus SPIX-averaged expression maps render for multiple genes.
- The final JSON report records runtime, dataset shape, segment counts, and
  manuscript reference scope.

## Boundary

Use this wording if asked what the notebook proves:

> The Colab notebook reproduces the core SPIX multiscale analysis mechanics on a
> public Visium HD ROI, while the full manuscript panels are reproduced in the
> verified local package from full raw or target-route inputs.
