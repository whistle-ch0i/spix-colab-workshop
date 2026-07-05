#!/usr/bin/env python3
"""Write the KOGO spatial transcriptomics practical notebook."""

from __future__ import annotations

import argparse
import hashlib
import json
import textwrap
from pathlib import Path

try:
    import nbformat as nbf
except Exception:  # pragma: no cover
    nbf = None


DATA_FILE = "visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad"
ROI_CONTEXT_FILE = "visiumhd_p2_roi_context_1000000_downsample.csv"
DEFAULT_DATA_URL = (
    "https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/"
    f"data/{DATA_FILE}"
)
DEFAULT_ROI_CONTEXT_URL = (
    "https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/"
    f"data/{ROI_CONTEXT_FILE}"
)
HELPER_FILE = "workshop_helpers.py"
DEFAULT_HELPER_URL = (
    "https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/"
    f"notebooks/{HELPER_FILE}"
)
DEFAULT_NOTEBOOK_DIR = "notebooks"
COMBINED_NOTEBOOK = "Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb"


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def md(source: str):
    text = textwrap.dedent(source).strip() + "\n"
    if nbf is not None:
        return nbf.v4.new_markdown_cell(text)
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(source: str):
    text = textwrap.dedent(source).strip() + "\n"
    if nbf is not None:
        return nbf.v4.new_code_cell(text)
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def new_notebook(name: str):
    if nbf is not None:
        nb = nbf.v4.new_notebook()
    else:
        nb = {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": []}
    nb["metadata"]["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb["metadata"]["language_info"] = {"name": "python", "pygments_lexer": "ipython3"}
    nb["metadata"]["colab"] = {"name": name, "provenance": [], "toc_visible": True}
    return nb


def setup_cells(
    data_url: str,
    data_sha256: str,
    roi_context_url: str,
    roi_context_sha256: str,
    helper_url: str,
) -> list:
    setup_code = """
    import os
    import sys
    import json
    import time
    import shutil
    import warnings
    import subprocess
    import urllib.request
    import importlib.util
    from pathlib import Path

    LECTURE_ID = os.environ.get("SPIX_WORKSHOP_LECTURE_ID", "choi_whisoo_combined")
    RUN_STARTED_AT = time.perf_counter()
    STAGE_TIMES = []

    N_JOBS = int(os.environ.get("SPIX_WORKSHOP_N_JOBS", "2"))
    os.environ.setdefault("OMP_NUM_THREADS", str(N_JOBS))
    os.environ.setdefault("OPENBLAS_NUM_THREADS", str(N_JOBS))
    os.environ.setdefault("MKL_NUM_THREADS", str(N_JOBS))
    os.environ.setdefault("NUMEXPR_NUM_THREADS", str(N_JOBS))
    os.environ.setdefault("VECLIB_MAXIMUM_THREADS", str(N_JOBS))
    os.environ.setdefault("SPIX_ENABLE_THREAD_CAP", "1")
    os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_spix_workshop")

    DATA_FILE = os.environ.get("SPIX_WORKSHOP_DATA_FILE", __DATA_FILE__)
    DATA_URL = os.environ.get("SPIX_WORKSHOP_DATA_URL", __DATA_URL__)
    DATA_SHA256 = os.environ.get("SPIX_WORKSHOP_DATA_SHA256", __DATA_SHA256__)
    ROI_CONTEXT_FILE = os.environ.get("SPIX_WORKSHOP_ROI_CONTEXT_FILE", __ROI_CONTEXT_FILE__)
    ROI_CONTEXT_URL = os.environ.get("SPIX_WORKSHOP_ROI_CONTEXT_URL", __ROI_CONTEXT_URL__)
    ROI_CONTEXT_SHA256 = os.environ.get("SPIX_WORKSHOP_ROI_CONTEXT_SHA256", __ROI_CONTEXT_SHA256__)
    HELPER_FILE = os.environ.get("SPIX_WORKSHOP_HELPER_FILE", __HELPER_FILE__)
    HELPER_URL = os.environ.get("SPIX_WORKSHOP_HELPER_URL", __HELPER_URL__)

    OUTPUT_DIR = Path("spix_korean_lecture_outputs") / LECTURE_ID
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    IN_COLAB = "google.colab" in sys.modules or "COLAB_RELEASE_TAG" in os.environ
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")

    helper_candidates = [
        Path(HELPER_FILE),
        Path("notebooks") / HELPER_FILE,
        Path.cwd() / "notebooks" / HELPER_FILE,
        Path("/content") / HELPER_FILE,
    ]
    helper_path = next((path.resolve() for path in helper_candidates if path.exists()), None)
    if helper_path is None:
        helper_path = Path("/content" if IN_COLAB else ".") / HELPER_FILE
        print("Downloading helper:", HELPER_URL)
        urllib.request.urlretrieve(HELPER_URL, helper_path)
        helper_path = helper_path.resolve()
    sys.path.insert(0, str(helper_path.parent))

    from workshop_helpers import (
        add_segment_labels,
        center_nonzero_panel,
        domain_ari_table as make_domain_ari_table,
        domain_count_table as make_domain_count_table,
        file_sha256,
        locate_or_download,
        pseudobulk_visiumhd_2um_to_8um,
        runtime_snapshot,
        sample_indices,
        sparse_vector,
        spatial_scatter,
        tidy_ligrec_result,
        timed_stage,
        top_rank_table,
    )

    runtime_info = runtime_snapshot(N_JOBS)

    print(json.dumps(runtime_info, indent=2, ensure_ascii=False))
    """
    setup_code = (
        setup_code.replace("__DATA_FILE__", json.dumps(DATA_FILE))
        .replace("__DATA_URL__", json.dumps(data_url))
        .replace("__DATA_SHA256__", json.dumps(data_sha256))
        .replace("__ROI_CONTEXT_FILE__", json.dumps(ROI_CONTEXT_FILE))
        .replace("__ROI_CONTEXT_URL__", json.dumps(roi_context_url))
        .replace("__ROI_CONTEXT_SHA256__", json.dumps(roi_context_sha256))
        .replace("__HELPER_FILE__", json.dumps(HELPER_FILE))
        .replace("__HELPER_URL__", json.dumps(helper_url))
    )

    return [
        md(
            """
            ## 0. 실행 환경

            먼저 지금 할당된 Colab runtime을 확인합니다. 실습 기본값은 CPU runtime,
            `N_JOBS=2`입니다. 시간이 충분하고 runtime이 넉넉하면 `N_JOBS`만 조금
            올리면 됩니다.

            파일 다운로드, checksum 확인, 시간 기록처럼 분석의 핵심이 아닌 반복
            작업은 `workshop_helpers.py`에 모아 두었습니다. 분석 도구 자체는 뒤에서
            Scanpy, Squidpy, BANKSY, BayesSpace, SpaGCN, SPIX 원래 함수 이름으로
            직접 호출합니다.
            """
        ),
        code(setup_code),
        md(
            """
            ## 1. 패키지 준비

            Colab에서 없는 패키지는 여기서 설치합니다. 로컬에서 실행할 때는 현재
            workspace에 있는 SPIX checkout을 먼저 사용합니다. Spatial domain 비교에
            BayesSpace를 포함했기 때문에 R의 BayesSpace 패키지도 함께 확인합니다.
            """
        ),
        code(
            """
            with timed_stage("import_or_install", STAGE_TIMES):
                if importlib.util.find_spec("SPIX") is None:
                    repo_root = None
                    for root in [Path.cwd().resolve(), *Path.cwd().resolve().parents]:
                        if (root / "SPIX" / "__init__.py").exists():
                            repo_root = root
                            break

                    if repo_root is not None:
                        sys.path.insert(0, str(repo_root))
                    elif IN_COLAB:
                        subprocess.check_call([
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "-q",
                            "git+https://github.com/whistle-ch0i/SPIX.git",
                        ])
                    else:
                        raise ImportError("SPIX repo 안에서 실행하거나 SPIX를 설치하세요.")

                needed = {
                    "scanpy": "scanpy",
                    "squidpy": "squidpy",
                    "SpaGCN": "SpaGCN",
                    "banksy": "pybanksy",
                    "anndata": "anndata",
                }
                missing = [
                    pip_name
                    for module, pip_name in needed.items()
                    if importlib.util.find_spec(module) is None
                ]
                if missing:
                    if not IN_COLAB:
                        raise ImportError(f"설치되지 않은 패키지: {missing}")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])

                if shutil.which("Rscript") is None:
                    raise ImportError("BayesSpace 실행을 위해 Rscript가 필요합니다.")

                bayesspace_check = subprocess.run(
                    [
                        "Rscript",
                        "-e",
                        "quit(status=ifelse(requireNamespace('BayesSpace', quietly=TRUE), 0, 1))",
                    ],
                    capture_output=True,
                    text=True,
                )
                if bayesspace_check.returncode != 0:
                    if not IN_COLAB:
                        raise ImportError("R package BayesSpace가 설치되어 있지 않습니다.")
                    subprocess.check_call([
                        "Rscript",
                        "-e",
                        (
                            "if (!requireNamespace('BiocManager', quietly=TRUE)) "
                            "install.packages('BiocManager', repos='https://cloud.r-project.org'); "
                            "BiocManager::install('BayesSpace', update=FALSE, ask=FALSE); "
                            "if (!requireNamespace('BayesSpace', quietly=TRUE)) "
                            "stop('BayesSpace install failed')"
                        ),
                    ])
                R_BAYESSPACE_READY = True

            print("BayesSpace R package: ready")
            """
        ),
        md(
            """
            ## 1-1. SPIX optional import 정리

            pip 설치본에서 오늘 쓰지 않는 optional module 때문에 import가 멈추는
            경우가 있어, 필요한 entry만 남깁니다.
            """
        ),
        code(
            """
            with timed_stage("patch_spix_optional_imports", STAGE_TIMES):
                if IN_COLAB:
                    spix_spec = importlib.util.find_spec("SPIX")
                    spix_root = Path(spix_spec.origin).parent

                    visualization_init = spix_root / "visualization" / "__init__.py"
                    if visualization_init.exists():
                        visualization_init.write_text(
                            "from .plotting import *\\n"
                            "from .origin_display import *\\n"
                        )

                    analysis_init = spix_root / "analysis" / "__init__.py"
                    if analysis_init.exists():
                        analysis_init.write_text(
                            "import os\\n"
                            "os.environ.setdefault('NUMBA_CACHE_DIR', '/tmp/numba_spix')\\n"
                            "from .multiscale_moran_ranks import *\\n"
                        )
            """
        ),
        md(
            """
            ## 1-2. import

            이후 셀에서는 아래 패키지들만 사용합니다.
            """
        ),
        code(
            """
            with timed_stage("import_analysis_packages", STAGE_TIMES):
                import anndata as ad
                import matplotlib.pyplot as plt
                import numpy as np
                import pandas as pd
                import scanpy as sc
                import scipy.sparse as sp
                import scipy.io as sio
                import squidpy as sq
                import SpaGCN
                from banksy.initialize_banksy import initialize_banksy
                from banksy.run_banksy import run_banksy_multiparam
                from IPython.display import display
                import SPIX

            print("Scanpy:", sc.__version__)
            print("Squidpy:", sq.__version__)
            print("BANKSY:", importlib.util.find_spec("banksy").origin)
            print("SPIX:", SPIX.__file__)
            """
        ),
    ]


def data_cells() -> list:
    return [
        md(
            """
            ## 2. 데이터 불러오기

            실습 입력은 Visium HD Human Colon Cancer P2의 2 um ROI입니다. 일반
            분석은 뒤에서 8 um pseudobulk로 바꾸고, SPIX 파트만 2 um 그대로
            사용합니다.
            """
        ),
        code(
            """
            with timed_stage("load_2um_data", STAGE_TIMES):
                data_path = locate_or_download(DATA_FILE, DATA_URL, sha256=DATA_SHA256)
                observed_sha256 = file_sha256(data_path)

                adata_2um = sc.read_h5ad(data_path)
                adata_2um.obs_names = adata_2um.obs_names.astype(str)
                adata_2um.var_names = adata_2um.var_names.astype(str)
                coords_2um = np.asarray(adata_2um.obsm["spatial"], dtype=float)

                source = adata_2um.uns.get("spix_workshop_source", {})
                data_summary = pd.DataFrame([{
                    "2um_bins": adata_2um.n_obs,
                    "genes": adata_2um.n_vars,
                    "file_mb": round(data_path.stat().st_size / 1024**2, 2),
                    "bin_size_um": source.get("bin_size_um", "unknown"),
                    "full_source_shape": str(source.get("full_shape", "unknown")),
                    "sha256": observed_sha256[:12] + "...",
                }])

            display(data_summary)
            """
        ),
        md(
            """
            ## 2-1. 전체 P2에서 선택한 ROI

            왼쪽은 전체 P2 좌표를 가볍게 downsample한 그림입니다. 주황색 박스가
            오늘 사용할 ROI입니다. 오른쪽은 그 ROI 안의 2 um bin을 counts로
            색칠한 그림입니다.
            """
        ),
        code(
            """
            with timed_stage("plot_selected_roi", STAGE_TIMES):
                roi_context_path = locate_or_download(
                    ROI_CONTEXT_FILE,
                    ROI_CONTEXT_URL,
                    sha256=ROI_CONTEXT_SHA256,
                )
                observed_context_sha256 = file_sha256(roi_context_path)

                roi_context = pd.read_csv(roi_context_path)
                full_points = roi_context[roi_context["kind"] == "full_p2_downsample"]
                roi_box = roi_context[roi_context["kind"] == "roi_bbox"]

                total_counts_2um = np.asarray(adata_2um.X.sum(axis=1)).ravel()
                roi_plot_idx = sample_indices(adata_2um.n_obs, max_points=120_000, seed=7)

                fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), constrained_layout=True)
                axes[0].scatter(full_points["x"], full_points["y"], s=0.3, c="#b8b8b8", rasterized=True)
                axes[0].plot(roi_box["x"], roi_box["y"], color="#d55e00", linewidth=1.8)
                axes[0].invert_yaxis()
                axes[0].set_aspect("equal")
                axes[0].set_title("Full P2 downsample + selected ROI")
                axes[0].set_xticks([])
                axes[0].set_yticks([])

                spatial_scatter(
                    axes[1],
                    coords_2um[roi_plot_idx],
                    values=np.log1p(total_counts_2um[roi_plot_idx]),
                    title="Selected ROI, log1p counts",
                    size=1,
                )
                plt.show()

                roi_summary = pd.DataFrame([{
                    "context_points": len(full_points),
                    "roi_x_min": float(roi_box["x"].min()),
                    "roi_x_max": float(roi_box["x"].max()),
                    "roi_y_min": float(roi_box["y"].min()),
                    "roi_y_max": float(roi_box["y"].max()),
                }])

            display(roi_summary)
            """
        ),
        md(
            """
            ## 2-2. 빠른 QC

            counts와 검출 gene 수 분포만 확인합니다. 오늘 목표는 QC 방법론이 아니라,
            같은 ROI에서 분석 질문이 어떻게 달라지는지 보는 것입니다.
            """
        ),
        code(
            """
            with timed_stage("quick_qc_2um", STAGE_TIMES):
                if sp.issparse(adata_2um.X):
                    detected_genes_2um = np.asarray((adata_2um.X > 0).sum(axis=1)).ravel()
                else:
                    detected_genes_2um = (adata_2um.X > 0).sum(axis=1)

                fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.2), constrained_layout=True)
                axes[0].hist(total_counts_2um, bins=50, color="#4c78a8")
                axes[0].set_title("UMI counts per 2 um bin")
                axes[1].hist(detected_genes_2um, bins=50, color="#59a14f")
                axes[1].set_title("Detected genes per 2 um bin")
                plt.show()

                qc_summary = pd.DataFrame([{
                    "median_counts": float(np.median(total_counts_2um)),
                    "median_detected_genes": float(np.median(detected_genes_2um)),
                    "max_counts": float(np.max(total_counts_2um)),
                }])

            display(qc_summary)
            """
        ),
    ]


def eight_um_cells() -> list:
    return [
        md(
            """
            ## 3. 8 um pseudobulk

            SVG, spatial domain, CCI는 8 um 단위로 진행합니다. 2 um bin 4 x 4개를
            같은 8 um bin으로 묶고 counts를 합산합니다. 이렇게 하면 공간 위치는
            유지하면서 표준 도구가 안정적으로 돌아갑니다.

            아래 helper는 `array_row`, `array_col`을 4로 나눈 grid를 만들고, 같은
            grid에 들어온 2 um bin들의 count를 합산합니다. 분석 도구가 아니라 실습용
            데이터 준비 함수입니다.
            """
        ),
        code(
            """
            with timed_stage("make_8um_pseudobulk", STAGE_TIMES):
                adata_8um = pseudobulk_visiumhd_2um_to_8um(adata_2um, coords_2um)
                coords_8um = np.asarray(adata_8um.obsm["spatial"], dtype=float)
                total_counts_8um = np.asarray(adata_8um.X.sum(axis=1)).ravel()

                pseudobulk_summary = adata_8um.obs["n_2um_bins"].describe().to_frame().T

            print(f"2 um: {adata_2um.n_obs:,} bins x {adata_2um.n_vars:,} genes")
            print(f"8 um: {adata_8um.n_obs:,} bins x {adata_8um.n_vars:,} genes")
            display(pseudobulk_summary)
            """
        ),
        md(
            """
            ## 3-1. 2 um와 8 um 비교

            왼쪽은 2 um ROI를 sampling해서 본 그림이고, 오른쪽은 같은 영역을 8 um
            bin으로 합친 그림입니다. 이후 표준 분석은 오른쪽 객체를 사용합니다.
            """
        ),
        code(
            """
            with timed_stage("plot_8um_pseudobulk", STAGE_TIMES):
                plot_2um_idx = sample_indices(adata_2um.n_obs, max_points=120_000, seed=7)

                fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), constrained_layout=True)
                spatial_scatter(
                    axes[0],
                    coords_2um[plot_2um_idx],
                    values=np.log1p(total_counts_2um[plot_2um_idx]),
                    title="2 um bins",
                    size=1,
                )
                spatial_scatter(
                    axes[1],
                    coords_8um,
                    values=np.log1p(total_counts_8um),
                    title="8 um pseudobulk",
                    size=3,
                )
                plt.show()
            """
        ),
        md(
            """
            ## 3-2. 표준 전처리

            8 um pseudobulk에 normalize, log transform, HVG, PCA를 적용합니다. HVG는
            뒤에서 SVG와 비교하기 위해 그대로 남겨둡니다.
            """
        ),
        code(
            """
            with timed_stage("preprocess_8um_for_standard_tools", STAGE_TIMES):
                analysis_adata = adata_8um.copy()
                HVG_N_TOP = int(os.environ.get("SPIX_WORKSHOP_HVG_N_TOP", "1200"))
                N_PCS = int(os.environ.get("SPIX_WORKSHOP_N_PCS", "30"))
                N_NEIGHBORS = int(os.environ.get("SPIX_WORKSHOP_N_NEIGHBORS", "25"))

                sc.pp.normalize_total(analysis_adata, target_sum=1e4)
                sc.pp.log1p(analysis_adata)
                analysis_adata.layers["log_norm"] = analysis_adata.X.copy()

                sc.pp.highly_variable_genes(
                    analysis_adata,
                    n_top_genes=min(HVG_N_TOP, analysis_adata.n_vars),
                    flavor="seurat",
                )

                sc.pp.pca(
                    analysis_adata,
                    n_comps=min(N_PCS, analysis_adata.n_obs - 1, analysis_adata.n_vars - 1),
                    mask_var="highly_variable",
                    svd_solver="arpack",
                    random_state=7,
                )

                sc.pp.neighbors(
                    analysis_adata,
                    n_neighbors=N_NEIGHBORS,
                    n_pcs=min(N_PCS, analysis_adata.obsm["X_pca"].shape[1]),
                    key_added="expression",
                    random_state=7,
                )

                sq.gr.spatial_neighbors(
                    analysis_adata,
                    spatial_key="spatial",
                    coord_type="generic",
                    n_neighs=6,
                    key_added="spatial",
                )

                sc.tl.leiden(
                    analysis_adata,
                    resolution=0.2,
                    neighbors_key="expression",
                    key_added="expression_leiden",
                    flavor="igraph",
                    n_iterations=2,
                    directed=False,
                    random_state=7,
                )

                analysis_coords = np.asarray(analysis_adata.obsm["spatial"], dtype=float)
                expression_cluster_summary = (
                    analysis_adata.obs["expression_leiden"]
                    .value_counts()
                    .sort_index()
                    .rename_axis("expression_leiden")
                    .reset_index(name="n_8um_bins")
                )

            print(f"analysis object: {analysis_adata.n_obs:,} bins x {analysis_adata.n_vars:,} genes")
            display(expression_cluster_summary)
            """
        ),
    ]


def svg_cells() -> list:
    return [
        md(
            """
            ## 4. SVG

            HVG는 sample 안에서 많이 변하는 gene입니다. 세포 상태나 cell type을
            볼 때 유용하지만, 그 변동이 조직 위에서 정리된 패턴인지까지는 말해주지
            않습니다.

            SVG는 질문이 조금 다릅니다. 같은 expression matrix를 보더라도 좌표를
            같이 사용해서, 가까운 bin들끼리 비슷하게 높거나 낮은 gene을 찾습니다.
            그래서 SVG는 spatial domain을 해석하거나, 특정 조직 구조를 설명할 marker
            후보를 잡을 때 먼저 보게 됩니다.

            여기서는 Squidpy의 Moran's I를 사용합니다. 값이 높을수록 해당 gene의
            발현이 무작위로 흩어진 것이 아니라, 공간적으로 모여 있는 경향이 강하다고
            해석합니다. HVG와 SVG가 많이 겹치지 않는다면, “변동이 큰 gene”과
            “조직 위에서 정리된 gene”이 서로 다를 수 있다는 뜻입니다.
            """
        ),
        code(
            """
            with timed_stage("svg_hvg_vs_moran", STAGE_TIMES):
                svg_genes = list(analysis_adata.var_names)
                svg_moran = sq.gr.spatial_autocorr(
                    analysis_adata,
                    genes=svg_genes,
                    mode="moran",
                    layer="log_norm",
                    n_perms=None,
                    n_jobs=N_JOBS,
                    backend="loky",
                    copy=True,
                    show_progress_bar=False,
                )

                svg_table = svg_moran.sort_values("I", ascending=False).copy()
                svg_table["gene"] = svg_table.index
                svg_table["svg_rank"] = np.arange(1, len(svg_table) + 1)

                hvg_table = analysis_adata.var[["means", "dispersions_norm", "highly_variable"]].copy()
                hvg_table["gene"] = hvg_table.index
                hvg_table = hvg_table.sort_values("dispersions_norm", ascending=False)
                hvg_table["hvg_rank"] = np.arange(1, len(hvg_table) + 1)

                top_hvg = hvg_table.head(20)[["hvg_rank", "gene", "dispersions_norm"]].reset_index(drop=True)
                top_svg = svg_table.head(20)[["svg_rank", "gene", "I"]].reset_index(drop=True)
                hvg_svg_comparison = pd.concat(
                    [
                        top_hvg.add_prefix("HVG_"),
                        top_svg.add_prefix("SVG_"),
                    ],
                    axis=1,
                )

                overlap_top100 = len(set(hvg_table.head(100)["gene"]) & set(svg_table.head(100)["gene"]))
                top_svg_genes = svg_table.head(6)["gene"].tolist()

            print(f"Top 100 HVG/SVG overlap: {overlap_top100} genes")
            display(hvg_svg_comparison)
            """
        ),
        md(
            """
            ## 4-1. SVG 공간 패턴

            표에서 끝내지 않고 실제 위치에 다시 그려 봅니다. 여기서 중요한 것은
            p-value나 rank만 보는 것이 아니라, 높은 rank의 gene이 조직 위에서 어떤
            모양으로 나타나는지 확인하는 것입니다.

            이 그림을 보고 나면 뒤의 spatial domain 결과를 해석할 때 “어떤 gene이
            어떤 영역을 설명하는가”라는 기준을 세울 수 있습니다.
            """
        ),
        code(
            """
            with timed_stage("svg_gene_maps", STAGE_TIMES):
                genes_to_plot = top_svg_genes[:4]
                expression_matrix = analysis_adata.layers["log_norm"]

                fig, axes = plt.subplots(
                    1,
                    len(genes_to_plot),
                    figsize=(4.0 * len(genes_to_plot), 3.8),
                    constrained_layout=True,
                )
                if len(genes_to_plot) == 1:
                    axes = [axes]

                for ax, gene in zip(axes, genes_to_plot):
                    gene_index = analysis_adata.var_names.get_loc(gene)
                    gene_values = sparse_vector(expression_matrix, gene_index)
                    spatial_scatter(
                        ax,
                        analysis_coords,
                        values=gene_values,
                        title=gene,
                        size=3,
                        cmap="magma",
                    )
                plt.show()
            """
        ),
    ]


def domain_cells() -> list:
    return [
        md(
            """
            ## 5. Spatial domain clustering

            여기서 말하는 clustering은 단순히 Leiden이나 k-means를 한 번 더 돌리는
            것이 아닙니다. 공간전사체에서 domain을 찾는다는 것은, 발현이 비슷한
            bin들이 실제 조직 위에서도 서로 붙어 있는지 같이 보는 작업입니다.

            그래서 먼저 expression-only 결과를 기준선으로 두고, 그 다음 spatial
            정보를 쓰는 도구들을 같은 panel에서 비교합니다. 같은 데이터를 넣어도
            방법마다 묻는 질문이 조금씩 다르기 때문에 결과가 완전히 같을 필요는
            없습니다.

            - Expression-only Leiden: 공간 정보를 쓰지 않는 비교 기준
            - Squidpy spatial graph: 좌표 인접성만으로 생기는 spatial block 확인
            - BANKSY: 주변 발현과 방향성 feature를 함께 쓰는 spatial domain 방법
            - BayesSpace: 인접 spot이 같은 domain일 가능성을 모델에 넣는 Bayesian 방법
            - SpaGCN: spatial graph convolution으로 발현과 위치를 함께 학습하는 방법

            모든 방법을 같은 정답에 맞추려는 것이 목표는 아닙니다. 같은 영역을
            안정적으로 잡는지, 특정 방법에서만 갈라지는 영역이 있는지, marker가
            해석 가능한지를 같이 보는 것이 더 중요합니다.
            """
        ),
        code(
            """
            with timed_stage("select_domain_panel", STAGE_TIMES):
                DOMAIN_MAX_OBS = int(os.environ.get("SPIX_WORKSHOP_DOMAIN_MAX_OBS", "3500"))
                domain_idx = center_nonzero_panel(
                    analysis_coords,
                    total_counts_8um,
                    max_obs=DOMAIN_MAX_OBS,
                )

                domain_adata = analysis_adata[domain_idx].copy()
                domain_coords = np.asarray(domain_adata.obsm["spatial"], dtype=float)
                DOMAIN_N_PCS = min(20, domain_adata.obsm["X_pca"].shape[1])
                domain_hvg_table = domain_adata.var[domain_adata.var["highly_variable"]].copy()
                domain_hvg_table = domain_hvg_table.sort_values("dispersions_norm", ascending=False)

            print(f"domain panel: {domain_adata.n_obs:,} nonzero 8 um bins x {domain_adata.n_vars:,} genes")
            """
        ),
        md(
            """
            ## 5-1. Expression-only baseline

            먼저 공간 정보를 쓰지 않는 결과를 만듭니다. 이 결과가 기준선입니다.
            이후 spatial tool의 결과가 이 기준선과 얼마나 달라지는지 보면, 각 도구가
            공간 정보를 어느 정도 강하게 반영했는지 감을 잡을 수 있습니다.
            """
        ),
        code(
            """
            with timed_stage("domain_expression_baseline", STAGE_TIMES):
                sc.pp.neighbors(
                    domain_adata,
                    n_neighbors=15,
                    use_rep="X_pca",
                    key_added="expression_domain_graph",
                    random_state=7,
                )
                sc.tl.leiden(
                    domain_adata,
                    resolution=0.35,
                    neighbors_key="expression_domain_graph",
                    key_added="expression_domain",
                    flavor="igraph",
                    n_iterations=2,
                    directed=False,
                    random_state=7,
                )

            print("clusters:", domain_adata.obs["expression_domain"].nunique())
            """
        ),
        md(
            """
            ## 5-2. Squidpy spatial graph

            Squidpy는 공간 좌표로 neighbor graph를 만들 수 있습니다. 여기서는 발현
            feature를 다시 보지 않고, 좌표상 가까운 bin끼리 연결된 graph 위에서
            Leiden을 돌립니다. 생물학적 annotation을 바로 주는 도구라기보다는,
            이 ROI가 공간적으로 어떤 block 구조를 갖는지 보는 기준입니다.
            """
        ),
        code(
            """
            with timed_stage("domain_squidpy_spatial_graph", STAGE_TIMES):
                sq.gr.spatial_neighbors(
                    domain_adata,
                    spatial_key="spatial",
                    coord_type="generic",
                    n_neighs=6,
                    key_added="squidpy_spatial",
                )
                sc.tl.leiden(
                    domain_adata,
                    adjacency=domain_adata.obsp["squidpy_spatial_connectivities"],
                    resolution=0.35,
                    key_added="squidpy_spatial_domain",
                    flavor="igraph",
                    n_iterations=2,
                    directed=False,
                    random_state=7,
                )

            print("clusters:", domain_adata.obs["squidpy_spatial_domain"].nunique())
            """
        ),
        md(
            """
            ## 5-3. BANKSY

            BANKSY는 각 bin의 발현만 보지 않고, 주변 bin의 평균 발현과 방향성
            정보를 feature에 함께 넣습니다. 그래서 작은 노이즈보다 주변 조직 문맥이
            더 중요할 때 domain이 더 안정적으로 잡히는지 확인할 수 있습니다.
            """
        ),
        code(
            """
            with timed_stage("domain_banksy", STAGE_TIMES):
                BANKSY_N_GENES = int(os.environ.get("SPIX_WORKSHOP_BANKSY_N_GENES", "800"))
                banksy_genes = domain_hvg_table.head(min(BANKSY_N_GENES, len(domain_hvg_table))).index.tolist()
                banksy_adata = domain_adata[:, banksy_genes].copy()
                if sp.issparse(banksy_adata.X):
                    gene_mean = np.asarray(banksy_adata.X.mean(axis=0)).ravel()
                    gene_mean2 = np.asarray(banksy_adata.X.power(2).mean(axis=0)).ravel()
                    keep_gene = (gene_mean2 - gene_mean**2) > 1e-8
                else:
                    keep_gene = np.var(np.asarray(banksy_adata.X), axis=0) > 1e-8
                banksy_adata = banksy_adata[:, keep_gene].copy()
                banksy_adata.obs["x"] = banksy_adata.obsm["spatial"][:, 0]
                banksy_adata.obs["y"] = banksy_adata.obsm["spatial"][:, 1]

                banksy_dict = initialize_banksy(
                    banksy_adata,
                    coord_keys=("x", "y", "spatial"),
                    num_neighbours=15,
                    nbr_weight_decay="scaled_gaussian",
                    max_m=1,
                    plt_edge_hist=False,
                    plt_nbr_weights=False,
                    plt_agf_angles=False,
                    plt_theta=False,
                )
                banksy_results = run_banksy_multiparam(
                    banksy_adata,
                    banksy_dict,
                    lambda_list=[0.8],
                    resolutions=[0.5],
                    color_list=["tab:blue"] * 256,
                    max_m=1,
                    filepath=str(OUTPUT_DIR / "banksy"),
                    key=("x", "y", "spatial"),
                    annotation_key=None,
                    savefig=False,
                    add_nonspatial=False,
                    pca_dims=[DOMAIN_N_PCS],
                    partition_seed=7,
                )
                banksy_label_obj = banksy_results.iloc[0]["labels"]
                if hasattr(banksy_label_obj, "dense"):
                    banksy_labels = np.asarray(banksy_label_obj.dense)
                else:
                    banksy_labels = np.asarray(banksy_label_obj)
                domain_adata.obs["banksy_domain"] = pd.Categorical(banksy_labels.astype(str))
                plt.close("all")

            print(f"BANKSY genes: {banksy_adata.n_vars:,}")
            print("clusters:", domain_adata.obs["banksy_domain"].nunique())
            """
        ),
        md(
            """
            ## 5-4. BayesSpace

            BayesSpace는 인접한 spot/bin이 같은 domain에 들어갈 가능성을 모델 안에
            넣는 방식입니다. 여기서는 8 um pseudobulk counts와 grid 좌표를 R
            BayesSpace에 넘기고, 결과 label만 다시 Python으로 읽어옵니다.

            실습에서는 시간을 줄이기 위해 MCMC 반복 수를 작게 둡니다. 논문용 분석에서
            BayesSpace를 정식으로 쓴다면 `q` 선택과 반복 수를 별도로 점검해야 합니다.

            BayesSpace는 입력 spot/bin의 count가 모두 있어야 안정적으로 동작합니다.
            그래서 HVG subset에서 zero-count bin이 생기면 전체 workshop gene set으로
            되돌린 뒤 실행합니다. 이 처리는 오류를 숨기기 위한 것이 아니라, 같은
            spatial panel을 유지하면서 BayesSpace 입력 조건을 맞추기 위한 것입니다.
            """
        ),
        code(
            """
            with timed_stage("domain_bayesspace", STAGE_TIMES):
                BAYESSPACE_N_GENES = int(os.environ.get("SPIX_WORKSHOP_BAYESSPACE_N_GENES", str(domain_adata.n_vars)))
                BAYESSPACE_Q = int(
                    os.environ.get(
                        "SPIX_WORKSHOP_BAYESSPACE_Q",
                        str(domain_adata.obs["expression_domain"].nunique()),
                    )
                )
                BAYESSPACE_D = int(os.environ.get("SPIX_WORKSHOP_BAYESSPACE_D", "15"))
                BAYESSPACE_NREP = int(os.environ.get("SPIX_WORKSHOP_BAYESSPACE_NREP", "200"))
                BAYESSPACE_BURNIN = int(os.environ.get("SPIX_WORKSHOP_BAYESSPACE_BURNIN", "50"))

                bayesspace_dir = OUTPUT_DIR / "bayesspace"
                bayesspace_dir.mkdir(parents=True, exist_ok=True)

                if BAYESSPACE_N_GENES >= domain_adata.n_vars:
                    bayesspace_genes = domain_adata.var_names.tolist()
                else:
                    bayesspace_genes = domain_hvg_table.head(
                        min(BAYESSPACE_N_GENES, len(domain_hvg_table))
                    ).index.tolist()
                bayesspace_raw = adata_8um[domain_idx, bayesspace_genes].copy()
                bayesspace_spot_counts = np.asarray(bayesspace_raw.X.sum(axis=1)).ravel()
                if np.any(bayesspace_spot_counts <= 0):
                    print("BayesSpace subset에 zero-count bin이 있어 전체 gene set으로 다시 준비합니다.")
                    bayesspace_genes = domain_adata.var_names.tolist()
                    bayesspace_raw = adata_8um[domain_idx, bayesspace_genes].copy()
                    bayesspace_spot_counts = np.asarray(bayesspace_raw.X.sum(axis=1)).ravel()
                assert np.all(bayesspace_spot_counts > 0), "BayesSpace 입력에 zero-count bin이 있습니다."
                counts_for_r = bayesspace_raw.X.T
                if sp.issparse(counts_for_r):
                    counts_for_r = counts_for_r.tocsc()
                else:
                    counts_for_r = sp.csc_matrix(counts_for_r)

                sio.mmwrite(bayesspace_dir / "counts.mtx", counts_for_r)
                pd.DataFrame({"gene": bayesspace_genes}).to_csv(
                    bayesspace_dir / "genes.csv",
                    index=False,
                )
                pd.DataFrame({
                    "barcode": bayesspace_raw.obs_names,
                    "array_row": bayesspace_raw.obs["array_row"].to_numpy(dtype=int),
                    "array_col": bayesspace_raw.obs["array_col"].to_numpy(dtype=int),
                }).to_csv(bayesspace_dir / "spots.csv", index=False)

                bayesspace_script = bayesspace_dir / "run_bayesspace.R"
                bayesspace_script.write_text(
                    '''
                    suppressPackageStartupMessages({
                      library(Matrix)
                      library(SingleCellExperiment)
                      library(BayesSpace)
                    })
                    args <- commandArgs(trailingOnly=TRUE)
                    input_dir <- args[[1]]
                    q <- as.integer(args[[2]])
                    d <- as.integer(args[[3]])
                    nrep <- as.integer(args[[4]])
                    burnin <- as.integer(args[[5]])

                    counts <- readMM(file.path(input_dir, "counts.mtx"))
                    genes <- read.csv(file.path(input_dir, "genes.csv"), stringsAsFactors=FALSE)$gene
                    spots <- read.csv(file.path(input_dir, "spots.csv"), stringsAsFactors=FALSE)

                    rownames(counts) <- make.unique(genes)
                    colnames(counts) <- spots$barcode
                    sce <- SingleCellExperiment(assays=list(counts=as(counts, "CsparseMatrix")))
                    colData(sce)$array_row <- as.integer(spots$array_row)
                    colData(sce)$array_col <- as.integer(spots$array_col)

                    set.seed(7)
                    sce <- spatialPreprocess(
                      sce,
                      platform="VisiumHD",
                      n.PCs=d,
                      n.HVGs=min(2000, nrow(sce)),
                      log.normalize=TRUE
                    )
                    set.seed(7)
                    sce <- spatialCluster(
                      sce,
                      q=q,
                      platform="VisiumHD",
                      d=d,
                      init.method="kmeans",
                      model="t",
                      gamma=2,
                      nrep=nrep,
                      burn.in=burnin,
                      save.chain=FALSE
                    )
                    out <- data.frame(
                      barcode=colnames(sce),
                      bayesspace_domain=as.character(colData(sce)$spatial.cluster)
                    )
                    write.csv(out, file.path(input_dir, "bayesspace_labels.csv"), row.names=FALSE)
                    '''
                )

                bayesspace_run = subprocess.run(
                    [
                        "Rscript",
                        str(bayesspace_script),
                        str(bayesspace_dir),
                        str(BAYESSPACE_Q),
                        str(BAYESSPACE_D),
                        str(BAYESSPACE_NREP),
                        str(BAYESSPACE_BURNIN),
                    ],
                    capture_output=True,
                    text=True,
                )
                bayesspace_log = (bayesspace_run.stdout + "\\n" + bayesspace_run.stderr).splitlines()
                print("\\n".join(bayesspace_log[-8:]))
                assert bayesspace_run.returncode == 0, "BayesSpace 실행이 실패했습니다."

                bayesspace_labels = pd.read_csv(
                    bayesspace_dir / "bayesspace_labels.csv"
                ).set_index("barcode")
                domain_adata.obs["bayesspace_domain"] = pd.Categorical(
                    bayesspace_labels.loc[domain_adata.obs_names, "bayesspace_domain"].astype(str).to_numpy()
                )

            print("q:", BAYESSPACE_Q)
            print("clusters:", domain_adata.obs["bayesspace_domain"].nunique())
            """
        ),
        md(
            """
            ## 5-5. SpaGCN

            SpaGCN은 spatial adjacency matrix를 만들고, graph convolution으로 발현
            정보와 위치 정보를 함께 반영합니다. 여기서는 histology image 없이 좌표만
            사용합니다. 같은 panel에서 돌려야 BANKSY, BayesSpace와 해석을 비교할
            수 있습니다.
            """
        ),
        code(
            """
            with timed_stage("domain_spagcn", STAGE_TIMES):
                spagcn_adata = domain_adata[:, domain_adata.var["highly_variable"].to_numpy()].copy()
                if sp.issparse(spagcn_adata.X):
                    spagcn_adata.X = spagcn_adata.X.toarray().astype(np.float32)

                spagcn_adj = SpaGCN.calculate_adj_matrix(
                    x=domain_coords[:, 0].tolist(),
                    y=domain_coords[:, 1].tolist(),
                    histology=False,
                )
                spagcn_l = SpaGCN.search_l(0.5, spagcn_adj, start=0.01, end=1000, tol=0.01, max_run=40)
                if spagcn_l is None:
                    positive_distances = spagcn_adj[spagcn_adj > 0]
                    spagcn_l = float(np.median(positive_distances))

                spagcn_model = SpaGCN.SpaGCN()
                spagcn_model.set_l(spagcn_l)
                spagcn_model.train(
                    spagcn_adata,
                    spagcn_adj,
                    num_pcs=min(30, spagcn_adata.n_vars - 1, spagcn_adata.n_obs - 1),
                    lr=0.01,
                    max_epochs=120,
                    init_spa=True,
                    init="louvain",
                    n_neighbors=10,
                    res=0.4,
                    tol=0.005,
                )
                spagcn_labels, spagcn_prob = spagcn_model.predict()
                domain_adata.obs["spagcn_domain"] = pd.Categorical(spagcn_labels.astype(str))

            print(f"SpaGCN l: {spagcn_l:.4f}")
            print("clusters:", domain_adata.obs["spagcn_domain"].nunique())
            """
        ),
        md(
            """
            ## 5-6. 결과를 표로 비교

            먼저 각 방법이 몇 개의 domain을 만들었는지 확인합니다. 그 다음 Adjusted
            Rand Index를 봅니다. ARI가 높다는 것은 두 방법이 비슷한 label을 냈다는
            뜻이고, 낮다는 것은 공간 정보를 반영하는 방식이 다르다는 뜻입니다.
            어느 쪽이 맞는지는 map과 marker를 같이 보고 판단해야 합니다.
            """
        ),
        code(
            """
            with timed_stage("summarize_spatial_domain_methods", STAGE_TIMES):
                domain_methods = {
                    "expression_domain": "Expression baseline",
                    "squidpy_spatial_domain": "Squidpy spatial graph",
                    "banksy_domain": "BANKSY",
                    "bayesspace_domain": "BayesSpace",
                    "spagcn_domain": "SpaGCN",
                }

                domain_count_table = make_domain_count_table(domain_adata, domain_methods)
                domain_ari_table = make_domain_ari_table(domain_adata, domain_methods)
                domain_count_table.to_csv(OUTPUT_DIR / "spatial_domain_counts.csv", index=False)
                domain_ari_table.to_csv(OUTPUT_DIR / "spatial_domain_ari.csv", index=False)

            display(domain_count_table)
            display(domain_ari_table)
            """
        ),
        md(
            """
            ## 5-7. Domain map 비교

            같은 8 um panel에서 결과를 나란히 봅니다. 좋은 결과는 cluster 개수가
            많다는 뜻이 아니라, 조직 구조와 marker 해석이 같이 맞는 결과입니다.
            """
        ),
        code(
            """
            with timed_stage("plot_spatial_domain_maps", STAGE_TIMES):
                fig, axes = plt.subplots(
                    1,
                    len(domain_methods),
                    figsize=(4.0 * len(domain_methods), 3.8),
                    constrained_layout=True,
                )
                for ax, (key, label) in zip(axes, domain_methods.items()):
                    codes = domain_adata.obs[key].astype("category").cat.codes.to_numpy()
                    spatial_scatter(
                        ax,
                        domain_coords,
                        values=codes,
                        title=label,
                        size=5,
                        cmap="tab20",
                    )
                plt.show()
            """
        ),
        md(
            """
            ## 5-8. Domain marker

            이후 CCI에서는 BANKSY domain을 사용합니다. 여기서는 각 domain의 marker를
            먼저 확인합니다.
            """
        ),
        code(
            """
            with timed_stage("banksy_domain_markers", STAGE_TIMES):
                sc.tl.rank_genes_groups(
                    domain_adata,
                    groupby="banksy_domain",
                    layer="log_norm",
                    use_raw=False,
                    method="t-test_overestim_var",
                    key_added="banksy_domain_markers",
                )
                marker_df = sc.get.rank_genes_groups_df(
                    domain_adata,
                    group=None,
                    key="banksy_domain_markers",
                )
                marker_df = marker_df.sort_values(["group", "scores"], ascending=[True, False])
                marker_df = marker_df.groupby("group", as_index=False).head(5)
                marker_df = marker_df[["group", "names", "scores", "logfoldchanges", "pvals_adj"]]

            display(marker_df)
            """
        ),
    ]


def cci_cells() -> list:
    return [
        md(
            """
            ## 6. Cell-cell interaction

            공간전사체에서 CCI를 볼 때의 장점은 순서가 분명하다는 것입니다. 먼저
            어떤 domain들이 실제로 서로 붙어 있는지 확인하고, 그 다음 그 접촉 관계를
            설명할 만한 ligand-receptor pair가 있는지 봅니다.

            발현만으로 ligand-receptor pair를 찾으면 멀리 떨어진 영역 사이의 신호도
            후보로 올라올 수 있습니다. 공간 정보를 같이 보면 “발현도 있고, 실제로
            가까이도 있는가”를 함께 확인할 수 있습니다.

            여기서는 두 단계를 분리합니다. 먼저 neighborhood enrichment로 어떤
            domain 쌍이 실제로 자주 붙어 있는지 보고, 그 다음 `ligrec` 결과에서
            그 접촉을 설명할 만한 ligand-receptor pair를 찾습니다.
            """
        ),
        code(
            """
            with timed_stage("cci_neighborhood_enrichment", STAGE_TIMES):
                CCI_CLUSTER_KEY = "banksy_domain"
                domain_adata.obs[CCI_CLUSTER_KEY] = domain_adata.obs[CCI_CLUSTER_KEY].astype("category")
                categories = domain_adata.obs[CCI_CLUSTER_KEY].cat.categories

                nhood_zscore, nhood_count = sq.gr.nhood_enrichment(
                    domain_adata,
                    cluster_key=CCI_CLUSTER_KEY,
                    n_perms=50,
                    numba_parallel=False,
                    seed=7,
                    copy=True,
                    n_jobs=N_JOBS,
                    backend="loky",
                    show_progress_bar=False,
                )

                nhood_zscore_df = pd.DataFrame(nhood_zscore, index=categories, columns=categories)
                nhood_count_df = pd.DataFrame(nhood_count, index=categories, columns=categories)

                fig, ax = plt.subplots(figsize=(5.2, 4.6))
                zscore_limit = np.nanmax(abs(nhood_zscore_df.to_numpy()))
                im = ax.imshow(nhood_zscore_df.to_numpy(), cmap="vlag", vmin=-zscore_limit, vmax=zscore_limit)
                ax.set_xticks(np.arange(len(categories)))
                ax.set_xticklabels(categories, rotation=45, ha="right")
                ax.set_yticks(np.arange(len(categories)))
                ax.set_yticklabels(categories)
                ax.set_title("Neighborhood enrichment z-score")
                fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                plt.show()

            display(nhood_zscore_df.round(2))
            """
        ),
        md(
            """
            ## 6-1. Ligand-receptor 후보 확인

            다음은 발현 기반 ligand-receptor 분석입니다. 실습 시간에는 전체 database를
            새로 받지 않고, colorectal tissue에서 해석하기 쉬운 후보 pair만 사용합니다.

            여기서 목표는 pair 수를 많이 뽑는 것이 아니라, 앞에서 본 domain 접촉
            구조와 LR 발현이 같은 방향으로 설명되는지 확인하는 것입니다.
            """
        ),
        code(
            """
            with timed_stage("cci_ligrec", STAGE_TIMES):
                LR_CANDIDATES = pd.DataFrame({
                    "source": ["SPP1", "MIF", "CD74", "COL1A1", "COL1A2", "FN1", "LAMB1", "JAG1", "APOE", "LGALS3", "TGFBI"],
                    "target": ["CD44", "CD74", "MIF", "ITGB1", "ITGB1", "ITGA5", "ITGB1", "NOTCH1", "LRP1", "ITGB1", "ITGB5"],
                })

                ligrec_interactions = LR_CANDIDATES[
                    LR_CANDIDATES["source"].isin(domain_adata.var_names)
                    & LR_CANDIDATES["target"].isin(domain_adata.var_names)
                ].copy()
                assert len(ligrec_interactions) > 0, "현재 gene set에서 사용할 수 있는 LR 후보가 없습니다."

                ligrec_result = sq.gr.ligrec(
                    domain_adata,
                    cluster_key=CCI_CLUSTER_KEY,
                    interactions=ligrec_interactions,
                    use_raw=False,
                    copy=True,
                    threshold=0.0,
                    n_perms=20,
                    n_jobs=N_JOBS,
                    numba_parallel=False,
                    seed=7,
                    corr_method=None,
                )

            display(ligrec_interactions)
            """
        ),
        md(
            """
            ## 6-2. LR 결과표

            mean expression이 크고 permutation p-value가 작은 조합을 위쪽에 둡니다.
            앞의 neighborhood enrichment와 같이 봐야 공간적 접촉과 발현 신호를
            함께 해석할 수 있습니다.
            """
        ),
        code(
            """
            with timed_stage("cci_ligrec_table", STAGE_TIMES):
                ligrec_table = tidy_ligrec_result(ligrec_result)
                ligrec_display = ligrec_table.head(20)

            display(ligrec_display)
            """
        ),
        md(
            """
            ## 6-3. 상위 LR pair heatmap

            가장 위에 있는 pair 하나를 domain 조합별로 펼쳐 봅니다.
            """
        ),
        code(
            """
            with timed_stage("cci_ligrec_heatmap", STAGE_TIMES):
                top_pair = ligrec_table.iloc[0]["pair"]
                pair_df = ligrec_table[ligrec_table["pair"] == top_pair].copy()
                heatmap_table = pair_df.pivot_table(
                    index="sender_cluster",
                    columns="receiver_cluster",
                    values="mean_expression",
                    aggfunc="mean",
                    fill_value=0,
                )

                fig, ax = plt.subplots(figsize=(5.6, 4.8))
                im = ax.imshow(heatmap_table.to_numpy(), cmap="magma")
                ax.set_xticks(np.arange(heatmap_table.shape[1]))
                ax.set_xticklabels(heatmap_table.columns, rotation=45, ha="right")
                ax.set_yticks(np.arange(heatmap_table.shape[0]))
                ax.set_yticklabels(heatmap_table.index)
                ax.set_title(f"{top_pair}: ligrec mean")
                fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                plt.show()

            display(heatmap_table)
            """
        ),
    ]


def spix_cells() -> list:
    return [
        md(
            """
            ## 7. SPIX

            마지막은 2 um ROI 전체를 그대로 사용합니다. 앞의 표준 도구들은 안정성을
            위해 8 um pseudobulk에서 돌렸지만, SPIX 파트는 2 um 정보를 버리지 않고
            여러 scale의 tissue unit으로 바꾸는 흐름을 보여줍니다.

            순서는 P2 재현 코드와 맞춰 `embedding -> smoothing -> equalization ->
            image cache -> multiscale segmentation -> scale별 SVG`로 둡니다.
            smoothing과 equalization은 직접 숫자를 찍어 넣지 않고 sweep으로 고릅니다.

            앞에서 8 um로 낮춘 이유는 표준 도구들이 안정적으로 돌아가게 하기 위한
            선택이었습니다. SPIX는 반대로 native 2 um 정보를 보존한 채 여러 scale의
            tissue unit을 만들기 때문에, 여기서는 1M개의 2 um bin 전체를 사용합니다.
            """
        ),
        code(
            """
            SPIX_EMBEDDING_DIMS = int(os.environ.get("SPIX_WORKSHOP_SPIX_EMBEDDING_DIMS", "30"))
            SPIX_EMBEDDING_CHANNELS = list(range(SPIX_EMBEDDING_DIMS))

            SPIX_RUN_TUNING = os.environ.get("SPIX_WORKSHOP_SPIX_RUN_TUNING", "1").lower()
            SPIX_RUN_TUNING = SPIX_RUN_TUNING in {"1", "true", "yes"}

            RESOLUTIONS_UM = [
                2, 8, 16, 30, 40, 50, 80, 100,
                150, 200, 250, 300, 350, 400, 450, 500,
            ]
            PITCH_UM = 2.0
            SPIX_MAX_WORKERS = int(os.environ.get("SPIX_WORKSHOP_SPIX_MAX_WORKERS", str(N_JOBS)))

            SEGMENT_DIR = OUTPUT_DIR / "spix_multiscale_segments"
            SPIX_CACHE_DIR = OUTPUT_DIR / "image_cache"
            SPIX_CACHE_NAMESPACE = "visiumhd_crc_p2_workshop_colab"

            print("embedding dims:", SPIX_EMBEDDING_DIMS)
            print("automatic smoothing/equalization sweep:", SPIX_RUN_TUNING)
            print("scales:", RESOLUTIONS_UM)
            """
        ),
        md(
            """
            ## 7-1. Embedding

            Count matrix를 log-normalized PCA embedding으로 바꿉니다. 여기서부터는
            2 um `adata_2um`을 복사해 `spix_adata`로 진행합니다.
            """
        ),
        code(
            """
            with timed_stage("spix_generate_embeddings", STAGE_TIMES):
                spix_adata = adata_2um.copy()
                spix_adata = SPIX.tm.generate_embeddings(
                    spix_adata,
                    dim_reduction="PCA",
                    normalization="log_norm",
                    n_jobs=N_JOBS,
                    dimensions=SPIX_EMBEDDING_DIMS,
                    nfeatures=min(2000, spix_adata.n_vars),
                    force=True,
                    use_coords_as_tiles=True,
                    coords_rescale_to_nn=False,
                    coords_max_gap_factor=None,
                    raster_random_seed=42,
                )

            print("X_embedding:", spix_adata.obsm["X_embedding"].shape)
            """
        ),
        md(
            """
            ## 7-2. Graph smoothing 자동 선택

            SPIX는 equalization 전에 embedding을 공간 graph 위에서 smoothing합니다.
            이 단계는 아주 작은 bin 단위의 노이즈를 줄이고, 주변 조직 문맥이
            segmentation에 반영되도록 만드는 과정입니다.

            여기서는 P2 재현 코드와 같은 grid를 두고 추천값을 고릅니다. 시간이 부족한
            예행연습에서는 `SPIX_WORKSHOP_SPIX_RUN_TUNING=0`으로 끌 수 있습니다.
            """
        ),
        code(
            """
            with timed_stage("spix_smoothing_selection", STAGE_TIMES):
                if SPIX_RUN_TUNING:
                    smoothing_selection = SPIX.ip.evaluate_smoothing_sweep(
                        spix_adata,
                        embedding="X_embedding",
                        methods=["graph"],
                        approx_mode="grid",
                        approx_target_n=2_000_000,
                        approx_max_bins=2_000_000,
                        graph_k_grid=[1, 3, 5, 10, 15, 20, 25, 30],
                        graph_t_grid=[1, 2, 3, 4, 6, 8, 10, 30, 50],
                        candidate_jobs=N_JOBS,
                        verbose=True,
                    )
                    smooth_params = dict(smoothing_selection["recommendation"]["params"])
                else:
                    smooth_params = {"graph_k": 20, "graph_t": 10}
                    smoothing_selection = {
                        "recommendation": {
                            "params": smooth_params,
                            "source": "manual fallback for rehearsal only",
                        }
                    }

                (OUTPUT_DIR / "spix_smoothing_selection.json").write_text(
                    json.dumps(smoothing_selection, indent=2, default=str)
                )

            print(smooth_params)
            """
        ),
        code(
            """
            with timed_stage("spix_smooth_image", STAGE_TIMES):
                spix_adata = SPIX.ip.smooth_image(
                    spix_adata,
                    methods=["graph"],
                    embedding="X_embedding",
                    embedding_dims=SPIX_EMBEDDING_CHANNELS,
                    output="X_embedding_smooth",
                    approx_mode="grid",
                    approx_target_n=2_000_000,
                    approx_max_bins=2_000_000,
                    graph_k=int(smooth_params["graph_k"]),
                    graph_t=int(smooth_params["graph_t"]),
                    n_jobs=N_JOBS,
                    backend="threads",
                    implementation="auto",
                    rescale_mode="final",
                )

            print("X_embedding_smooth:", spix_adata.obsm["X_embedding_smooth"].shape)
            """
        ),
        md(
            """
            ## 7-3. Equalization 자동 선택과 image cache

            smoothing된 embedding을 SLIC 계열 segmentation이 쓰기 좋은 multichannel
            image로 바꿉니다. equalization은 channel별 contrast가 너무 약하거나
            너무 강해지는 것을 막기 위한 단계입니다. 이 값도 sweep으로 고릅니다.
            """
        ),
        code(
            """
            with timed_stage("spix_equalization_selection", STAGE_TIMES):
                if SPIX_RUN_TUNING:
                    equalization_selection = SPIX.ip.evaluate_equalization_sweep(
                        spix_adata,
                        embedding="X_embedding_smooth",
                        dimensions=SPIX_EMBEDDING_CHANNELS,
                        methods=["BalanceSimplest"],
                        sleft_grid=[0.1, 0.2, 0.3, 0.4, 0.5, 0.8, 1.0, 1.5, 2.0, 3, 4, 5],
                        sright_grid=[0.1, 0.2, 0.3, 0.4, 0.5, 0.8, 1.0, 1.5, 2.0, 3, 4, 5],
                        n_jobs=N_JOBS,
                        verbose=True,
                    )
                    equalization_params = dict(equalization_selection["best"])
                else:
                    equalization_params = {"sleft": 2.0, "sright": 2.0}
                    equalization_selection = {
                        "best": equalization_params,
                        "source": "manual fallback for rehearsal only",
                    }

                (OUTPUT_DIR / "spix_equalization_selection.json").write_text(
                    json.dumps(equalization_selection, indent=2, default=str)
                )

            print(equalization_params)
            """
        ),
        code(
            """
            with timed_stage("spix_equalize_and_cache_image", STAGE_TIMES):
                spix_adata = SPIX.ip.equalize_image(
                    spix_adata,
                    dimensions=SPIX_EMBEDDING_CHANNELS,
                    embedding="X_embedding_smooth",
                    sleft=float(equalization_params["sleft"]),
                    sright=float(equalization_params["sright"]),
                )

                SPIX.ip.cache_embedding_image(
                    spix_adata,
                    embedding="X_embedding_equalize",
                    dimensions=SPIX_EMBEDDING_CHANNELS,
                    key="image_plot_slic",
                    brighten_continuous=True,
                    continuous_gamma=0.7,
                    origin=True,
                    store="memmap",
                    memmap_dir=str(SPIX_CACHE_DIR),
                    cache_namespace=SPIX_CACHE_NAMESPACE,
                    show=False,
                    verbose=True,
                )

            print("image cache key: image_plot_slic")
            """
        ),
        md(
            """
            ## 7-4. Multiscale segmentation

            compactness를 하나로 고정하지 않고 후보값을 넘깁니다. SPIX가 각 scale에서
            요청한 크기에 맞는 segmentation을 고릅니다.
            """
        ),
        code(
            """
            with timed_stage("spix_multiscale_segmentation", STAGE_TIMES):
                segment_index = SPIX.sp.precompute_multiscale_segments(
                    spix_adata,
                    resolutions=RESOLUTIONS_UM,
                    compactness_candidates=[0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.5],
                    dimensions=SPIX_EMBEDDING_CHANNELS,
                    embedding="X_embedding_equalize",
                    out_dir=str(SEGMENT_DIR),
                    pitch_um=PITCH_UM,
                    max_workers=SPIX_MAX_WORKERS,
                    cache_kwargs={
                        "runtime_fill_from_boundary": True,
                        "runtime_fill_closing_radius": 1,
                        "runtime_fill_holes": True,
                        "origin": True,
                        "store": "memmap",
                        "memmap_dir": str(SPIX_CACHE_DIR),
                        "cache_namespace": SPIX_CACHE_NAMESPACE,
                        "brighten_continuous": True,
                        "continuous_gamma": 0.7,
                    },
                    verbose=True,
                )
                segment_index = pd.read_csv(SEGMENT_DIR / "segments_index.csv")

            display(segment_index[[
                "scale_id",
                "resolution",
                "requested_n_segments",
                "observed_obs_n_segments",
                "seconds",
            ]])
            """
        ),
        md(
            """
            ## 7-5. SPIX scale별 SVG

            같은 gene이라도 2 um bin에서 볼 때와 100 um tissue unit에서 볼 때의
            공간성이 달라질 수 있습니다. 이 셀은 scale별 Moran rank를 계산합니다.
            """
        ),
        code(
            """
            with timed_stage("spix_multiscale_moran_svg", STAGE_TIMES):
                spix_rank_df, spix_score_df = SPIX.an.multiscale_moran_ranks(
                    spix_adata,
                    segments_index_csv=str(SEGMENT_DIR / "segments_index.csv"),
                    out_csv=str(SEGMENT_DIR / "multiscale_moran_ranks.csv"),
                    out_score_csv=str(SEGMENT_DIR / "multiscale_moran_scores.csv"),
                    engine="fast",
                    backend="threads",
                    n_jobs=N_JOBS,
                    threads_per_process=1,
                    moran_thresh=-1.0,
                    return_scores=True,
                    quiet=False,
                )
                spix_top_svg_table = top_rank_table(spix_rank_df, top_n=5)

            display(spix_top_svg_table)
            """
        ),
        md(
            """
            ## 7-6. 대표 scale map

            50, 100, 500 um scale을 먼저 확인합니다. 필요하면
            `SPIX_WORKSHOP_SPIX_PLOT_SCALES_UM` 값을 바꾸면 됩니다.
            """
        ),
        code(
            """
            with timed_stage("spix_add_segment_labels", STAGE_TIMES):
                add_segment_labels(spix_adata, segment_index, SEGMENT_DIR, prefix="spix_")
            """
        ),
        code(
            """
            with timed_stage("spix_scale_overview", STAGE_TIMES):
                plot_scales_um = os.environ.get("SPIX_WORKSHOP_SPIX_PLOT_SCALES_UM", "50,100,500")
                plot_scales_um = [float(x.strip()) for x in plot_scales_um.split(",") if x.strip()]
                plot_segment_index = segment_index[
                    segment_index["resolution"].astype(float).isin(plot_scales_um)
                ].copy()

                if plot_segment_index.empty:
                    non_native = segment_index["native_identity"].astype(str).str.lower() != "true"
                    plot_segment_index = segment_index[non_native].head(3).copy()

                spix_plot_idx = sample_indices(spix_adata.n_obs, max_points=140_000, seed=7)

                fig, axes = plt.subplots(
                    1,
                    len(plot_segment_index),
                    figsize=(4.2 * len(plot_segment_index), 3.8),
                    constrained_layout=True,
                )
                if len(plot_segment_index) == 1:
                    axes = [axes]

                for ax, (_, row) in zip(axes, plot_segment_index.iterrows()):
                    obs_key = f"spix_{row['scale_id']}"
                    color_codes = spix_adata.obs[obs_key].cat.codes.to_numpy()
                    spatial_scatter(
                        ax,
                        coords_2um[spix_plot_idx],
                        values=color_codes[spix_plot_idx],
                        title=f"{row['scale_id']} / {int(row['observed_obs_n_segments'])} units",
                        size=1.5,
                        cmap="tab20",
                    )
                plt.show()

                spix_scale_summary = segment_index[[
                    "scale_id",
                    "resolution",
                    "observed_obs_n_segments",
                ]].copy()
                spix_scale_summary["mean_2um_bins_per_unit"] = (
                    spix_adata.n_obs / spix_scale_summary["observed_obs_n_segments"]
                )

            display(spix_scale_summary)
            """
        ),
    ]


def final_cells() -> list:
    return [
        md(
            """
            ## 8. 실행 시간 저장

            Colab에서 실행한 뒤 이 JSON을 보관하면 실제 무료 티어 시간을 확인할 수
            있습니다.
            """
        ),
        code(
            """
            with timed_stage("final_report", STAGE_TIMES):
                runtime_info = runtime_snapshot(N_JOBS)
                elapsed = round(time.perf_counter() - RUN_STARTED_AT, 2)
                report = {
                    "lecture_id": LECTURE_ID,
                    "topic": "SVG, spatial domain clustering, cell-cell interaction, SPIX",
                    "validation_passed": True,
                    "elapsed_seconds": elapsed,
                    "runtime": runtime_info,
                    "data_file": str(data_path),
                    "roi_context_file": str(roi_context_path),
                    "data_shape_2um": [int(adata_2um.n_obs), int(adata_2um.n_vars)],
                    "data_shape_8um": [int(adata_8um.n_obs), int(adata_8um.n_vars)],
                    "spatial_domain_panel_shape": [int(domain_adata.n_obs), int(domain_adata.n_vars)],
                    "spatial_domain_methods": list(domain_methods.values()),
                    "spix_shape": [int(spix_adata.n_obs), int(spix_adata.n_vars)],
                    "stage_times": STAGE_TIMES,
                    "outputs": {
                        "output_dir": str(OUTPUT_DIR),
                        "spatial_domain_counts": str(OUTPUT_DIR / "spatial_domain_counts.csv"),
                        "spatial_domain_ari": str(OUTPUT_DIR / "spatial_domain_ari.csv"),
                        "bayesspace_labels": str(OUTPUT_DIR / "bayesspace" / "bayesspace_labels.csv"),
                        "smoothing_selection": str(OUTPUT_DIR / "spix_smoothing_selection.json"),
                        "equalization_selection": str(OUTPUT_DIR / "spix_equalization_selection.json"),
                        "segments_index": str(SEGMENT_DIR / "segments_index.csv"),
                        "spix_moran_ranks": str(SEGMENT_DIR / "multiscale_moran_ranks.csv"),
                        "spix_moran_scores": str(SEGMENT_DIR / "multiscale_moran_scores.csv"),
                    },
                }

                report_path = OUTPUT_DIR / f"{LECTURE_ID}_timing_report.json"
                report_path.write_text(json.dumps(report, indent=2, sort_keys=True))

                print("Validation passed")
                print("Report:", report_path)
                print(json.dumps(report, indent=2, ensure_ascii=False)[:2000])

            if IN_COLAB:
                try:
                    from google.colab import files
                    files.download(str(report_path))
                except Exception as exc:
                    print("자동 다운로드를 건너뜁니다:", exc)
            """
        ),
    ]


def combined_notebook(
    data_url: str,
    data_sha256: str,
    roi_context_url: str,
    roi_context_sha256: str,
    helper_url: str,
):
    nb = new_notebook(COMBINED_NOTEBOOK)
    nb["cells"] = [
        md(
            """
            # 공간전사체 분석 실습: SVG, spatial domain, CCI, SPIX

            오늘 실습은 같은 Visium HD P2 ROI를 계속 사용합니다. 데이터를 바꾸지
            않고 질문만 바꾸면, 각 분석이 어떤 역할을 하는지 훨씬 분명하게 보입니다.

            1. **SVG**: 공간적으로 정리된 gene은 무엇인가?
            2. **Spatial domain**: 조직 영역은 어떻게 나눌 수 있는가?
            3. **CCI**: 서로 붙어 있는 영역 사이에 어떤 ligand-receptor 신호가 보이는가?
            4. **SPIX**: 2 um 정보를 여러 scale의 tissue unit으로 어떻게 바꿀 수 있는가?

            앞의 세 파트는 8 um pseudobulk에서 안정적으로 진행하고, 마지막 SPIX
            파트는 2 um ROI 전체를 사용합니다.

            코드는 한 셀에서 한 가지 일만 하도록 나누었습니다. 수업 중에는 표와
            그림을 먼저 보고, 필요할 때만 코드 안의 파라미터를 확인하면 됩니다.
            """
        ),
        md(
            """
            ## 입력 자료

            원본 P2는 2 um bin이 약 8.7M개입니다. 여기서는 그중 하나의 ROI를
            사용합니다. 일반 분석은 8 um pseudobulk로 진행하고, SPIX는 2 um ROI
            전체를 사용합니다.

            실습에서 중요한 것은 “가장 큰 데이터”를 억지로 Colab에 올리는 것이
            아니라, 같은 ROI에서 표준 공간 분석과 SPIX의 multiscale 분석이 어떻게
            이어지는지 끝까지 확인하는 것입니다.

            8M full section은 reference run으로 따로 보는 것이 맞고, 여기서는
            무료 Colab에서 끝까지 완주할 수 있는 크기로 ROI를 잡았습니다.
            """
        ),
    ]
    nb["cells"].extend(
        setup_cells(data_url, data_sha256, roi_context_url, roi_context_sha256, helper_url)
    )
    nb["cells"].extend(data_cells())
    nb["cells"].extend(eight_um_cells())
    nb["cells"].extend(svg_cells())
    nb["cells"].extend(domain_cells())
    nb["cells"].extend(cci_cells())
    nb["cells"].extend(spix_cells())
    nb["cells"].extend(final_cells())
    return COMBINED_NOTEBOOK, nb


def write_notebook(path: Path, nb) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if nbf is not None:
        nbf.write(nb, path)
    else:
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook-dir", default=DEFAULT_NOTEBOOK_DIR)
    parser.add_argument("--data-file", default=f"data/{DATA_FILE}")
    parser.add_argument("--data-url", default=DEFAULT_DATA_URL)
    parser.add_argument("--roi-context-file", default=f"data/{ROI_CONTEXT_FILE}")
    parser.add_argument("--roi-context-url", default=DEFAULT_ROI_CONTEXT_URL)
    parser.add_argument("--helper-url", default=DEFAULT_HELPER_URL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data_file)
    data_sha256 = sha256sum(data_path) if data_path.exists() else ""
    roi_context_path = Path(args.roi_context_file)
    roi_context_sha256 = sha256sum(roi_context_path) if roi_context_path.exists() else ""
    notebook_dir = Path(args.notebook_dir)

    name, nb = combined_notebook(
        args.data_url,
        data_sha256,
        args.roi_context_url,
        roi_context_sha256,
        args.helper_url,
    )
    write_notebook(notebook_dir / name, nb)

    print(
        json.dumps(
            {
                "written": [str(notebook_dir / name)],
                "data_sha256": data_sha256,
                "roi_context_sha256": roi_context_sha256,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
