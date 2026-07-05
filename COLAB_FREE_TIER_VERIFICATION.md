# Colab Free-Tier Check

Use this after the repo is pushed and the notebook URL is live.

Official Colab FAQ checked on 2026-07-05:
<https://research.google.com/colaboratory/faq.html>

## Preflight

1. Push the workshop folder and data file to the branch used by the notebook.
2. Confirm the notebook data URL resolves:
   `https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad`
3. Confirm the SPIX install URL in the notebook points to a branch containing
   the required SPIX APIs.

## Free-Tier Condition

Use a Google account without active Colab Pro, Pro+, Pay As You Go compute
units, or enterprise allocation.

## Run

1. Open one of the notebooks in Colab:
   - `notebooks/SPIX_VisiumHD_multiscale_colab.ipynb`
   - `notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`
2. Select `Runtime > Disconnect and delete runtime`.
3. Select `Runtime > Change runtime type > Hardware accelerator: None`.
4. Run all cells from the top.
5. The final cell must print `Validation passed` and write a JSON timing
   report. The Choi Whisoo notebook auto-downloads
   `choi_whisoo_colab_timing_report.json` when running in Colab.

## Pass Criteria

- `running_in_colab` is `true` in the first-cell runtime snapshot.
- Notebook runs on CPU runtime with no GPU requirement.
- Data SHA-256 check passes.
- All Choi Whisoo notebook stages complete:
  - SPIX embedding/equalization/cache,
  - multiscale SPIX segmentation,
  - spatial clustering,
  - multiscale SVG Moran ranking,
  - marker-derived cell-state scoring,
  - segment-level spatial LR scoring.
- Final segment counts and rank-table shapes are non-empty.
- Total elapsed runtime is acceptable for the workshop slot.

## Current Default Preflight Result

Observed locally on 2026-07-06 with the Choi Whisoo notebook and pip-installed
SPIX, using a Colab-path stub:

- Data:
  - shape: `500000 x 2515`
  - file size: 42.89 MB
  - SHA-256:
    `ddc3a4eb3ee5b64dae210a6c8cf5820fbbfff784cabbebdf671100c266e8a586`
- Result:
  - `validation_passed`: true
  - total elapsed after dependencies were installed: 29.97 seconds
- Output checks:
  - segment counts: `r48` 900, `r96` 220, `r192` 52, `r384` 12
  - spatial LR radius: 160 um, converted to 80 coordinate units
  - top LR examples include `MIF-CD74`, `CD74-MIF`, and
    `COL1A1-ITGB1`

This validates the current notebook/data path before a live Colab run. Collect
a new downloaded timing report from real Colab after this change is pushed.

## Earlier Observed Colab CPU Result

Timing report received on 2026-07-06 from
the earlier 16 um version of
`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`.

- Runtime:
  - `runtime.running_in_colab`: true
  - Python: `3.12.13`
  - CPU count: 2
  - memory total: 12.67 GB
  - disk free: 87.28 GB
  - hardware accelerator: not required
- Data:
  - shape: `10000 x 2515`
  - SHA-256:
    `5157b0dabb979ef3fdad6110fe447eec8336f2906e3607eb48d8fffcbfe0e585`
- Result:
  - `validation_passed`: true
  - total elapsed: 126.45 seconds
  - install/import: 80.79 seconds
  - analysis after install/import: 45.66 seconds
- Main stage timings:
  - SPIX embedding/image cache: 29.75 seconds
  - SPIX multiscale segmentation: 1.67 seconds
  - spatial clustering: 0.61 seconds
  - multiscale SVG Moran: 4.49 seconds
  - segment-level spatial LR scoring: 3.89 seconds
- Output checks:
  - segment counts: `r48` 1138, `r96` 285, `r192` 68, `r384` 21
  - SVG rank table: `2515 x 4`
  - SVG score table: `2515 x 4`
  - top LR examples include `MIF-CD74`, `CD74-MIF`, and
    `COL1A1-ITGB1`

This remains useful evidence that the notebook structure can complete on a
small Colab CPU runtime. Because the current default dataset is now the larger
2 um ROI, collect a fresh real-Colab timing report before using this as the
current workshop timing.

## Local Baseline

The local low-resource smoke run with `N_JOBS=2` completed all 14 code cells
using the marker-diverse `10000 x 2515` dataset. It produced:

- `r48`: 1138 observed units
- `r96`: 285 observed units
- `r192`: 68 observed units
- `r384`: 21 observed units
- rank table: `2515 x 4`
- score table: `2515 x 4`
- best-scale counts: `r48` 318, `r96` 835, `r192` 669, `r384` 693 genes
- expression-map representative genes: `PIGR`, `OLFM4`, `COL1A1`, `THBS2`,
  `COL1A2`, `COL12A1`
- elapsed runtime after dependencies and local data were already present:
  21.42 seconds

The Colab number can differ. A fresh runtime has to install packages and
download the data.
