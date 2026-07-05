# Data Directory

This directory contains the workshop `.h5ad` files.

Default for the KOGO practical notebook:

`visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad`

ROI overview helper:

`visiumhd_p2_roi_context_1000000_downsample.csv`

This CSV contains 120,000 downsampled full-P2 coordinates plus the selected ROI
bounding box. The notebook uses it only for the first ROI-location plot.

The previous 500k ROI is kept as a fallback for quick debugging:

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
set for workshop runtime stability. The notebook builds 8 um pseudobulk from
this file for SVG, spatial domain, and CCI sections. The SPIX section uses the
native 2 um file to run the VisiumHD P2 manuscript-style workflow on a
Colab-sized ROI.

Source dataset:
<https://www.10xgenomics.com/datasets/visium-hd-cytassist-11mm-human-colon-cancer-HE>
