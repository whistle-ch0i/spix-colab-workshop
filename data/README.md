# Data Directory

This directory contains the workshop `.h5ad` files.

Default for the KOGO practical notebook:

`visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad`

Quick smoke-test and broader mini-reproduction file:

`visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad`

Generate the 2 um file with:

```bash
python ../scripts/build_visiumhd_2um_roi_from_full_h5ad.py --help
```

Generate the 16 um file with:

```bash
python ../scripts/build_visiumhd_colon_roi_h5ad.py --help
```

The file is derived from the 10x Genomics Visium HD Human Colon Cancer public
dataset. The main file keeps native 2 um bins while bounding the ROI and gene
set for workshop runtime stability. The SPIX section uses this file to run the
VisiumHD P2 manuscript-style workflow on a Colab-sized native-resolution ROI.

Source dataset:
<https://www.10xgenomics.com/datasets/visium-hd-cytassist-11mm-human-colon-cancer-HE>
