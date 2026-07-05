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

Colab free-tier hardware is assigned by Colab and should not be treated as a
fixed CPU-core setting. The notebook records `cpu_count`, `/proc/meminfo`, and
disk free space in the first cell. The observed free-tier CPU result received
for this workshop was 2 CPUs and 12.67 GB memory.

## Run

1. Open the main notebook in Colab:
   - `notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`
2. Select `Runtime > Disconnect and delete runtime`.
3. Select `Runtime > Change runtime type > Hardware accelerator: None`.
4. Run all cells from the top.
5. The final cell must print `Validation passed` and write a JSON timing
   report. The practical notebook auto-downloads its timing report when
   running in Colab.

## Pass Criteria

- `running_in_colab` is `true` in the first-cell runtime snapshot.
- Notebook runs on CPU runtime with no GPU requirement.
- Data SHA-256 check passes.
- The practical notebook completes all of its stages:
  - standard-tool preprocessing with Scanpy and Squidpy,
  - SVG with Squidpy Moran's I,
  - spatial clustering with Scanpy Leiden and marker ranking,
  - cell-cell interaction with Squidpy `ligrec`,
  - SPIX manuscript-style embedding, graph smoothing, equalization, image
    cache,
  - SPIX `image_plot_slic` multiscale segmentation and multiscale Moran/SVG.
- Final cluster tables, SVG table, CCI table, and SPIX segment counts are non-empty.
- Total elapsed runtime is acceptable for the workshop slot.

## Current Default Preflight Result

Observed locally on 2026-07-06 with the combined practical notebook:

- Data:
  - shape: `500000 x 2515`
  - file size: 42.89 MB
  - SHA-256:
    `ddc3a4eb3ee5b64dae210a6c8cf5820fbbfff784cabbebdf671100c266e8a586`
- Result:
  - top-to-bottom notebook pass with `N_JOBS=2`
  - local elapsed after dependencies and data were present: 128.32 seconds
- Output checks:
  - standard-tool teaching subset: `47039 x 2515`
  - Scanpy Leiden clusters: 13 at `n_neighbors=30`, `resolution=0.01`
  - top Squidpy Moran SVG examples: `OLFM4`, `PIGR`, `REG1A`, `MUC2`,
    `TAGLN`
  - Squidpy `ligrec`: 11 ligand-receptor candidates, 20 permutations,
    top examples include `MIF-CD74`, `CD74-MIF`, and `LGALS3-ITGB1`
  - SPIX section uses the full `500000 x 2515` ROI
  - SPIX follows the VisiumHD P2 manuscript/reproduction path: 30-dimensional
    PCA/log-normalized embedding, graph smoothing before equalization,
    `image_plot_slic` segmentation, and multiscale Moran/SVG
  - default SPIX tuning is off for workshop runtime; the fixed fallback values
    are `graph_k=20`, `graph_t=10`, `sleft=2.0`, `sright=2.0`
  - manuscript-style tuning sweeps can be enabled with
    `SPIX_WORKSHOP_SPIX_RUN_TUNING=1`
  - SPIX segment counts:
    `r2` 500000, `r8` 32146, `r16` 8012, `r30` 2272, `r40` 1277,
    `r50` 806, `r80` 312, `r100` 200, `r150` 89, `r200` 51,
    `r250` 29, `r300` 21, `r350` 19, `r400` 12, `r450` 12, `r500` 5

This validates the current notebook/data path before a live Colab run. Collect
a new downloaded timing report from real Colab after this change is pushed.

## Full P2 8M-Bin Boundary

The full P2 2 um object was tested locally with a 12 GiB memory cap to mimic the
observed free-tier memory budget.

The current probe script defaults to the same manuscript-style SPIX path as the
workshop notebook. The historical high-memory timings below came from an
earlier lower-dimensional boundary probe, so they should be used for memory
feasibility, not as the final timing of the current 30-dimensional/16-scale
path.

- Full `8731400 x 18085` in-memory `read_h5ad`: failed with `MemoryError`
  before SPIX analysis.
- Full `8731400 x 2515` selected-gene materialization from backed AnnData:
  failed while allocating a 956 MiB CSR index array.
- High-memory local server, no 12 GiB cap:
  - `8731400 x 2515` SPIX embedding/cache/segmentation completed in
    14.1 minutes with `N_JOBS=2`.
  - multiscale Moran/SVG completed in 6.3 minutes.
  - peak RSS was about 16.6 GB.

Conclusion: full P2 can be used as a high-memory stress/reference run, but it is
not a safe free-tier Colab hands-on default. The workshop default remains the
500k native 2 um ROI.

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
