# SPIX Colab Workshop

This workshop is a small CPU-only SPIX mini-reproduction for free Google Colab
runtimes. It uses a compact ROI derived from the public 10x Genomics Visium HD
Human Colon Cancer dataset and walks through:

1. loading a small `AnnData` object,
2. building an SPIX embedding image,
3. exporting fine/mid/coarse SPIX segmentations, and
4. ranking spatially variable genes across scales with Moran's I,
5. plotting native versus SPIX-averaged expression maps, and
6. contrasting expression abundance with scale-resolved spatial organization.

The goal is to reproduce the manuscript's core multiscale analysis logic in a
format that many workshop participants can run live. The full manuscript panel
reproduction remains a separate local reference package outside this public
workshop repository.

The original manuscript mini-reproduction notebook is:

`notebooks/SPIX_VisiumHD_multiscale_colab.ipynb`

The Choi Whisoo section notebook for **SPIX, spatial clustering, SVG, and
cell-cell interaction** is:

`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

For the panel-by-panel boundary between live Colab execution and reference-only
full reproduction, see `MANUSCRIPT_CORE_RESULTS_MAP.md`.

For the direct Colab free-tier run protocol, see
`COLAB_LIVE_RUN_PROTOCOL.md`.

## Dataset

Source dataset:

<https://www.10xgenomics.com/datasets/visium-hd-cytassist-11mm-human-colon-cancer-HE>

The source page lists the dataset as a Visium HD Spatial Gene Expression Human
Colon Cancer dataset analyzed with Space Ranger 4.1.0 and licensed under
Creative Commons Attribution 4.0 International.

The default workshop file is a derived subset:

`data/visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad`

It keeps a spatially contiguous `square_016um` ROI selected for mixed
epithelial/secretory, immune, stromal, and proliferative marker signal, plus a
bounded gene set. This is intentional: full Visium HD outputs are too large and
too variable for a room of free Colab runtimes.

## Build The Data File

Run from this workshop repository root:

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

## Regenerate The Notebook

After the data file exists, regenerate the notebook so it embeds the current
SHA-256 checksum:

```bash
CONDA_NO_PLUGINS=true conda run --no-capture-output -n SPIX_0426 \
python scripts/write_colab_notebook.py \
  --output notebooks/SPIX_VisiumHD_multiscale_colab.ipynb \
  --data-file data/visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad
```

## Validate Locally

Execute the notebook top-to-bottom before sharing. In a full Jupyter
environment, use:

```bash
CONDA_NO_PLUGINS=true \
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 \
NUMBA_CACHE_DIR=/tmp/numba_spix_workshop_nb MPLCONFIGDIR=/tmp/mpl_spix_workshop_nb \
conda run --no-capture-output -n SPIX_0426 \
jupyter nbconvert --execute --to notebook --inplace \
  notebooks/SPIX_VisiumHD_multiscale_colab.ipynb
```

If `nbconvert`, `nbclient`, or `nbformat` are not installed, use the bundled
fallback executor from the workshop directory:

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

Current local validation is recorded in `VALIDATION.md`.

## Publish For Colab

The notebook default data URL points at the GitHub raw URL for this repository:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad`

Before a live workshop, make sure the data file has been pushed to the branch
used by that URL, or set `SPIX_WORKSHOP_DATA_URL` in the first notebook cell to
a GitHub Release, Zenodo, or Google Cloud Storage URL.

The true free-tier check is intentionally separate from local validation because
Colab runtime allocation requires an interactive Google account. Use
`COLAB_FREE_TIER_VERIFICATION.md` for the release checklist.

## Colab Notes

- Use CPU runtime: `Runtime > Change runtime type > Hardware accelerator: None`.
- The notebook defaults to `N_JOBS=2`.
- Keep participant edits focused on `RESOLUTIONS_UM`, `N_JOBS`, and the gene
  tables. Avoid asking every participant to download full Visium HD outputs.
- If Colab is slow or disconnects, restart the runtime and run cells from the top.
