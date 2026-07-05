# Validation

Validation date: 2026-07-06

Environment:

- Conda env: `SPIX_0426`
- CPU cap: `SPIX_WORKSHOP_N_JOBS=2`
- Thread env: `OMP_NUM_THREADS=2`, `OPENBLAS_NUM_THREADS=2`,
  `MKL_NUM_THREADS=2`, `NUMEXPR_NUM_THREADS=2`
- Notebook executor: `scripts/execute_notebook_code_cells.py`

## Current Choi Whisoo Default

Notebook:

`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Default dataset:

`data/visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad`

Dataset details:

- Native Visium HD 2 um ROI from full P2 intermediate.
- Full source shape: `8731400 x 18085`.
- Workshop shape: `500000 x 2515`.
- File size: 42.89 MB.
- SHA-256:
  `ddc3a4eb3ee5b64dae210a6c8cf5820fbbfff784cabbebdf671100c266e8a586`

Local fallback executor result, 2026-07-06:

- Code cells: 13/13 passed.
- Total elapsed: 36.56 seconds after local dependencies and data were present.
- Segment counts: `r48` 900, `r96` 220, `r192` 52, `r384` 12.
- Spatial clustering scale: `r96`.
- SVG rank/score tables: `2515 x 4`.
- Cell-state bins: ambiguous 319782, stromal 85419, secretory 45082,
  epithelial 29516, immune 18274, proliferation 1927.
- CCI: `r48` segment-level scoring, 160 um physical radius,
  80 coordinate-unit radius for 2 um bins, 29172 directed non-ambiguous
  segment-neighbor edges.
- Slowest stages:
  - multiscale SVG Moran: 10.12 seconds
  - SPIX multiscale segmentation: 9.41 seconds
  - SPIX embedding/image cache: 9.20 seconds

Pip-installed SPIX plus Colab-path stub result, 2026-07-06:

- Code cells: 13/13 passed.
- Total elapsed: 29.97 seconds after dependencies were present.
- SPIX import path:
  `/tmp/spix_colab_like_env/lib/python3.10/site-packages/SPIX/__init__.py`

The previous 16 um `10000 x 2515` validation is retained below as a legacy
smoke baseline and as the broader mini-reproduction notebook input.

## Legacy 16 um Mini-Reproduction Notebook

Command:

```bash
CONDA_NO_PLUGINS=true \
SPIX_WORKSHOP_N_JOBS=2 \
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 \
NUMBA_CACHE_DIR=/tmp/numba_spix_workshop_nb MPLCONFIGDIR=/tmp/mpl_spix_workshop_nb \
conda run --no-capture-output -n SPIX_0426 \
python scripts/execute_notebook_code_cells.py \
  notebooks/SPIX_VisiumHD_multiscale_colab.ipynb \
  --workdir .
```

Result:

- Data loaded: `10000 x 2515`
- ROI selection: `marker_diverse`
- Marker-group log fractions:
  - epithelial/tumor: 0.197
  - intestinal/secretory: 0.211
  - immune/inflammatory: 0.222
  - stromal/matrix: 0.228
  - proliferation: 0.142
- SPIX segment counts:
  - `r48`: 1138 observed units
  - `r96`: 285 observed units
  - `r192`: 68 observed units
  - `r384`: 21 observed units
- Moran rank table: `2515 x 4`
- Moran score table: `2515 x 4`
- Best-scale gene counts:
  - `r48`: 318 genes
  - `r96`: 835 genes
  - `r192`: 669 genes
  - `r384`: 693 genes
- Representative expression-map genes:
  - `PIGR`, `OLFM4`, `COL1A1`, `THBS2`, `COL1A2`, `COL12A1`
- Top expression/organization examples:
  - `COL1A1`: best scale `r96`, peak Moran's I `0.894946`
  - `PIGR`: best scale `r48`, peak Moran's I `0.882549`
  - `THBS2`: best scale `r96`, peak Moran's I `0.873673`
- Runtime elapsed in fallback executor: 21.42 seconds after dependencies were
  already installed and local data were present.
- All 14 notebook code cells executed successfully.

Standard `jupyter nbconvert --execute` was not available in this local
environment because `nbconvert`, `nbclient`, and `nbformat` are not installed.
The fallback executor runs the notebook code cells in order and is sufficient
for runtime smoke validation, but a final release pass can still use
`nbconvert` in a fuller notebook environment.

## Legacy Choi Whisoo 16 um Notebook

Notebook:

`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Command:

```bash
CONDA_NO_PLUGINS=true \
SPIX_WORKSHOP_N_JOBS=2 \
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 \
NUMBA_CACHE_DIR=/tmp/numba_spix_choi_nb MPLCONFIGDIR=/tmp/mpl_spix_choi_nb \
conda run --no-capture-output -n SPIX_0426 \
python scripts/execute_notebook_code_cells.py \
  notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb \
  --workdir .
```

Result:

- All 13 code cells executed successfully.
- Total elapsed: 28.60 seconds after local dependencies and data were present.
- Dataset: `10000 x 2515`.
- SPIX segment counts:
  - `r48`: 1138 observed units
  - `r96`: 285 observed units
  - `r192`: 68 observed units
  - `r384`: 21 observed units
- Spatial clustering:
  - `r96` SPIX units clustered into 6 domains.
- SVG:
  - rank table: `2515 x 4`
  - score table: `2515 x 4`
- Cell-state labels:
  - stromal: 2649 bins
  - immune: 1866 bins
  - ambiguous: 1691 bins
  - epithelial: 1539 bins
  - secretory: 1299 bins
  - proliferation: 956 bins
- CCI, legacy pre-radius-unit-fix result:
  - mode: `r48` SPIX segment-level spatial LR scoring
  - radius setting: 160
  - directed segment-neighbor edges after removing ambiguous states: 1,280,292
  - LR pairs used: 12
- Slowest stages:
  - multiscale SVG Moran: 7.95 seconds
  - CCI segment-level scoring: 6.89 seconds
  - SPIX embedding/image cache: 6.79 seconds

Observed legacy Colab CPU run, 2026-07-06:

- Runtime snapshot:
  - `runtime.running_in_colab`: true
  - Python: `3.12.13`
  - CPU count: 2
  - memory total: 12.67 GB
  - disk free: 87.28 GB
  - working directory: `/content`
- Result:
  - `validation_passed`: true
  - dataset SHA-256:
    `5157b0dabb979ef3fdad6110fe447eec8336f2906e3607eb48d8fffcbfe0e585`
  - dataset shape: `10000 x 2515`
  - total elapsed: 126.45 seconds
  - install/import stage: 80.79 seconds
  - analysis after install/import: 45.66 seconds
- Stage times:
  - SPIX embedding/image cache: 29.75 seconds
  - SPIX multiscale segmentation: 1.67 seconds
  - spatial clustering: 0.61 seconds
  - multiscale SVG Moran: 4.49 seconds
  - cell-state scoring: 0.82 seconds
  - segment-level spatial LR scoring: 3.89 seconds
- Output checks:
  - segment counts: `r48` 1138, `r96` 285, `r192` 68, `r384` 21
  - SVG rank table: `2515 x 4`
  - SVG score table: `2515 x 4`
  - cell-state bins: stromal 2649, immune 1866, ambiguous 1691,
    epithelial 1539, secretory 1299, proliferation 956
  - top LR examples include `MIF-CD74`, `CD74-MIF`, `COL1A1-ITGB1`,
    `COL1A2-ITGB1`, and `FN1-ITGAV`
