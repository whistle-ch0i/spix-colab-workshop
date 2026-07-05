# SPIX Colab Workshop

Colab-ready SPIX materials for a short hands-on session. The main live notebook
uses a native-resolution 2 um ROI from the public 10x Genomics Visium HD Human
Colon Cancer dataset, so participants see data closer to the manuscript setting
without waiting on the full 8.7M-bin slide.

The main workshop thread is:

- build SPIX multiscale units,
- cluster SPIX units into spatial domains,
- rank scale-response SVGs,
- score a small spatial ligand-receptor panel,
- save a timing report for Colab validation.

Start here:

`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

A second notebook keeps the broader manuscript mini-reproduction flow:

`notebooks/SPIX_VisiumHD_multiscale_colab.ipynb`

For the panel-by-panel boundary between live Colab execution and reference-only
full reproduction, see `MANUSCRIPT_CORE_RESULTS_MAP.md`.

For the free-tier check, use `COLAB_LIVE_RUN_PROTOCOL.md`.

## Dataset

Source dataset:

<https://www.10xgenomics.com/datasets/visium-hd-cytassist-11mm-human-colon-cancer-HE>

The source page lists this as a Visium HD Spatial Gene Expression Human Colon
Cancer dataset analyzed with Space Ranger 4.1.0 and released under CC BY 4.0.

The default Choi Whisoo workshop file is a derived 2 um subset:

`data/visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad`

It is a spatially contiguous native-resolution ROI with 500,000 bins and the
same marker-diverse workshop gene set. The full 2 um P2 source has
`8731400 x 18085` observations/features and is intentionally not used for the
live exercise.

The smaller 16 um file remains in `data/` for quick smoke tests and for the
broader mini-reproduction notebook:

`data/visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad`

## Rebuild The Data Files

Only needed if you want to recreate the bundled `.h5ad` files.

The default 2 um Choi notebook file is recreated from a full P2 AnnData
intermediate:

```bash
CONDA_NO_PLUGINS=true \
NUMBA_CACHE_DIR=/tmp/numba_spix_workshop_build MPLCONFIGDIR=/tmp/mpl_spix_workshop_build \
conda run --no-capture-output -n SPIX_0426 \
python scripts/build_visiumhd_2um_roi_from_full_h5ad.py \
  --max-obs 500000 \
  --output data/visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad
```

The legacy 16 um smoke-test file is recreated from Space Ranger outputs:

```bash
CONDA_NO_PLUGINS=true \
OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 \
NUMBA_CACHE_DIR=/tmp/numba_spix_workshop_build MPLCONFIGDIR=/tmp/mpl_spix_workshop_build \
conda run --no-capture-output -n SPIX_0426 \
python scripts/build_visiumhd_colon_roi_h5ad.py \
  --input-bin-dir /path/to/SpaceRanger/binned_outputs/square_016um \
  --output data/visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad \
  --max-obs 10000 \
  --max-genes 2500 \
  --bin-size-um 16 \
  --seed 7 \
  --selection-mode marker_diverse \
  --candidate-count 512
```

## Regenerate Notebooks

Regenerate after changing the data file or default URLs:

```bash
python3 scripts/write_choi_whisoo_colab_notebook.py \
  --output notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb \
  --data-file data/visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad
```

## Local Check

Run this before a workshop if you changed the notebooks:

```bash
CONDA_NO_PLUGINS=true \
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 \
NUMBA_CACHE_DIR=/tmp/numba_spix_workshop_nb MPLCONFIGDIR=/tmp/mpl_spix_workshop_nb \
conda run --no-capture-output -n SPIX_0426 \
jupyter nbconvert --execute --to notebook --inplace \
  notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb
```

If `nbconvert`, `nbclient`, or `nbformat` are not installed:

```bash
CONDA_NO_PLUGINS=true \
SPIX_WORKSHOP_N_JOBS=2 \
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 \
NUMBA_CACHE_DIR=/tmp/numba_spix_workshop_nb MPLCONFIGDIR=/tmp/mpl_spix_workshop_nb \
conda run --no-capture-output -n SPIX_0426 \
python scripts/execute_notebook_code_cells.py \
  notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb \
  --workdir .
```

Current numbers are in `VALIDATION.md`.

## Publish For Colab

The notebooks expect this raw data URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad`

Before a live run, make sure the data file exists at that URL. If not, set
`SPIX_WORKSHOP_DATA_URL` in the first notebook cell.

## Colab Notes

- Use CPU runtime: `Runtime > Change runtime type > Hardware accelerator: None`.
- The notebook defaults to `N_JOBS=2`.
- Keep participant edits focused on `RESOLUTIONS_UM`, `N_JOBS`, CCI radius,
  and gene lists.
- If Colab is slow or disconnects, restart the runtime and run cells from the top.
