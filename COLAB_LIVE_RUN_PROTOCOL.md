# Direct Colab Free-Tier Run Protocol

This is the protocol for validating the Choi Whisoo SPIX workshop notebook on a
real Google Colab free-tier runtime.

## Notebook

`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Recommended Colab URL after this folder is pushed to a branch:

`https://colab.research.google.com/github/whistle-ch0i/spix-colab-workshop/blob/main/notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

The notebook data URL must point to the same branch:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad`

## What I Can Do

- Prepare the notebook and data.
- Make a clean GitHub repository containing only the workshop files.
- Provide the exact Colab URL.
- Read the downloaded timing report and decide whether free-tier validation
  passed.
- If it fails or is slow, tune the notebook and repeat.

## What Requires User Help

Google Colab execution requires an interactive Google account session. The user
must:

1. Open the Colab URL with a Google account that does not have active Colab Pro,
   Pro+, Pay As You Go compute units, or enterprise allocation.
2. Select `Runtime > Disconnect and delete runtime`.
3. Select `Runtime > Change runtime type > Hardware accelerator: None`.
4. Run all cells.
5. Upload or paste the downloaded `choi_whisoo_colab_timing_report.json`.

Do not use SSH, remote desktop, or notebook-UI bypass methods for this check.

## Pass Criteria

- `runtime.running_in_colab` is `true`.
- `runtime.thread_cap` is `2`.
- `validation_passed` is `true`.
- All four sections complete:
  - SPIX multiscale segmentation,
  - spatial clustering,
  - multiscale SVG,
  - segment-level spatial LR scoring.
- The final report contains stage timings.
- Total time is acceptable for the workshop slot.

## Local Baseline

Local low-resource execution on 2026-07-05:

- Code cells: 13/13 passed.
- Dataset: `10000 x 2515`.
- Total elapsed: 28.04 seconds after local dependencies and data were available.
- Slowest stages:
  - CCI segment-level scoring: 8.05 seconds.
  - multiscale SVG Moran: 7.40 seconds.
  - SPIX embedding/image cache: 6.40 seconds.
- Segment counts:
  - `r48`: 1138
  - `r96`: 285
  - `r192`: 68
  - `r384`: 21

Colab will be slower because it must install SPIX and download data unless the
runtime already has them cached.
