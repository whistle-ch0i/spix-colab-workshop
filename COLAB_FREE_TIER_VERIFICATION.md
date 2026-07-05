# Colab Free-Tier Verification Checklist

This file records the actual Google Colab validation protocol. Local smoke tests
are useful, but they do not prove free-tier Colab success because Google allocates
Colab runtimes only after an interactive Google account session.

Official Colab FAQ checked on 2026-07-05:
<https://research.google.com/colaboratory/faq.html>

## Preflight

1. Push the workshop folder and data file to the branch used by the notebook.
2. Confirm the notebook data URL resolves:
   `https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad`
3. Confirm the SPIX install URL in the notebook points to a branch containing
   the required SPIX APIs.

## Manual Free-Tier Condition

Use a Google account without active Colab Pro, Pro+, Pay As You Go compute units,
or other paid/enterprise runtime allocation. Colab does not expose a reliable
programmatic flag for account tier inside the notebook, so this must be checked
manually in the Colab UI/account state.

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
- All SPIX stages complete:
  - embedding/equalization/cache,
  - `precompute_multiscale_segments`,
  - `multiscale_moran_ranks`,
  - best-scale summary,
  - native and SPIX-averaged expression maps,
  - expression-versus-organization summary.
- Final segment counts and rank-table shapes are non-empty.
- Total elapsed runtime is acceptable for the workshop slot.

## Expected Local Baseline

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

Actual Colab runtime may differ because Google states that free Colab resources
are not guaranteed and limits can fluctuate.
