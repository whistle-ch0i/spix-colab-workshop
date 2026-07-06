# Data Directory

This directory contains the workshop `.h5ad` files.

Default for the KOGO practical notebook:

`visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad`

ROI overview helper:

`visiumhd_p2_roi_context_1000000_downsample.csv`

This CSV contains 120,000 downsampled full-P2 coordinates plus the selected ROI
bounding box. The notebook uses it only for the first ROI-location plot.

Bundled spatial domain labels for the fixed 3,500-bin 8 um panel:

`bayesspace_labels_1m_panel3500.csv`

`spagcn_labels_1m_panel3500.csv`

These files keep the live Colab run stable. BayesSpace can require a long
R/Bioconductor setup, and SpaGCN can restart free Colab kernels through its
TensorFlow import path. The notebook still explains both methods in the spatial
domain comparison section.

Bundled CCI result for the same fixed 3,500-bin panel:

`liana_rank_aggregate_1m_panel3500.csv`

This file was produced with LIANA rank-aggregate on the bundled BayesSpace
domain labels used by the CCI section. The notebook uses it by default so the
workshop does not depend on a fresh LIANA install during class.
Regenerate it with `scripts/build_liana_rank_aggregate_panel.py` after changing
the fixed panel or CCI domain labels.

Reference ontology tables for the SPIX scale-response SVG section:

`crc_scale_svg_ontology_reference.csv`

`crc_ontology_layer_summary_by_scale.csv`

These are copied from the manuscript reproduction ontology tables. The notebook
does not rerun online Enrichr calls during class; it uses these fixed tables to
show how fine, mid, and coarse SPIX SVGs are interpreted.

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
