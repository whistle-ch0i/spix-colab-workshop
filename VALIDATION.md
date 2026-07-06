# Validation

Validation date: 2026-07-06

Environment:

- Conda env: `SPIX_0426`
- CPU cap: `SPIX_WORKSHOP_N_JOBS=2`
- Thread env: `OMP_NUM_THREADS=2`, `OPENBLAS_NUM_THREADS=2`,
  `MKL_NUM_THREADS=2`, `NUMEXPR_NUM_THREADS=2`
- Notebook executor: `scripts/execute_notebook_code_cells.py`

## Current Practical Defaults

The current workshop default is one practical notebook:

`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Lecture section order:

1. SVG
2. spatial clustering
3. cell-cell interaction
4. SPIX

Default dataset:

`data/visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad`

Dataset details:

- Native Visium HD 2 um ROI from full P2 intermediate.
- Full source shape: `8731400 x 18085`.
- Workshop shape: `1000000 x 2515`.
- File size: 87.29 MiB.
- SHA-256:
  `abf1f7848397869a1abd7b329d0dd86c9aea80bf87c71e93d727585a4c41802f`

Local fallback executor result, 2026-07-06:

- Code cells: 37/37 passed.
- Colab safe mode was forced for this validation:
  `SPIX_WORKSHOP_COLAB_SAFE_MODE=1`.
- Total elapsed in Colab safe mode: 195.32 seconds after local dependencies and
  data were present.
- Final process peak RSS in local safe-mode validation: 3.26 GB.
- Notebook structure: the practical notebook is split into short, stepwise code
  cells for workshop use. Repeated file/checksum/timing/plotting chores live in
  `notebooks/workshop_helpers.py`. Colab setup chores live in
  `notebooks/colab_bootstrap.py`, and Python package versions are pinned in
  `requirements-colab.txt`. The notebook cells still call Scanpy, Squidpy,
  BANKSY, BayesSpace, SpaGCN, and SPIX directly.
- Pinned package check in the validation run:
  `scanpy 1.11.5`, `squidpy 1.6.5`, `SpaGCN 1.2.7`,
  `pybanksy 1.3.5`, `anndata 0.11.4`, `zarr 2.18.3`,
  `numcodecs 0.13.1`.
- ROI context plot input:
  `data/visiumhd_p2_roi_context_1000000_downsample.csv`
  - downsample points: 120,000 full-P2 coordinates
  - ROI context SHA-256:
    `5b429739f7901cfa92b45afbaf7d6b4b191beafd547829d5f8fa5c7042e0e5a4`
- Standard sections:
  - 8 um pseudobulk shape: `62898 x 2515`
  - spatial domain comparison panel: `3500 x 2515`
- SVG:
  - Squidpy Moran's I over all 2,515 workshop genes on 8 um pseudobulk.
  - Top 100 HVG/SVG overlap: 3 genes.
  - Example top SVG genes: `PIGR`, `OLFM4`, `FCGBP`, `COL1A1`, `COL3A1`.
- Spatial domain:
  - expression-only Leiden baseline,
  - Squidpy spatial graph clustering,
  - BANKSY through `pyBANKSY`, using 800 HVGs,
  - BayesSpace through live R BayesSpace when available, otherwise bundled
    labels for the fixed 3,500-bin domain panel,
  - SpaGCN.
  - BayesSpace live R input is checked for zero-count bins; if the selected
    subset is unsafe, the notebook falls back to the full workshop gene set
    before calling R BayesSpace.
  - Bundled BayesSpace label file:
    `data/bayesspace_labels_1m_panel3500.csv`
  - Bundled-label validation ARI:
    expression vs Squidpy spatial graph 0.067, expression vs BANKSY 0.386,
    expression vs BayesSpace 0.633, expression vs SpaGCN 0.703,
    Squidpy spatial graph vs BANKSY 0.118, Squidpy spatial graph vs
    BayesSpace 0.072, Squidpy spatial graph vs SpaGCN 0.076,
    BANKSY vs BayesSpace 0.310, BANKSY vs SpaGCN 0.448,
    BayesSpace vs SpaGCN 0.594.
- Cell-cell interaction:
  - Squidpy neighborhood enrichment on BANKSY domains, 50 permutations.
  - Squidpy `ligrec`, 11 ligand-receptor candidates, 20 permutations,
    `threshold=0.0`.
  - Top CCI examples include `MIF-CD74`, `CD74-MIF`, and `LGALS3-ITGB1`.
- SPIX section: VisiumHD P2 manuscript/reproduction path. The full
  `1000000 x 2515` 2 um ROI remains the reference setting. In default Colab
  safe mode, SPIX uses a central `500000 x 2515` native 2 um subset after
  standard-analysis objects are cleared from memory:
  - PCA/log-normalized embedding with 30 dimensions and up to 2,000 features.
  - graph smoothing before equalization.
  - smoothing sweep enabled by default; selected `graph_k=15`, `graph_t=10`.
  - equalization sweep enabled by default; selected `BalanceSimplest`,
    `sleft=0.5`, `sright=0.5`.
  - `image_plot_slic` multiscale segmentation at
    `2,8,16,30,40,50,80,100,150,200,250,300,350,400,450,500` um.
  - compactness auto-selection through candidate sweep in
    `precompute_multiscale_segments`.
  - multiscale Moran/SVG ranking with SPIX segment labels.
- SPIX segment counts:
  - `r2`: 500000 native 2 um bins
  - `r8`: 33257
  - `r16`: 8283
  - `r30`: 2343
  - `r40`: 1185
  - `r50`: 777
  - `r80`: 303
  - `r100`: 197
  - `r150`: 89
  - `r200`: 49
  - `r250`: 28
  - `r300`: 21
  - `r350`: 18
  - `r400`: 12
  - `r450`: 12
  - `r500`: 5
- Slowest stages:
  - 8 um preprocessing with Scanpy/Squidpy: 41.85 seconds
  - SPIX multiscale segmentation: 37.68 seconds
  - SPIX equalization sweep: 28.62 seconds
  - import analysis packages: 20.39 seconds
  - SPIX smoothing sweep: 19.48 seconds
  - SPIX multiscale Moran/SVG: 11.37 seconds
  - BayesSpace bundled label loading: 0.01 seconds

Pip-installed SPIX plus Colab-path stub result, 2026-07-06:

- Code cells: 13/13 passed.
- Total elapsed: 29.97 seconds after dependencies were present.
- SPIX import path:
  `/tmp/spix_colab_like_env/lib/python3.10/site-packages/SPIX/__init__.py`

## Full P2 8M-Bin Probe

Probe script:

`scripts/probe_visiumhd_full_p2_limits.py`

The script defaults now match the VisiumHD P2 manuscript-style SPIX path used
by the workshop notebook: 30-dimensional embedding, graph smoothing,
equalization, 16 physical scales, and multiscale Moran/SVG. The historical
full-P2 timings below were collected as a lower-dimensional memory-boundary
probe before that default was updated, so treat them as feasibility evidence
rather than current manuscript-style full-P2 runtime.

Full P2 source:

`8731400 x 18085`, 7.66 GB h5ad.

Colab-free memory simulation, 2026-07-06:

- Memory cap: 12 GiB virtual memory, matching the observed free Colab runtime
  order of magnitude.
- `read_h5ad` full in-memory path:
  - failed with `MemoryError` after 147.93 seconds.
  - failure occurred while reading `/uns/tiles/barcode`, before SPIX analysis.
- `8M x 2515` selected-gene materialization from backed AnnData:
  - failed during `materialize_selected_adata` after 18.24 seconds.
  - error: unable to allocate 956 MiB for the full CSR `indices` array.
- Interpretation: the full P2 object is not suitable as the default free-tier
  Colab hands-on input. The bottleneck is memory, not CPU.

High-memory local server probe, `N_JOBS=2`, 2026-07-06:

- Data path: full 8,731,400 bins, reduced to the 2,515 workshop genes.
- Materialization: 115.25 seconds, peak RSS 10.93 GB.
- SPIX embedding: 116.72 seconds, peak RSS 13.60 GB.
- Equalization: 60.88 seconds.
- Image cache: 86.15 seconds, 3369 x 3369 x 16 memmap image,
  about 692.8 MB raw.
- Multiscale segmentation: 393.84 seconds, peak RSS 16.41 GB.
- Segment counts:
  - `r48`: 15351 observed units
  - `r96`: 3856 observed units
  - `r192`: 969 observed units
  - `r384`: 250 observed units
- Multiscale Moran/SVG on the same full-P2 selected-gene object:
  - 281.45 seconds, peak RSS 16.62 GB.
- Interpretation: the optimized full-8M selected-gene path works on a
  high-memory local server, but it exceeds a safe free-tier Colab memory budget.

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
