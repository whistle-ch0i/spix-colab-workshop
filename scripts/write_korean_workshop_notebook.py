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


DATA_FILE = "visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad"
ROI_CONTEXT_FILE = "visiumhd_p2_roi_context_downsample.csv"
DEFAULT_DATA_URL = (
    "https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/"
    f"data/{DATA_FILE}"
)
DEFAULT_ROI_CONTEXT_URL = (
    "https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/"
    f"data/{ROI_CONTEXT_FILE}"
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
) -> list:
    setup_code = """
    import os
    import sys
    import json
    import time
    import shutil
    import hashlib
    import platform
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

    OUTPUT_DIR = Path("spix_korean_lecture_outputs") / LECTURE_ID
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    IN_COLAB = "google.colab" in sys.modules or "COLAB_RELEASE_TAG" in os.environ
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")

    meminfo = {}
    if Path("/proc/meminfo").exists():
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}:
                meminfo[key] = round(float(value.strip().split()[0]) / 1024 / 1024, 2)

    disk = shutil.disk_usage(Path.cwd())
    runtime_info = {
        "running_in_colab": bool(IN_COLAB),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "thread_cap": N_JOBS,
        "memory_gb": meminfo,
        "cwd": str(Path.cwd().resolve()),
        "disk_free_gb": round(disk.free / 1024**3, 2),
    }

    print(json.dumps(runtime_info, indent=2, ensure_ascii=False))
    """
    setup_code = (
        setup_code.replace("__DATA_FILE__", json.dumps(DATA_FILE))
        .replace("__DATA_URL__", json.dumps(data_url))
        .replace("__DATA_SHA256__", json.dumps(data_sha256))
        .replace("__ROI_CONTEXT_FILE__", json.dumps(ROI_CONTEXT_FILE))
        .replace("__ROI_CONTEXT_URL__", json.dumps(roi_context_url))
        .replace("__ROI_CONTEXT_SHA256__", json.dumps(roi_context_sha256))
    )

    return [
        md(
            """
            ## 0. 실행 환경

            먼저 지금 할당된 Colab runtime을 확인합니다. 실습 기본값은 CPU runtime,
            `N_JOBS=2`입니다. 시간이 충분하고 runtime이 넉넉하면 `N_JOBS`만 조금
            올리면 됩니다.
            """
        ),
        code(setup_code),
        md(
            """
            ## 1. 패키지 준비

            Colab에서 없는 패키지는 여기서 설치합니다. 로컬에서 실행할 때는 현재
            workspace에 있는 SPIX checkout을 먼저 사용합니다.
            """
        ),
        code(
            """
            stage = "import_or_install"
            start = time.perf_counter()

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
                "anndata": "anndata",
            }
            missing = [pip_name for module, pip_name in needed.items() if importlib.util.find_spec(module) is None]
            if missing:
                if not IN_COLAB:
                    raise ImportError(f"설치되지 않은 패키지: {missing}")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            stage = "patch_spix_optional_imports"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            stage = "import_analysis_packages"
            start = time.perf_counter()

            import anndata as ad
            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd
            import scanpy as sc
            import scipy.sparse as sp
            import squidpy as sq
            import SpaGCN
            from IPython.display import display
            from sklearn.metrics import adjusted_rand_score
            import SPIX

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print("Scanpy:", sc.__version__)
            print("Squidpy:", sq.__version__)
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
            stage = "load_2um_data"
            start = time.perf_counter()

            data_file_name = Path(DATA_FILE).name
            candidate_paths = [
                Path(DATA_FILE).expanduser(),
                Path("data") / data_file_name,
                Path("..") / "data" / data_file_name,
                Path.cwd() / "data" / data_file_name,
                Path("/content") / data_file_name,
            ]

            data_path = None
            for candidate in candidate_paths:
                if candidate.exists():
                    data_path = candidate.resolve()
                    break

            if data_path is None:
                data_path = Path("/content" if IN_COLAB else ".") / data_file_name
                print("Downloading:", DATA_URL)
                urllib.request.urlretrieve(DATA_URL, data_path)
                data_path = data_path.resolve()

            file_hash = hashlib.sha256()
            with data_path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    file_hash.update(chunk)
            observed_sha256 = file_hash.hexdigest()
            if DATA_SHA256:
                assert observed_sha256 == DATA_SHA256, f"Data SHA-256 mismatch: {observed_sha256}"

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            stage = "plot_selected_roi"
            start = time.perf_counter()

            context_file_name = Path(ROI_CONTEXT_FILE).name
            context_candidates = [
                Path(ROI_CONTEXT_FILE).expanduser(),
                Path("data") / context_file_name,
                Path("..") / "data" / context_file_name,
                Path.cwd() / "data" / context_file_name,
                Path("/content") / context_file_name,
            ]

            roi_context_path = None
            for candidate in context_candidates:
                if candidate.exists():
                    roi_context_path = candidate.resolve()
                    break

            if roi_context_path is None:
                roi_context_path = Path("/content" if IN_COLAB else ".") / context_file_name
                print("Downloading:", ROI_CONTEXT_URL)
                urllib.request.urlretrieve(ROI_CONTEXT_URL, roi_context_path)
                roi_context_path = roi_context_path.resolve()

            context_hash = hashlib.sha256()
            with roi_context_path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    context_hash.update(chunk)
            observed_context_sha256 = context_hash.hexdigest()
            if ROI_CONTEXT_SHA256:
                assert observed_context_sha256 == ROI_CONTEXT_SHA256, (
                    f"ROI context SHA-256 mismatch: {observed_context_sha256}"
                )

            roi_context = pd.read_csv(roi_context_path)
            full_points = roi_context[roi_context["kind"] == "full_p2_downsample"]
            roi_box = roi_context[roi_context["kind"] == "roi_bbox"]

            total_counts_2um = np.asarray(adata_2um.X.sum(axis=1)).ravel()
            rng = np.random.default_rng(7)
            if adata_2um.n_obs > 120000:
                roi_plot_idx = np.sort(rng.choice(adata_2um.n_obs, size=120000, replace=False))
            else:
                roi_plot_idx = np.arange(adata_2um.n_obs)

            fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), constrained_layout=True)
            axes[0].scatter(full_points["x"], full_points["y"], s=0.3, c="#b8b8b8", rasterized=True)
            axes[0].plot(roi_box["x"], roi_box["y"], color="#d55e00", linewidth=1.8)
            axes[0].invert_yaxis()
            axes[0].set_aspect("equal")
            axes[0].set_title("Full P2 downsample + selected ROI")
            axes[0].set_xticks([])
            axes[0].set_yticks([])

            axes[1].scatter(
                coords_2um[roi_plot_idx, 0],
                coords_2um[roi_plot_idx, 1],
                s=1,
                c=np.log1p(total_counts_2um[roi_plot_idx]),
                cmap="viridis",
                rasterized=True,
            )
            axes[1].invert_yaxis()
            axes[1].set_aspect("equal")
            axes[1].set_title("Selected ROI, log1p counts")
            axes[1].set_xticks([])
            axes[1].set_yticks([])
            plt.show()

            roi_summary = pd.DataFrame([{
                "context_points": len(full_points),
                "roi_x_min": float(roi_box["x"].min()),
                "roi_x_max": float(roi_box["x"].max()),
                "roi_y_min": float(roi_box["y"].min()),
                "roi_y_max": float(roi_box["y"].max()),
            }])

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            stage = "quick_qc_2um"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            """
        ),
        code(
            """
            stage = "make_8um_pseudobulk"
            start = time.perf_counter()

            row_8um = (adata_2um.obs["array_row"].to_numpy(dtype=int) // 4)
            col_8um = (adata_2um.obs["array_col"].to_numpy(dtype=int) // 4)
            group_labels = pd.Series(row_8um.astype(str) + "_" + col_8um.astype(str))
            group_codes, group_names = pd.factorize(group_labels, sort=True)
            n_groups = len(group_names)

            aggregation = sp.csr_matrix(
                (
                    np.ones(adata_2um.n_obs, dtype=np.float32),
                    (group_codes, np.arange(adata_2um.n_obs)),
                ),
                shape=(n_groups, adata_2um.n_obs),
            )

            X_8um = aggregation @ adata_2um.X
            if not sp.issparse(X_8um):
                X_8um = sp.csr_matrix(X_8um)

            bins_per_8um = np.asarray(aggregation.sum(axis=1)).ravel()
            mean_x = np.asarray(aggregation @ coords_2um[:, 0]).ravel() / bins_per_8um
            mean_y = np.asarray(aggregation @ coords_2um[:, 1]).ravel() / bins_per_8um
            mean_array_row = np.asarray(
                aggregation @ adata_2um.obs["array_row"].to_numpy(dtype=float)
            ).ravel() / bins_per_8um
            mean_array_col = np.asarray(
                aggregation @ adata_2um.obs["array_col"].to_numpy(dtype=float)
            ).ravel() / bins_per_8um

            obs_8um = pd.DataFrame(index=[f"bin8_{name}" for name in group_names])
            obs_8um["n_2um_bins"] = bins_per_8um.astype(int)
            obs_8um["array_row"] = mean_array_row
            obs_8um["array_col"] = mean_array_col

            adata_8um = ad.AnnData(X=X_8um.tocsr(), obs=obs_8um, var=adata_2um.var.copy())
            adata_8um.var_names = adata_2um.var_names.copy()
            adata_8um.var_names_make_unique()
            adata_8um.obsm["spatial"] = np.column_stack([mean_x, mean_y]).astype(np.float32)
            adata_8um.uns["pseudobulk"] = {"source_bin_um": 2, "target_bin_um": 8, "rule": "4x4 sum"}

            coords_8um = np.asarray(adata_8um.obsm["spatial"], dtype=float)
            total_counts_8um = np.asarray(adata_8um.X.sum(axis=1)).ravel()

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print(f"2 um: {adata_2um.n_obs:,} bins x {adata_2um.n_vars:,} genes")
            print(f"8 um: {adata_8um.n_obs:,} bins x {adata_8um.n_vars:,} genes")
            display(obs_8um['n_2um_bins'].describe().to_frame().T)
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
            stage = "plot_8um_pseudobulk"
            start = time.perf_counter()

            rng = np.random.default_rng(7)
            if adata_2um.n_obs > 120000:
                plot_2um_idx = np.sort(rng.choice(adata_2um.n_obs, size=120000, replace=False))
            else:
                plot_2um_idx = np.arange(adata_2um.n_obs)

            fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), constrained_layout=True)
            axes[0].scatter(
                coords_2um[plot_2um_idx, 0],
                coords_2um[plot_2um_idx, 1],
                s=1,
                c=np.log1p(total_counts_2um[plot_2um_idx]),
                cmap="viridis",
                rasterized=True,
            )
            axes[0].invert_yaxis()
            axes[0].set_aspect("equal")
            axes[0].set_title("2 um bins")
            axes[0].set_xticks([])
            axes[0].set_yticks([])

            axes[1].scatter(
                coords_8um[:, 0],
                coords_8um[:, 1],
                s=3,
                c=np.log1p(total_counts_8um),
                cmap="viridis",
                rasterized=True,
            )
            axes[1].invert_yaxis()
            axes[1].set_aspect("equal")
            axes[1].set_title("8 um pseudobulk")
            axes[1].set_xticks([])
            axes[1].set_yticks([])
            plt.show()

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            stage = "preprocess_8um_for_standard_tools"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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

            HVG는 sample 안에서 많이 변하는 gene입니다. 하지만 그 변동이 조직 위에서
            정리되어 있는지는 보지 않습니다. SVG는 같은 expression matrix에 공간
            좌표를 같이 넣고, 주변 bin끼리 비슷한 패턴을 보이는 gene을 찾습니다.
            """
        ),
        code(
            """
            stage = "svg_hvg_vs_moran"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print(f"Top 100 HVG/SVG overlap: {overlap_top100} genes")
            display(hvg_svg_comparison)
            """
        ),
        md(
            """
            ## 4-1. SVG 공간 패턴

            표에서 끝내지 않고 실제 위치에 다시 그려 봅니다. SVG가 유용한 이유는
            rank가 높은 gene이 어느 조직 영역에서 올라오는지 바로 확인할 수 있기
            때문입니다.
            """
        ),
        code(
            """
            stage = "svg_gene_maps"
            start = time.perf_counter()

            genes_to_plot = top_svg_genes[:4]
            expression_matrix = analysis_adata.layers["log_norm"]

            fig, axes = plt.subplots(1, len(genes_to_plot), figsize=(4.0 * len(genes_to_plot), 3.8), constrained_layout=True)
            if len(genes_to_plot) == 1:
                axes = [axes]

            for ax, gene in zip(axes, genes_to_plot):
                gene_index = analysis_adata.var_names.get_loc(gene)
                gene_values = expression_matrix[:, gene_index]
                if sp.issparse(gene_values):
                    gene_values = gene_values.toarray()
                gene_values = np.asarray(gene_values).ravel()

                ax.scatter(
                    analysis_coords[:, 0],
                    analysis_coords[:, 1],
                    s=3,
                    c=gene_values,
                    cmap="magma",
                    rasterized=True,
                )
                ax.invert_yaxis()
                ax.set_aspect("equal")
                ax.set_title(gene)
                ax.set_xticks([])
                ax.set_yticks([])
            plt.show()

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            """
        ),
    ]


def domain_cells() -> list:
    return [
        md(
            """
            ## 5. Spatial domain clustering

            여기서 목표는 단순히 Leiden이나 k-means를 실행하는 것이 아닙니다. 공간
            transcriptomics에서 domain을 찾는 방법은 주변 위치의 정보를 같이 씁니다.
            아래에서는 세 가지 결과를 나란히 봅니다.

            - expression-only Leiden: 비교용 baseline
            - BANKSY-style neighborhood feature: 주변 bin의 발현 정보를 feature에 추가
            - SpaGCN: spatial graph를 쓰는 spatial domain method
            """
        ),
        code(
            """
            stage = "spatial_domain_methods"
            start = time.perf_counter()

            DOMAIN_MAX_OBS = int(os.environ.get("SPIX_WORKSHOP_DOMAIN_MAX_OBS", "3500"))
            center_8um = np.median(analysis_coords, axis=0)
            distance_to_center = ((analysis_coords - center_8um) ** 2).sum(axis=1)
            if analysis_adata.n_obs <= DOMAIN_MAX_OBS:
                domain_idx = np.arange(analysis_adata.n_obs)
            else:
                domain_idx = np.sort(np.argpartition(distance_to_center, DOMAIN_MAX_OBS - 1)[:DOMAIN_MAX_OBS])

            domain_adata = analysis_adata[domain_idx].copy()
            domain_coords = np.asarray(domain_adata.obsm["spatial"], dtype=float)
            DOMAIN_N_PCS = min(20, domain_adata.obsm["X_pca"].shape[1])

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

            sq.gr.spatial_neighbors(
                domain_adata,
                spatial_key="spatial",
                coord_type="generic",
                n_neighs=6,
                key_added="spatial",
            )
            spatial_graph = domain_adata.obsp["spatial_connectivities"].tocsr()
            row_sum = np.asarray(spatial_graph.sum(axis=1)).ravel()
            row_sum[row_sum == 0] = 1
            spatial_average = sp.diags(1 / row_sum) @ spatial_graph
            neighbor_pca = spatial_average @ domain_adata.obsm["X_pca"][:, :DOMAIN_N_PCS]

            banksy_weight = float(os.environ.get("SPIX_WORKSHOP_BANKSY_STYLE_WEIGHT", "0.8"))
            domain_adata.obsm["X_banksy_style"] = np.hstack([
                domain_adata.obsm["X_pca"][:, :DOMAIN_N_PCS],
                banksy_weight * neighbor_pca,
            ])

            sc.pp.neighbors(
                domain_adata,
                n_neighbors=15,
                use_rep="X_banksy_style",
                key_added="banksy_style_graph",
                random_state=7,
            )
            sc.tl.leiden(
                domain_adata,
                resolution=0.35,
                neighbors_key="banksy_style_graph",
                key_added="banksy_domain",
                flavor="igraph",
                n_iterations=2,
                directed=False,
                random_state=7,
            )

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

            domain_methods = {
                "expression_domain": "Expression baseline",
                "banksy_domain": "BANKSY-style",
                "spagcn_domain": "SpaGCN",
            }

            count_tables = []
            for key, label in domain_methods.items():
                one = (
                    domain_adata.obs[key]
                    .value_counts()
                    .sort_index()
                    .rename_axis("domain")
                    .reset_index(name="n_bins")
                )
                one.insert(0, "method", label)
                count_tables.append(one)
            domain_count_table = pd.concat(count_tables, ignore_index=True)

            ari_rows = []
            method_items = list(domain_methods.items())
            for i in range(len(method_items)):
                for j in range(i + 1, len(method_items)):
                    key_a, label_a = method_items[i]
                    key_b, label_b = method_items[j]
                    ari_rows.append({
                        "method_a": label_a,
                        "method_b": label_b,
                        "adjusted_rand_index": adjusted_rand_score(
                            domain_adata.obs[key_a].astype(str),
                            domain_adata.obs[key_b].astype(str),
                        ),
                    })
            domain_ari_table = pd.DataFrame(ari_rows)

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print(f"domain panel: {domain_adata.n_obs:,} 8 um bins")
            print(f"SpaGCN l: {spagcn_l:.4f}")
            display(domain_count_table)
            display(domain_ari_table)
            """
        ),
        md(
            """
            ## 5-1. Domain map 비교

            같은 8 um panel에서 세 방법의 결과를 나란히 봅니다. 좋은 결과는 cluster
            개수가 많다는 뜻이 아니라, 조직 구조와 marker 해석이 같이 맞는 결과입니다.
            """
        ),
        code(
            """
            stage = "plot_spatial_domain_maps"
            start = time.perf_counter()

            fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
            for ax, (key, label) in zip(axes, domain_methods.items()):
                codes = domain_adata.obs[key].astype("category").cat.codes.to_numpy()
                ax.scatter(
                    domain_coords[:, 0],
                    domain_coords[:, 1],
                    s=5,
                    c=codes,
                    cmap="tab20",
                    rasterized=True,
                )
                ax.invert_yaxis()
                ax.set_aspect("equal")
                ax.set_title(label)
                ax.set_xticks([])
                ax.set_yticks([])
            plt.show()

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            """
        ),
        md(
            """
            ## 5-2. Domain marker

            이후 CCI에서는 BANKSY-style domain을 사용합니다. 여기서는 각 domain의
            marker를 간단히 확인합니다.
            """
        ),
        code(
            """
            stage = "banksy_domain_markers"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            display(marker_df)
            """
        ),
    ]


def cci_cells() -> list:
    return [
        md(
            """
            ## 6. Cell-cell interaction

            공간전사체에서 CCI를 볼 때의 장점은 두 가지입니다. 먼저 domain끼리 실제로
            붙어 있는지 볼 수 있고, 그 다음 ligand-receptor 발현이 그 접촉 관계와
            맞는지 볼 수 있습니다.
            """
        ),
        code(
            """
            stage = "cci_neighborhood_enrichment"
            start = time.perf_counter()

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
            im = ax.imshow(nhood_zscore_df.to_numpy(), cmap="vlag", vmin=-np.nanmax(abs(nhood_zscore_df.to_numpy())), vmax=np.nanmax(abs(nhood_zscore_df.to_numpy())))
            ax.set_xticks(np.arange(len(categories)))
            ax.set_xticklabels(categories, rotation=45, ha="right")
            ax.set_yticks(np.arange(len(categories)))
            ax.set_yticklabels(categories)
            ax.set_title("Neighborhood enrichment z-score")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            plt.show()

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            display(nhood_zscore_df.round(2))
            """
        ),
        md(
            """
            ## 6-1. Ligand-receptor 후보 확인

            다음은 발현 기반 ligand-receptor 분석입니다. 실습 시간에는 전체 database를
            새로 받지 않고, colorectal tissue에서 해석하기 쉬운 후보 pair만 사용합니다.
            """
        ),
        code(
            """
            stage = "cci_ligrec"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            stage = "cci_ligrec_table"
            start = time.perf_counter()

            means = ligrec_result["means"].copy()
            pvalues = ligrec_result["pvalues"].copy()

            row_names = []
            for i, name in enumerate(means.index.names):
                row_names.append(name if name is not None else f"row_{i}")
            means.index.names = row_names
            pvalues.index.names = row_names

            if means.columns.nlevels == 2:
                means.columns.names = ["sender_cluster", "receiver_cluster"]
                pvalues.columns.names = ["sender_cluster", "receiver_cluster"]
                means_table = means.stack(["sender_cluster", "receiver_cluster"], dropna=False)
                pvalue_table = pvalues.stack(["sender_cluster", "receiver_cluster"], dropna=False)
            else:
                means.columns.name = "cluster_pair"
                pvalues.columns.name = "cluster_pair"
                means_table = means.stack(dropna=False)
                pvalue_table = pvalues.stack(dropna=False)

            ligrec_means = means_table.rename("mean_expression").reset_index()
            ligrec_pvalues = pvalue_table.rename("pvalue").reset_index()

            merge_columns = [col for col in ligrec_means.columns if col != "mean_expression"]
            ligrec_table = ligrec_means.merge(ligrec_pvalues, on=merge_columns, how="left")
            ligrec_table = ligrec_table.replace([np.inf, -np.inf], np.nan)
            ligrec_table = ligrec_table.dropna(subset=["mean_expression"])

            if "source" in ligrec_table.columns and "target" in ligrec_table.columns:
                ligrec_table["pair"] = (
                    ligrec_table["source"].astype(str) + "-" + ligrec_table["target"].astype(str)
                )
            else:
                ligrec_table["pair"] = ligrec_table.iloc[:, 0].astype(str)

            ligrec_table["pvalue_sort"] = ligrec_table["pvalue"].fillna(1.0)
            ligrec_table = ligrec_table.sort_values(
                ["pvalue_sort", "mean_expression"],
                ascending=[True, False],
            )
            ligrec_display = ligrec_table.drop(columns=["pvalue_sort"])

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            display(ligrec_display.head(20))
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
            stage = "cci_ligrec_heatmap"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            display(heatmap_table)
            """
        ),
    ]


def spix_cells() -> list:
    return [
        md(
            """
            ## 7. SPIX

            마지막은 2 um ROI 전체를 그대로 사용합니다. 흐름은 P2 재현 코드와 맞춰
            `embedding -> smoothing -> equalization -> image cache -> multiscale segmentation -> scale별 SVG`
            순서로 둡니다. smoothing/equalization은 기본값으로 sweep을 돌려 자동
            선택합니다.
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
            stage = "spix_generate_embeddings"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print("X_embedding:", spix_adata.obsm["X_embedding"].shape)
            """
        ),
        md(
            """
            ## 7-2. Graph smoothing 자동 선택

            SPIX는 equalization 전에 embedding을 공간 graph 위에서 smoothing합니다.
            여기서는 P2 재현 코드와 같은 grid를 두고 추천값을 고릅니다. 시간이 부족한
            예행연습에서는 `SPIX_WORKSHOP_SPIX_RUN_TUNING=0`으로 끌 수 있습니다.
            """
        ),
        code(
            """
            stage = "spix_smoothing_selection"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print(smooth_params)
            """
        ),
        code(
            """
            stage = "spix_smooth_image"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print("X_embedding_smooth:", spix_adata.obsm["X_embedding_smooth"].shape)
            """
        ),
        md(
            """
            ## 7-3. Equalization 자동 선택과 image cache

            smoothing된 embedding을 SLIC 계열 segmentation이 쓰기 좋은 multichannel
            image로 바꿉니다. equalization parameter도 sweep으로 고릅니다.
            """
        ),
        code(
            """
            stage = "spix_equalization_selection"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print(equalization_params)
            """
        ),
        code(
            """
            stage = "spix_equalize_and_cache_image"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            stage = "spix_multiscale_segmentation"
            start = time.perf_counter()

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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            stage = "spix_multiscale_moran_svg"
            start = time.perf_counter()

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

            top_rows = []
            for column in spix_rank_df.columns:
                scale_id = column.replace("rank_", "")
                top_genes = spix_rank_df[column].dropna().sort_values().head(5)
                top_rows.append(pd.DataFrame({
                    "scale": scale_id,
                    "gene": top_genes.index,
                    "rank": top_genes.values,
                }))
            spix_top_svg_table = pd.concat(top_rows, ignore_index=True)

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            stage = "spix_add_segment_labels"
            start = time.perf_counter()

            for _, row in segment_index.iterrows():
                scale_id = str(row["scale_id"])
                is_native = str(row.get("native_identity", "")).lower() == "true"
                if is_native or str(row.get("path", "")) == "__native_identity__":
                    continue

                segment_path = Path(str(row["path"]))
                if not segment_path.is_absolute():
                    segment_path = SEGMENT_DIR / segment_path.name

                segment_file = np.load(segment_path, allow_pickle=True)
                spix_adata.obs[f"spix_{scale_id}"] = pd.Categorical(segment_file["seg_codes"].astype(str))

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            """
        ),
        code(
            """
            stage = "spix_scale_overview"
            start = time.perf_counter()

            plot_scales_um = os.environ.get("SPIX_WORKSHOP_SPIX_PLOT_SCALES_UM", "50,100,500")
            plot_scales_um = [float(x.strip()) for x in plot_scales_um.split(",") if x.strip()]
            plot_segment_index = segment_index[
                segment_index["resolution"].astype(float).isin(plot_scales_um)
            ].copy()

            if plot_segment_index.empty:
                non_native = segment_index["native_identity"].astype(str).str.lower() != "true"
                plot_segment_index = segment_index[non_native].head(3).copy()

            if spix_adata.n_obs > 140000:
                rng = np.random.default_rng(7)
                spix_plot_idx = np.sort(rng.choice(spix_adata.n_obs, size=140000, replace=False))
            else:
                spix_plot_idx = np.arange(spix_adata.n_obs)

            fig, axes = plt.subplots(1, len(plot_segment_index), figsize=(4.2 * len(plot_segment_index), 3.8), constrained_layout=True)
            if len(plot_segment_index) == 1:
                axes = [axes]

            for ax, (_, row) in zip(axes, plot_segment_index.iterrows()):
                obs_key = f"spix_{row['scale_id']}"
                color_codes = spix_adata.obs[obs_key].cat.codes.to_numpy()
                ax.scatter(
                    coords_2um[spix_plot_idx, 0],
                    coords_2um[spix_plot_idx, 1],
                    s=1.5,
                    c=color_codes[spix_plot_idx],
                    cmap="tab20",
                    rasterized=True,
                )
                ax.invert_yaxis()
                ax.set_aspect("equal")
                ax.set_title(f"{row['scale_id']} / {int(row['observed_obs_n_segments'])} units")
                ax.set_xticks([])
                ax.set_yticks([])
            plt.show()

            spix_scale_summary = segment_index[[
                "scale_id",
                "resolution",
                "observed_obs_n_segments",
            ]].copy()
            spix_scale_summary["mean_2um_bins_per_unit"] = (
                spix_adata.n_obs / spix_scale_summary["observed_obs_n_segments"]
            )

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
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
            stage = "final_report"
            start = time.perf_counter()

            meminfo = {}
            if Path("/proc/meminfo").exists():
                for line in Path("/proc/meminfo").read_text().splitlines():
                    key, value = line.split(":", 1)
                    if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}:
                        meminfo[key] = round(float(value.strip().split()[0]) / 1024 / 1024, 2)

            disk = shutil.disk_usage(Path.cwd())
            runtime_info = {
                "running_in_colab": bool(IN_COLAB),
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "cpu_count": os.cpu_count(),
                "thread_cap": N_JOBS,
                "memory_gb": meminfo,
                "cwd": str(Path.cwd().resolve()),
                "disk_free_gb": round(disk.free / 1024**3, 2),
            }

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
                "spix_shape": [int(spix_adata.n_obs), int(spix_adata.n_vars)],
                "stage_times": STAGE_TIMES,
                "outputs": {
                    "output_dir": str(OUTPUT_DIR),
                    "smoothing_selection": str(OUTPUT_DIR / "spix_smoothing_selection.json"),
                    "equalization_selection": str(OUTPUT_DIR / "spix_equalization_selection.json"),
                    "segments_index": str(SEGMENT_DIR / "segments_index.csv"),
                    "spix_moran_ranks": str(SEGMENT_DIR / "multiscale_moran_ranks.csv"),
                    "spix_moran_scores": str(SEGMENT_DIR / "multiscale_moran_scores.csv"),
                },
            }

            report_path = OUTPUT_DIR / f"{LECTURE_ID}_timing_report.json"
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True))

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})

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


def combined_notebook(data_url: str, data_sha256: str, roi_context_url: str, roi_context_sha256: str):
    nb = new_notebook(COMBINED_NOTEBOOK)
    nb["cells"] = [
        md(
            """
            # 공간전사체 분석 실습: SVG, spatial domain, CCI, SPIX

            같은 Visium HD P2 ROI에서 네 가지 질문을 순서대로 봅니다.

            1. **SVG**: 공간적으로 정리된 gene은 무엇인가?
            2. **Spatial domain**: 조직 영역은 어떻게 나눌 수 있는가?
            3. **CCI**: 서로 붙어 있는 영역 사이에 어떤 ligand-receptor 신호가 보이는가?
            4. **SPIX**: 2 um 정보를 여러 scale의 tissue unit으로 어떻게 바꿀 수 있는가?
            """
        ),
        md(
            """
            ## 입력 자료

            원본 P2는 2 um bin이 약 8.7M개입니다. 여기서는 그중 하나의 ROI를
            사용합니다. 일반 분석은 8 um pseudobulk로 진행하고, SPIX는 2 um ROI
            전체를 사용합니다.
            """
        ),
    ]
    nb["cells"].extend(setup_cells(data_url, data_sha256, roi_context_url, roi_context_sha256))
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
