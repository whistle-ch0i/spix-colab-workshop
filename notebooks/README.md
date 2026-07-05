# Notebook Guide

KOGO 공간전사체 실습에서 사용할 Colab 파일입니다.

`Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

실습 순서는 다음과 같습니다.

1. SVG
2. Spatial clustering
3. Cell-cell interaction
4. SPIX

코드는 함수형 helper를 최소화하고, 실습 중 위에서 아래로 따라가기 쉽도록
단계별 code cell로 나누어 두었습니다.

앞의 세 분석은 많이 쓰이는 표준 도구로 진행합니다.

- SVG: Squidpy Moran's I
- Spatial clustering: Scanpy PCA, neighbor graph, Leiden
- Cell-cell interaction: Squidpy `ligrec`

SPIX 파트는 VisiumHD P2 논문/재현 코드의 흐름에 맞춰 `embedding ->
graph smoothing -> equalization -> image cache -> image_plot_slic
multiscale segmentation -> multiscale Moran/SVG` 순서로 진행합니다.
