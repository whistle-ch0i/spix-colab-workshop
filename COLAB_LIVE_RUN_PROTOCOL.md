# Colab Free-Tier Run

Use this checklist for the live free-tier run.

## Open

Main Korean workshop notebook:

`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Colab URL:

`https://colab.research.google.com/github/whistle-ch0i/spix-colab-workshop/blob/main/notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Data URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad`

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
- The notebook completes the SVG, spatial clustering, cell-cell interaction,
  and SPIX sections.
- The final report contains stage timings.
- The SPIX section reports the VisiumHD P2-style path:
  30-dimensional embedding, graph smoothing before equalization,
  `image_plot_slic` multiscale segmentation, and multiscale Moran/SVG.
- Total time is acceptable for the workshop slot.

## Current Default Local Check

Observed locally on 2026-07-06 with the Korean combined notebook:

- Dataset: native 2 um ROI, `500000 x 2515`, 42.89 MB.
- Validation: top-to-bottom notebook pass with `N_JOBS=2`.
- Local elapsed time after dependencies and data were present: 128.32 seconds.
- Standard-tool teaching subset: `47039 x 2515`.
- Scanpy Leiden clusters: 13 at `n_neighbors=30`, `resolution=0.01`.
- Squidpy Moran top examples: `OLFM4`, `PIGR`, `REG1A`, `MUC2`, `TAGLN`.
- Squidpy `ligrec`: 11 LR candidates, 20 permutations.
- SPIX: manuscript-style 30-dimensional embedding, graph smoothing,
  equalization, `image_plot_slic` segmentation, and multiscale Moran/SVG.
- SPIX segment counts:
  `r2` 500000, `r8` 32146, `r16` 8012, `r30` 2272, `r40` 1277,
  `r50` 806, `r80` 312, `r100` 200, `r150` 89, `r200` 51,
  `r250` 29, `r300` 21, `r350` 19, `r400` 12, `r450` 12, `r500` 5.

This is the current preflight baseline. Run the notebook once in real Colab
after pushing any data/notebook changes and keep the downloaded timing report.

## Earlier Passing Colab CPU Run

Observed on 2026-07-06 with the earlier 16 um Choi Whisoo notebook:

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
