# Data Directory

This directory is for the compact workshop `.h5ad` file:

`visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad`

Generate it with:

```bash
python ../scripts/build_visiumhd_colon_roi_h5ad.py --help
```

The file is derived from the 10x Genomics Visium HD Human Colon Cancer public
dataset and keeps a marker-diverse spatial ROI plus a bounded gene set for
workshop runtime stability.

Source dataset:
<https://www.10xgenomics.com/datasets/visium-hd-cytassist-11mm-human-colon-cancer-HE>
