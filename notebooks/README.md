# Notebook Guide

KOGO 공간전사체 실습에서 사용할 Colab 파일입니다.

`Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

실습 순서는 다음과 같습니다.

1. SVG
2. Spatial domain
3. Cell-cell interaction
4. SPIX

코드는 실습 중 위에서 아래로 따라가기 쉽도록 단계별 code cell로 나누어
두었습니다. 파일 다운로드, checksum 확인, timing 기록, 간단한 plotting처럼
반복되는 작업만 `workshop_helpers.py`로 뺐고, 분석 도구는 노트북 안에서 원래
함수 이름으로 직접 호출합니다.

Colab에서 패키지 설치와 SPIX optional import 보정은 `colab_bootstrap.py`가
담당합니다. Python 패키지 버전은 repo root의 `requirements-colab.txt`에 고정해
두었습니다.

기본 데이터는 VisiumHD P2의 native 2 um 1M-bin ROI입니다. 일반 분석은
이 ROI를 8 um pseudobulk로 만든 뒤 진행합니다.

- SVG: HVG와 Squidpy Moran's I 비교
- Spatial domain: expression-only baseline, Squidpy spatial graph, BANKSY,
  BayesSpace, SpaGCN 비교
- Cell-cell interaction: Squidpy neighborhood enrichment, Squidpy `ligrec`

SPIX 파트는 VisiumHD P2 논문/재현 코드의 흐름에 맞춰 `embedding ->
graph smoothing -> equalization -> image cache -> image_plot_slic
multiscale segmentation -> multiscale Moran/SVG` 순서로 진행합니다.
smoothing/equalization parameter는 기본값에서 sweep으로 자동 선택합니다.
