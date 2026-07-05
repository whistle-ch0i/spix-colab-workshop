# Notebook Guide

기본 강의 자료는 하나의 한국어 Colab 노트북입니다.

`Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

노트북 안의 강의 순서는 다음과 같습니다.

1. SVG
2. Spatial clustering
3. Cell-cell interaction
4. SPIX

앞의 세 분석은 각각 많이 쓰이는 표준 도구로 진행합니다.

- SVG: Squidpy Moran's I
- Spatial clustering: Scanpy PCA, neighbor graph, Leiden
- Cell-cell interaction: Squidpy `ligrec`

SPIX는 마지막 섹션에서 독립적으로 다룹니다. 이 파트는 VisiumHD P2
논문/재현 코드의 흐름에 맞춰 `embedding -> graph smoothing ->
equalization -> image cache -> image_plot_slic multiscale segmentation ->
multiscale Moran/SVG` 순서로 진행합니다.
