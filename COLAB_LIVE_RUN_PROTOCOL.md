# Colab Free-Tier Run

Use this checklist for the live free-tier run.

## Open

Main practical notebook:

`notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Colab URL:

`https://colab.research.google.com/github/whistle-ch0i/spix-colab-workshop/blob/main/notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

Data URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad`

ROI context URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/visiumhd_p2_roi_context_1000000_downsample.csv`

Bundled BayesSpace label URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/bayesspace_labels_1m_panel3500.csv`

Bundled SpaGCN label URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/data/spagcn_labels_1m_panel3500.csv`

Requirements URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/requirements-colab.txt`

Bootstrap URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/notebooks/colab_bootstrap.py`

Helper URL:

`https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/notebooks/workshop_helpers.py`

## Before Opening Colab

Before pushing:

```bash
CONDA_NO_PLUGINS=true conda run --no-capture-output -n SPIX_0426 \
python scripts/check_colab_publish_ready.py
```

After pushing:

```bash
CONDA_NO_PLUGINS=true conda run --no-capture-output -n SPIX_0426 \
python scripts/check_colab_publish_ready.py --check-urls
```

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
- The notebook prints `[memory] ...` lines around data loading, pseudobulk,
  cleanup, and SPIX stages. If Colab exits silently, the last printed memory
  line is the first place to check.
- The standard sections use the 8 um pseudobulk object made from the 2 um ROI.
- The spatial domain section includes expression-only baseline, Squidpy spatial
  graph, BANKSY through `pyBANKSY`, BayesSpace, and SpaGCN.
- In the default Colab path, SpaGCN uses bundled labels for the fixed
  3,500-bin panel. Do not turn on live SpaGCN during class unless it has already
  been rehearsed in the same Colab runtime type.
- The CCI section includes spatial neighborhood enrichment and Squidpy `ligrec`.
- The SPIX section reports the VisiumHD P2-style path:
  30-dimensional embedding, graph smoothing before equalization,
  `image_plot_slic` multiscale segmentation, and multiscale Moran/SVG.
- In default Colab safe mode, the SPIX section uses a central 500k native
  2 um subset after standard-analysis objects are cleared from memory.
- The default SPIX run uses automatic smoothing/equalization parameter sweeps.
- Total time is acceptable for the workshop slot.

## Current Default Local Check

Observed locally on 2026-07-06 with the combined practical notebook:

- Dataset: native 2 um ROI, `1000000 x 2515`, 87.29 MiB.
- 8 um pseudobulk: `62898 x 2515`.
- Spatial domain comparison panel: `3500 x 2515`.
- ROI context SHA-256:
  `5b429739f7901cfa92b45afbaf7d6b4b191beafd547829d5f8fa5c7042e0e5a4`.
- Validation: top-to-bottom notebook pass with `N_JOBS=2`.
- Code cells: 37/37 passed.
- Local elapsed time in Colab safe mode after dependencies and data were
  present: 219.32 seconds.
- Final process peak RSS in local safe-mode validation: 3.06 GB.
- Setup files included in the repo:
  `requirements-colab.txt`, `notebooks/colab_bootstrap.py`, and
  `notebooks/workshop_helpers.py`.
- Pinned Python package check:
  `scanpy 1.11.5`, `squidpy 1.6.5`, `pybanksy 1.3.5`,
  `anndata 0.11.4`, `zarr 2.18.3`, `numcodecs 0.13.1`.
- Squidpy Moran top examples: `PIGR`, `OLFM4`, `FCGBP`, `COL1A1`, `COL3A1`.
- Top 100 HVG/SVG overlap: 3 genes.
- Spatial domain methods: expression-only baseline, Squidpy spatial graph,
  BANKSY through `pyBANKSY`, BayesSpace, and SpaGCN.
- BayesSpace uses live R BayesSpace only when the R package is already
  available or `SPIX_WORKSHOP_INSTALL_BAYESSPACE=1` is set. The default Colab
  fallback uses bundled BayesSpace labels for the fixed 3,500-bin domain panel.
- SpaGCN uses bundled labels by default for the fixed 3,500-bin domain panel.
  Live SpaGCN is optional with `SPIX_WORKSHOP_RUN_SPAGCN_LIVE=1`; it is not the
  workshop default because it imports TensorFlow and can restart a free Colab
  kernel.
- CCI: neighborhood enrichment plus Squidpy `ligrec` with 11 LR candidates and
  20 permutations.
- SPIX: manuscript-style 30-dimensional embedding, graph smoothing,
  equalization, `image_plot_slic` segmentation, and multiscale Moran/SVG.
- SPIX input in default Colab safe mode: central `500000 x 2515` native 2 um
  bins.
- Automatic SPIX smoothing recommendation: `graph_k=15`, `graph_t=10`.
- Automatic SPIX equalization recommendation: `BalanceSimplest`, `sleft=0.5`,
  `sright=0.5`.
- SPIX segment counts:
  `r2` 500000, `r8` 33257, `r16` 8283, `r30` 2343, `r40` 1185,
  `r50` 777, `r80` 303, `r100` 197, `r150` 89, `r200` 49,
  `r250` 28, `r300` 21, `r350` 18, `r400` 12, `r450` 12,
  `r500` 5.
- Slowest local stages in Colab safe mode: SPIX multiscale segmentation
  45.00 sec, 8 um preprocessing 42.69 sec, equalization sweep 29.19 sec,
  smoothing sweep 26.07 sec, import analysis packages 20.09 sec,
  SPIX multiscale Moran/SVG 16.40 sec. BayesSpace and SpaGCN bundled label
  loading each took 0.01 sec.

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

For planning the current Colab-safe notebook, the local analysis pass takes
about 3.7 minutes after packages and data are present. A fresh Colab runtime
also has to install missing packages and download files, so reserve about
6-10 minutes until a new real Colab timing report is collected.

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
