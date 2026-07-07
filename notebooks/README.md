# Notebook Guide

KOGO 공간전사체 실습에서 사용할 Colab 파일입니다.

`Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb`

`Choi_Whisoo_KOGO_spatial_downstream_colab.ipynb`

두 번째 파일은 강의 흐름을 더 분명히 잡은 downstream lecture 버전입니다. 앞선
KOGO 실습의 Visium deconvolution, VisiumHD segmentation, Xenium/cell typing
결과가 이후 분석 질문으로 어떻게 이어지는지를 먼저 잡고, SVG -> spatial domain
-> CCI -> SPIX 순서로 진행합니다.

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

BayesSpace는 R 패키지가 이미 준비되어 있으면 live로 실행합니다. Colab에서 R
패키지가 없으면 설치에 오래 걸릴 수 있으므로, 기본 실습은 고정 ROI/panel에서
미리 계산한 BayesSpace label을 읽어옵니다.

SpaGCN은 기본 Colab 경로에서 미리 계산한 label을 읽어옵니다. SpaGCN live 실행은
TensorFlow import 때문에 무료 Colab kernel이 재시작될 수 있어 수업 기본값에서는
끄고, 필요할 때만 `SPIX_WORKSHOP_RUN_SPAGCN_LIVE=1`로 켭니다.

기본 데이터는 VisiumHD P2의 native 2 um 1M-bin ROI입니다. 일반 분석은
이 ROI를 8 um pseudobulk로 만든 뒤 진행하고, SPIX 파트는 같은 1M 2 um ROI를
native resolution에서 사용합니다. 무료 Colab 런타임이 불안정하면
`SPIX_WORKSHOP_SPIX_MAX_2UM_BINS=500000`으로 낮춰 리허설할 수 있습니다.

- SVG: Moran's I로 공간 패턴 gene을 찾고, domain DEG, SVG module,
  program overlap으로 해석
- Spatial domain: expression-only baseline, Squidpy spatial graph, BANKSY,
  BayesSpace, SpaGCN 비교와 marker/program 해석
- Cell-cell interaction: Squidpy neighborhood enrichment, Squidpy `ligrec`,
  LIANA rank-aggregate 결과 비교, CellPhoneDB/CellChat/COMMOT/SpaTalk
  reference table

SPIX 파트는 VisiumHD P2 논문/재현 코드의 흐름에 맞춰 `embedding ->
graph smoothing -> equalization -> image cache -> image_plot_slic
multiscale segmentation -> multiscale Moran/SVG` 순서로 진행합니다.
smoothing/equalization parameter는 기본값에서 sweep으로 자동 선택합니다.
마지막에는 scale-response SVG heatmap, gene map, CRC ontology reference
heatmap을 이어서 보면서 SPIX의 scale별 생물학 해석을 확인합니다.
