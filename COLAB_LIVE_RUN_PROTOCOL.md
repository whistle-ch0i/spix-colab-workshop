# Colab Free-Tier Run

Use this checklist for the live free-tier run.

## Open

Main practical notebook:

`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Colab URL:

`https://colab.research.google.com/github/whistle-ch0i/spix-colab-workshop/blob/main/notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Data URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad`

ROI context URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_p2_roi_context_downsample.csv`

## Run

1. Open the Colab URL with a free-tier Google account.
2. Select `Runtime > Disconnect and delete runtime`.
3. Select `Runtime > Change runtime type > Hardware accelerator: None`.
4. Run all cells.
5. Keep the downloaded timing report JSON.

For a clean free-tier check, do not use Pro, Pro+, Pay As You Go compute units,
or an enterprise runtime.

## Pass Criteria

- `runtime.running_in_colab` is `true`.
- `runtime.thread_cap` is `2`.
- `validation_passed` is `true`.
- The notebook completes the SVG, spatial domain, cell-cell interaction,
  and SPIX sections.
- The final report contains stage timings.
- The standard sections use the 8 um pseudobulk object made from the 2 um ROI.
- The spatial domain section includes expression-only baseline, Squidpy spatial
  graph, BANKSY through `pyBANKSY`, and SpaGCN.
- The CCI section includes spatial neighborhood enrichment and Squidpy `ligrec`.
- The SPIX section reports the VisiumHD P2-style path:
  30-dimensional embedding, graph smoothing before equalization,
  `image_plot_slic` multiscale segmentation, and multiscale Moran/SVG.
- The default SPIX run uses automatic smoothing/equalization parameter sweeps.
- Total time is acceptable for the workshop slot.

## Current Default Local Check

Observed locally on 2026-07-06 with the combined practical notebook:

- Dataset: native 2 um ROI, `500000 x 2515`, 42.89 MB.
- 8 um pseudobulk: `31535 x 2515`.
- Spatial domain comparison panel: `3500 x 2515`.
- ROI context SHA-256:
  `6eddea31f94576514f5234edd849811d96711cbaabbdc594a44692071729bfbb`.
- Validation: top-to-bottom notebook pass with `N_JOBS=2`.
- Code cells: 30/30 passed.
- Local elapsed time after dependencies and data were present: 203.87 seconds.
- Squidpy Moran top examples: `PIGR`, `OLFM4`, `FCGBP`, `COL1A1`, `JCHAIN`.
- Top 100 HVG/SVG overlap: 3 genes.
- Spatial domain methods: expression-only baseline, Squidpy spatial graph,
  BANKSY through `pyBANKSY`, and SpaGCN.
- CCI: neighborhood enrichment plus Squidpy `ligrec` with 11 LR candidates and
  20 permutations.
- SPIX: manuscript-style 30-dimensional embedding, graph smoothing,
  equalization, `image_plot_slic` segmentation, and multiscale Moran/SVG.
- Automatic SPIX smoothing recommendation: `graph_k=5`, `graph_t=30`.
- Automatic SPIX equalization recommendation: `BalanceSimplest`, `sleft=0.5`,
  `sright=0.5`.
- SPIX segment counts:
  `r2` 500000, `r8` 32138, `r16` 8001, `r30` 2260, `r40` 1274,
  `r50` 804, `r80` 309, `r100` 198, `r150` 87, `r200` 47,
  `r250` 28, `r300` 21, `r350` 19, `r400` 12, `r450` 12, `r500` 5.
- Slowest local stages: 8 um preprocessing 37.43 sec, SPIX multiscale
  segmentation 40.08 sec, equalization sweep 30.76 sec, smoothing sweep
  24.76 sec, SPIX multiscale Moran/SVG 12.17 sec.

This is the current preflight baseline. Run the notebook once in real Colab
after pushing any data/notebook changes and keep the downloaded timing report.

## Earlier Passing Colab CPU Run

Observed on 2026-07-06 with the earlier 16 um practical notebook:

- Runtime: Colab CPU session, Python `3.12.13`, 2 CPUs, 12.67 GB RAM.
- Dataset: `10000 x 2515`.
- Validation: passed.
- Total elapsed: 126.45 seconds.
- One-time install/import: 80.79 seconds.
- Analysis after install/import: 45.66 seconds.
- Slowest analysis stage: SPIX embedding/image cache, 29.75 seconds.
- Multiscale SVG Moran: 4.49 seconds.
- Segment-level spatial LR scoring: 3.89 seconds.

For planning the current 500k 2 um notebook, budget about 4-5 minutes for a
fresh Colab runtime until a new real Colab timing report is collected.

## Local Baseline

Legacy local low-resource run on 2026-07-05:

- Code cells: 13/13 passed.
- Dataset: `10000 x 2515`.
- Total elapsed: 28.60 seconds after local dependencies and data were available.
- Slowest stages:
  - multiscale SVG Moran: 7.95 seconds.
  - CCI segment-level scoring: 6.89 seconds.
  - SPIX embedding/image cache: 6.79 seconds.
- Segment counts:
  - `r48`: 1138
  - `r96`: 285
  - `r192`: 68
  - `r384`: 21

Colab will usually be slower because it has to install packages and download the
data on a fresh runtime.
