# KOGO Spatial Transcriptomics Practice

Materials for the spatial transcriptomics practical session in the 2026 KOGO
statistical genetics workshop. The live Colab file uses a bounded 2 um ROI from
the public 10x Genomics Visium HD Human Colon Cancer P2 dataset. The notebook
shows where the ROI sits in the full section, runs standard spatial workflows on
8 um pseudobulk, and then runs SPIX on the native 2 um ROI.

Main practical notebook:

`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Session flow:

- ROI overview: full P2 downsample plus selected ROI box
- 8 um pseudobulk from native 2 um bins
- SVG: HVG versus Squidpy Moran's I
- spatial domain comparison: expression-only baseline, Squidpy spatial graph,
  BANKSY through `pyBANKSY`, BayesSpace, and SpaGCN
- cell-cell interaction: spatial neighborhood enrichment plus Squidpy `ligrec`
- SPIX: VisiumHD P2-style embedding, automatic graph smoothing selection,
  automatic equalization selection, `image_plot_slic` multiscale segmentation,
  and multiscale Moran/SVG

The notebook code is intentionally split into short stepwise cells for a
hands-on class. Most cells can be run from top to bottom without editing.
Small repeated tasks such as file lookup, checksum checks, stage timing, and
simple plotting live in `notebooks/workshop_helpers.py`; the analysis calls
still use the original Scanpy, Squidpy, BANKSY, BayesSpace, SpaGCN, and SPIX
APIs in the notebook.

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

The default practical file is a derived 2 um ROI:

`data/visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad`

It is a spatially contiguous native-resolution ROI with 1,000,000 bins and the
same marker-diverse workshop gene set. The full 2 um P2 source has
`8731400 x 18085` observations/features and is intentionally not used for the
live exercise.

The notebook builds a `62898 x 2515` 8 um pseudobulk object from this ROI for
SVG, spatial domain, and CCI sections. The spatial domain comparison uses a
central 3,500-bin 8 um panel so BANKSY, BayesSpace, and SpaGCN stay comfortable
on a free CPU runtime. In Colab safe mode, the final SPIX section uses a
central 500,000-bin native 2 um subset to avoid silent free-tier runtime exits.
Set `SPIX_WORKSHOP_SPIX_MAX_2UM_BINS=1000000` for the 1M reference run.

The ROI overview plot uses:

`data/visiumhd_p2_roi_context_1000000_downsample.csv`

The full P2 object was explicitly probed on 2026-07-06. Under a 12 GiB
free-tier-style memory cap, the full in-memory read failed before SPIX analysis,
and even the `8M x 2515` selected-gene backed materialization failed. On a
high-memory local server, the optimized `8M x 2515` SPIX segmentation plus
multiscale Moran path completed with `N_JOBS=2`, peaking around 16.6 GB RSS.
Those numbers are recorded in `VALIDATION.md`.

The smaller 16 um file remains in `data/` for quick smoke tests and for the
broader mini-reproduction notebook:

`data/visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad`

## Rebuild The Data Files

Only needed if you want to recreate the bundled `.h5ad` files.

The default 2 um practice file is recreated from a full P2 AnnData intermediate:

```bash
CONDA_NO_PLUGINS=true \
NUMBA_CACHE_DIR=/tmp/numba_spix_workshop_build MPLCONFIGDIR=/tmp/mpl_spix_workshop_build \
conda run --no-capture-output -n SPIX_0426 \
python scripts/build_visiumhd_2um_roi_from_full_h5ad.py \
  --max-obs 1000000 \
  --output data/visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad
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

## Regenerate Notebook

Regenerate the practical notebook after changing the data file or default URLs:

```bash
CONDA_NO_PLUGINS=true conda run --no-capture-output -n SPIX_0426 \
python scripts/write_korean_workshop_notebook.py
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

The current local check uses the same VisiumHD P2 SPIX path as the manuscript
workflow, but on the bounded 1M native 2 um ROI. Current numbers are in
`VALIDATION.md`.

## Publish For Colab

Before pushing, check the files that Colab will need:

```bash
CONDA_NO_PLUGINS=true conda run --no-capture-output -n SPIX_0426 \
python scripts/check_colab_publish_ready.py
```

After pushing, check the GitHub raw URLs:

```bash
CONDA_NO_PLUGINS=true conda run --no-capture-output -n SPIX_0426 \
python scripts/check_colab_publish_ready.py --check-urls
```

The notebook expects these raw URLs:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad`

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_p2_roi_context_1000000_downsample.csv`

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/bayesspace_labels_1m_panel3500.csv`

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/requirements-colab.txt`

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/notebooks/colab_bootstrap.py`

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/notebooks/workshop_helpers.py`

Before a live run, make sure those files exist at the URLs above. If not, set
the matching `SPIX_WORKSHOP_*_URL` value in the first notebook cell.

## Colab Notes

- Use CPU runtime: `Runtime > Change runtime type > Hardware accelerator: None`.
- The notebook defaults to `N_JOBS=2`.
- Colab safe mode is on by default in Colab. It keeps SVG/domain/CCI on the
  1M ROI-derived 8 um pseudobulk, then runs SPIX on a central 500k native
  2 um subset after clearing standard-analysis objects from memory.
- Python packages are pinned in `requirements-colab.txt`. `zarr==2.18.3` is
  fixed deliberately so the SPIX image-cache step does not receive zarr v3 in a
  fresh Colab runtime.
- The notebook does not install R/Bioconductor BayesSpace by default in Colab.
  If BayesSpace is already available, it runs live. Otherwise it uses the
  bundled BayesSpace labels for the fixed 3,500-bin domain panel. Set
  `SPIX_WORKSHOP_INSTALL_BAYESSPACE=1` only for a rehearsal where a long R
  install is acceptable.
- Colab free-tier CPU/RAM is assigned by Colab and is not a reproducible knob
  for workshop participants. The first notebook cell records `cpu_count`,
  memory, and disk space for the actual runtime.
- The default SPIX section runs smoothing/equalization sweeps. For a shortened
  rehearsal, set `SPIX_WORKSHOP_SPIX_RUN_TUNING=0`.
- Keep participant edits focused on `SPIX_WORKSHOP_N_JOBS`,
  `SPIX_WORKSHOP_DOMAIN_MAX_OBS`, `SPIX_WORKSHOP_SPIX_MAX_2UM_BINS`,
  `SPIX_WORKSHOP_SPIX_RUN_TUNING`, and selected plotting genes.
- If Colab is slow or disconnects, restart the runtime and run cells from the top.
