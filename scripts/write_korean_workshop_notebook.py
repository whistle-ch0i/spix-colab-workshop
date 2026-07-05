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
DEFAULT_DATA_URL = (
    "https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/"
    f"data/{DATA_FILE}"
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


def setup_cells(data_url: str, data_sha256: str) -> list:
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

    LECTURE_ID = "choi_whisoo_combined"
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
    )

    return [
        md(
            """
            ## 0. 실행 환경

            Colab 무료 티어는 CPU와 RAM이 고정되어 있지 않습니다. 첫 셀에서
            현재 런타임 정보를 확인합니다. 실습 기본값은 CPU runtime,
            `N_JOBS=2`입니다.
            """
        ),
        code(setup_code),
        md(
            """
            ## 1. SPIX 설치 확인

            Colab에서 SPIX가 없으면 GitHub에서 설치합니다. 로컬에서 실행할 때는
            현재 workspace의 SPIX checkout을 먼저 찾습니다.
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

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            """
        ),
        md(
            """
            ## 1-1. Colab용 SPIX import 정리

            이 셀은 Colab에서만 동작합니다. 이번 실습에 쓰지 않는 optional module
            때문에 import가 멈추지 않도록, 필요한 import만 남깁니다.
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
            ## 1-2. 분석 패키지 import

            여기서부터 실제 분석에 사용할 패키지를 불러옵니다.
            """
        ),
        code(
            """
            stage = "import_analysis_packages"
            start = time.perf_counter()

            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd
            import scanpy as sc
            import scipy.sparse as sp
            import squidpy as sq
            from IPython.display import display
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

            실습 데이터는 10x Genomics Visium HD Human Colon Cancer P2에서 잘라낸
            native 2 um ROI입니다. 원본 전체는 약 8.7M bins라 Colab 무료 티어에서
            바로 다루기 어렵기 때문에, 해상도는 유지하고 영역과 gene 수만 줄였습니다.
            """
        ),
        code(
            """
            stage = "load_data"
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
                assert observed_sha256 == DATA_SHA256, (
                    f"Data SHA-256 mismatch: {observed_sha256}"
                )

            adata = sc.read_h5ad(data_path)
            adata.obs_names = adata.obs_names.astype(str)
            adata.var_names = adata.var_names.astype(str)
            coords = np.asarray(adata.obsm["spatial"], dtype=float)

            source = adata.uns.get("spix_workshop_source", {})
            data_summary = pd.DataFrame([{
                "n_bins": adata.n_obs,
                "n_genes": adata.n_vars,
                "file_mb": round(data_path.stat().st_size / 1024**2, 2),
                "bin_size_um": source.get("bin_size_um", "unknown"),
                "source_shape": str(source.get("full_shape", "unknown")),
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
            ## 3. 빠른 QC

            분석 전에 counts와 검출 gene 수가 공간적으로 크게 깨져 있지 않은지
            확인합니다. 오늘은 QC를 깊게 다루지는 않고, 뒤 결과를 읽을 수 있는
            상태인지 정도만 봅니다.
            """
        ),
        code(
            """
            stage = "quick_qc"
            start = time.perf_counter()

            total_counts = np.asarray(adata.X.sum(axis=1)).ravel()
            if sp.issparse(adata.X):
                detected_genes = np.asarray((adata.X > 0).sum(axis=1)).ravel()
            else:
                detected_genes = (adata.X > 0).sum(axis=1)

            max_points = 100000
            if adata.n_obs <= max_points:
                plot_idx = np.arange(adata.n_obs)
            else:
                rng = np.random.default_rng(7)
                plot_idx = np.sort(rng.choice(adata.n_obs, size=max_points, replace=False))

            fig, ax = plt.subplots(figsize=(5, 4.5))
            ax.scatter(
                coords[plot_idx, 0],
                coords[plot_idx, 1],
                s=2,
                c=np.log1p(total_counts[plot_idx]),
                cmap="viridis",
                rasterized=True,
            )
            ax.invert_yaxis()
            ax.set_aspect("equal")
            ax.set_title("log1p(total counts)")
            ax.set_xticks([])
            ax.set_yticks([])
            plt.show()

            fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), constrained_layout=True)
            axes[0].hist(total_counts, bins=50, color="#4C78A8")
            axes[0].set_title("UMI counts per 2 um bin")
            axes[1].hist(detected_genes, bins=50, color="#59A14F")
            axes[1].set_title("Detected genes per 2 um bin")
            plt.show()

            qc_summary = pd.DataFrame([{
                "median_counts": float(np.median(total_counts)),
                "median_detected_genes": float(np.median(detected_genes)),
                "max_counts": float(np.max(total_counts)),
            }])

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            display(qc_summary)
            """
        ),
    ]


def standard_tool_cells() -> list:
    return [
        md(
            """
            ## 4. 표준 도구용 sub-ROI 만들기

            SVG, clustering, CCI는 Scanpy/Squidpy로 진행합니다. 500k bins 전체에
            이 과정을 모두 얹으면 Colab에서 시간이 불안정해질 수 있어, 같은 ROI
            안의 중심부 50k bins를 사용합니다. SPIX 파트는 뒤에서 500k 전체를
            사용합니다.
            """
        ),
        code(
            """
            stage = "standard_tool_subset"
            start = time.perf_counter()

            TOOL_MAX_OBS = int(os.environ.get("SPIX_WORKSHOP_TOOL_MAX_OBS", "50000"))

            center = np.median(coords, axis=0)
            distance_to_center = ((coords - center) ** 2).sum(axis=1)

            if adata.n_obs <= TOOL_MAX_OBS:
                tool_idx = np.arange(adata.n_obs)
            else:
                tool_idx = np.sort(np.argpartition(distance_to_center, TOOL_MAX_OBS - 1)[:TOOL_MAX_OBS])

            tool_adata = adata[tool_idx].copy()
            tool_coords = np.asarray(tool_adata.obsm["spatial"], dtype=float)

            tool_counts = np.asarray(tool_adata.X.sum(axis=1)).ravel()
            keep_nonzero = tool_counts > 0
            if keep_nonzero.sum() < tool_adata.n_obs:
                tool_adata = tool_adata[keep_nonzero].copy()
                tool_coords = np.asarray(tool_adata.obsm["spatial"], dtype=float)

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print(f"sub-ROI: {tool_adata.n_obs:,} bins x {tool_adata.n_vars:,} genes")
            """
        ),
        md(
            """
            ## 4-1. Scanpy 전처리와 neighbor graph

            표준적인 흐름대로 normalize, log transform, HVG, PCA, neighbor graph,
            Leiden clustering을 순서대로 실행합니다.
            """
        ),
        code(
            """
            stage = "standard_tool_preprocessing_scanpy_squidpy"
            start = time.perf_counter()

            TOOL_HVG_N_TOP = int(os.environ.get("SPIX_WORKSHOP_TOOL_HVG_N_TOP", "1200"))
            TOOL_N_PCS = int(os.environ.get("SPIX_WORKSHOP_TOOL_N_PCS", "30"))
            TOOL_N_NEIGHBORS = int(os.environ.get("SPIX_WORKSHOP_TOOL_N_NEIGHBORS", "30"))
            SCANPY_LEIDEN_RESOLUTION = float(os.environ.get("SPIX_WORKSHOP_SCANPY_RESOLUTION", "0.01"))

            sc.pp.normalize_total(tool_adata, target_sum=1e4)
            sc.pp.log1p(tool_adata)
            tool_adata.layers["log_norm"] = tool_adata.X.copy()

            sc.pp.highly_variable_genes(
                tool_adata,
                n_top_genes=min(TOOL_HVG_N_TOP, tool_adata.n_vars),
                flavor="seurat",
            )

            sc.pp.pca(
                tool_adata,
                n_comps=min(TOOL_N_PCS, tool_adata.n_obs - 1, tool_adata.n_vars - 1),
                mask_var="highly_variable",
                svd_solver="arpack",
                random_state=7,
            )

            sc.pp.neighbors(
                tool_adata,
                n_neighbors=TOOL_N_NEIGHBORS,
                n_pcs=min(TOOL_N_PCS, tool_adata.obsm["X_pca"].shape[1]),
                random_state=7,
            )

            sc.tl.leiden(
                tool_adata,
                resolution=SCANPY_LEIDEN_RESOLUTION,
                key_added="scanpy_leiden",
                flavor="igraph",
                n_iterations=2,
                directed=False,
                random_state=7,
            )

            sq.gr.spatial_neighbors(
                tool_adata,
                spatial_key="spatial",
                coord_type="generic",
                n_neighs=6,
                key_added="spatial",
            )

            cluster_summary = (
                tool_adata.obs["scanpy_leiden"]
                .value_counts()
                .sort_index()
                .rename_axis("scanpy_leiden")
                .reset_index(name="n_bins")
            )

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print(f"neighbors={TOOL_N_NEIGHBORS}, Leiden resolution={SCANPY_LEIDEN_RESOLUTION}")
            display(cluster_summary)
            """
        ),
    ]


def svg_cells() -> list:
    return [
        md(
            """
            ## 5. SVG

            먼저 공간적으로 모여 있는 gene을 찾습니다. 여기서는 Squidpy의 Moran's I를
            사용합니다. 기본값은 실습용 marker panel이고, 전체 gene을 보려면
            `SPIX_WORKSHOP_SVG_MODE=all`로 바꾸면 됩니다.
            """
        ),
        code(
            """
            stage = "svg_squidpy_moran"
            start = time.perf_counter()

            SVG_MARKER_PANEL = [
                "PIGR", "OLFM4", "MUC2", "TFF3", "REG1A", "REG1B", "REG4", "CLCA4",
                "EPCAM", "KRT8", "KRT18", "KRT19", "CEACAM5", "TACSTD2",
                "COL1A1", "COL1A2", "COL3A1", "COL12A1", "DCN", "VIM", "TAGLN", "ACTA2", "FMOD",
                "PTPRC", "CD74", "LYZ", "SPP1", "CXCL10", "MIF",
                "MKI67", "TOP2A", "UBE2C", "MCM10", "FOXM1",
                "MGP", "THBS2", "SFRP4", "FN1", "LAMB1",
            ]

            SVG_MODE = os.environ.get("SPIX_WORKSHOP_SVG_MODE", "panel").lower()
            if SVG_MODE == "all":
                svg_genes = list(tool_adata.var_names)
            else:
                svg_genes = [gene for gene in SVG_MARKER_PANEL if gene in tool_adata.var_names]

            assert len(svg_genes) > 0, "현재 데이터에 존재하는 SVG panel gene이 없습니다."

            svg_moran = sq.gr.spatial_autocorr(
                tool_adata,
                genes=svg_genes,
                mode="moran",
                layer="log_norm",
                n_perms=None,
                n_jobs=N_JOBS,
                backend="loky",
                copy=True,
                show_progress_bar=False,
            )

            svg_moran = svg_moran.sort_values("I", ascending=False)
            top_svg_genes = svg_moran.head(6).index.tolist()

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            display(svg_moran.head(15))
            """
        ),
        md(
            """
            ## 5-1. SVG 공간 패턴 확인

            Moran's I 상위 gene을 tissue 위에 다시 그립니다. 순위표와 실제 공간
            패턴을 같이 봐야 결과를 해석하기 쉽습니다.
            """
        ),
        code(
            """
            stage = "svg_gene_maps"
            start = time.perf_counter()

            genes_to_plot = top_svg_genes[:4]
            fig, axes = plt.subplots(
                1,
                len(genes_to_plot),
                figsize=(4.2 * len(genes_to_plot), 4),
                constrained_layout=True,
            )
            if len(genes_to_plot) == 1:
                axes = [axes]

            expression_matrix = tool_adata.layers["log_norm"]
            for ax, gene in zip(axes, genes_to_plot):
                gene_index = tool_adata.var_names.get_loc(gene)
                gene_values = expression_matrix[:, gene_index]
                if sp.issparse(gene_values):
                    gene_values = gene_values.toarray()
                gene_values = np.asarray(gene_values).ravel()

                ax.scatter(
                    tool_coords[:, 0],
                    tool_coords[:, 1],
                    s=2,
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


def clustering_cells() -> list:
    return [
        md(
            """
            ## 6. Spatial clustering

            Leiden cluster를 tissue 위에 그려 봅니다. 여기서는 cluster 자체보다,
            뒤에서 marker와 함께 해석할 공간 domain의 초안을 만든다고 보면 됩니다.
            """
        ),
        code(
            """
            stage = "spatial_clustering_scanpy_plot"
            start = time.perf_counter()

            cluster_codes = tool_adata.obs["scanpy_leiden"].cat.codes.to_numpy()

            fig, ax = plt.subplots(figsize=(5.2, 4.8))
            ax.scatter(
                tool_coords[:, 0],
                tool_coords[:, 1],
                s=2,
                c=cluster_codes,
                cmap="tab20",
                rasterized=True,
            )
            ax.invert_yaxis()
            ax.set_aspect("equal")
            ax.set_title("Scanpy Leiden spatial domains")
            ax.set_xticks([])
            ax.set_yticks([])
            plt.show()

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            display(cluster_summary)
            """
        ),
        md(
            """
            ## 6-1. Cluster marker

            각 cluster에서 올라오는 marker를 확인합니다. 앞의 SVG 결과와 같이 보면
            cluster가 어떤 조직 영역을 반영하는지 더 쉽게 읽을 수 있습니다.
            """
        ),
        code(
            """
            stage = "spatial_clustering_scanpy_markers"
            start = time.perf_counter()

            sc.tl.rank_genes_groups(
                tool_adata,
                groupby="scanpy_leiden",
                layer="log_norm",
                use_raw=False,
                method="t-test_overestim_var",
                key_added="scanpy_leiden_markers",
            )

            marker_df = sc.get.rank_genes_groups_df(
                tool_adata,
                group=None,
                key="scanpy_leiden_markers",
            )

            marker_df = marker_df.sort_values(
                ["group", "scores"],
                ascending=[True, False],
            )
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
            ## 7. Cell-cell interaction

            cluster 사이 ligand-receptor signal을 Squidpy `ligrec`으로 확인합니다.
            실습 시간에는 전체 DB를 새로 받지 않고, colorectal tissue에서 읽기 쉬운
            후보 pair만 사용합니다.
            """
        ),
        code(
            """
            stage = "cell_cell_interaction_squidpy_ligrec"
            start = time.perf_counter()

            LR_CANDIDATES = pd.DataFrame({
                "source": ["SPP1", "MIF", "CD74", "COL1A1", "COL1A2", "FN1", "LAMB1", "JAG1", "APOE", "LGALS3", "TGFBI"],
                "target": ["CD44", "CD74", "MIF", "ITGB1", "ITGB1", "ITGA5", "ITGB1", "NOTCH1", "LRP1", "ITGB1", "ITGB5"],
            })

            ligrec_interactions = LR_CANDIDATES[
                LR_CANDIDATES["source"].isin(tool_adata.var_names)
                & LR_CANDIDATES["target"].isin(tool_adata.var_names)
            ].copy()

            assert len(ligrec_interactions) > 0, "현재 gene set에서 사용할 수 있는 LR 후보가 없습니다."

            LIGREC_PERMUTATIONS = int(os.environ.get("SPIX_WORKSHOP_LIGREC_PERMUTATIONS", "20"))

            ligrec_result = sq.gr.ligrec(
                tool_adata,
                cluster_key="scanpy_leiden",
                interactions=ligrec_interactions,
                use_raw=False,
                copy=True,
                threshold=0.0,
                n_perms=LIGREC_PERMUTATIONS,
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
            ## 7-1. LR 결과표 정리

            `ligrec` 결과는 matrix 형태로 나오기 때문에, 보기 쉬운 긴 표로 바꿉니다.
            mean expression이 크고 p-value가 작은 pair를 위쪽에 둡니다.
            """
        ),
        code(
            """
            stage = "cell_cell_interaction_table"
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
            ## 7-2. 상위 LR pair heatmap

            상위 pair 하나를 골라 sender cluster와 receiver cluster 조합으로 펼쳐
            봅니다.
            """
        ),
        code(
            """
            stage = "cell_cell_interaction_heatmap"
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

            fig, ax = plt.subplots(figsize=(6, 5))
            im = ax.imshow(heatmap_table.to_numpy(), cmap="magma")
            ax.set_xticks(np.arange(heatmap_table.shape[1]))
            ax.set_xticklabels(heatmap_table.columns, rotation=45, ha="right")
            ax.set_yticks(np.arange(heatmap_table.shape[0]))
            ax.set_yticklabels(heatmap_table.index)
            ax.set_title(f"{top_pair}: Squidpy ligrec mean")
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
            ## 8. SPIX

            이제 같은 Visium HD 2 um 자료를 SPIX 방식으로 처리합니다. 아래 순서는
            VisiumHD P2 논문/재현 코드 흐름에 맞췄고, Colab 실습을 위해 데이터
            크기와 `N_JOBS`만 조절했습니다.
            """
        ),
        code(
            """
            SPIX_EMBEDDING_DIMS = int(os.environ.get("SPIX_WORKSHOP_SPIX_EMBEDDING_DIMS", "30"))
            SPIX_EMBEDDING_CHANNELS = list(range(SPIX_EMBEDDING_DIMS))

            SPIX_RUN_TUNING = os.environ.get("SPIX_WORKSHOP_SPIX_RUN_TUNING", "0").lower()
            SPIX_RUN_TUNING = SPIX_RUN_TUNING in {"1", "true", "yes"}

            SPIX_GRAPH_K = int(os.environ.get("SPIX_WORKSHOP_SPIX_GRAPH_K", "20"))
            SPIX_GRAPH_T = int(os.environ.get("SPIX_WORKSHOP_SPIX_GRAPH_T", "10"))
            SPIX_EQ_SLEFT = float(os.environ.get("SPIX_WORKSHOP_SPIX_EQ_SLEFT", "2.0"))
            SPIX_EQ_SRIGHT = float(os.environ.get("SPIX_WORKSHOP_SPIX_EQ_SRIGHT", "2.0"))

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
            print("graph smoothing:", {"graph_k": SPIX_GRAPH_K, "graph_t": SPIX_GRAPH_T})
            print("equalization:", {"sleft": SPIX_EQ_SLEFT, "sright": SPIX_EQ_SRIGHT})
            print("scales:", RESOLUTIONS_UM)
            """
        ),
        md(
            """
            ## 8-1. Embedding

            Count matrix를 log-normalized PCA embedding으로 바꿉니다. 논문 P2
            흐름처럼 30차원, 최대 2,000 features를 사용합니다.
            """
        ),
        code(
            """
            stage = "spix_generate_embeddings"
            start = time.perf_counter()

            adata = SPIX.tm.generate_embeddings(
                adata,
                dim_reduction="PCA",
                normalization="log_norm",
                n_jobs=N_JOBS,
                dimensions=SPIX_EMBEDDING_DIMS,
                nfeatures=min(2000, adata.n_vars),
                force=True,
                use_coords_as_tiles=True,
                coords_rescale_to_nn=False,
                coords_max_gap_factor=None,
                raster_random_seed=42,
            )

            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": stage, "seconds": seconds, "ok": True})
            print(f"[timing] {stage}: {seconds} sec")
            print("X_embedding:", adata.obsm["X_embedding"].shape)
            """
        ),
        md(
            """
            ## 8-2. Graph smoothing

            Equalization 전에 graph smoothing을 적용합니다. 기본값은 P2 재현 코드의
            fixed fallback 값입니다. 시간이 충분하면 `SPIX_WORKSHOP_SPIX_RUN_TUNING=1`
            로 sweep을 켤 수 있습니다.
            """
        ),
        code(
            """
            stage = "spix_smoothing_selection"
            start = time.perf_counter()

            if SPIX_RUN_TUNING:
                smoothing_selection = SPIX.ip.evaluate_smoothing_sweep(
                    adata,
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
                smooth_params = {"graph_k": SPIX_GRAPH_K, "graph_t": SPIX_GRAPH_T}
                smoothing_selection = {
                    "recommendation": {
                        "params": smooth_params,
                        "source": "fixed fallback from VisiumHD P2 reproduction code",
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

            adata = SPIX.ip.smooth_image(
                adata,
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
            print("X_embedding_smooth:", adata.obsm["X_embedding_smooth"].shape)
            """
        ),
        md(
            """
            ## 8-3. Equalization과 image cache

            SLIC 계열 segmentation에 사용할 multichannel image를 만듭니다. 여기서는
            smoothing된 embedding을 equalization한 뒤 `image_plot_slic` cache로
            저장합니다.
            """
        ),
        code(
            """
            stage = "spix_equalization_selection"
            start = time.perf_counter()

            if SPIX_RUN_TUNING:
                equalization_selection = SPIX.ip.evaluate_equalization_sweep(
                    adata,
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
                equalization_params = {"sleft": SPIX_EQ_SLEFT, "sright": SPIX_EQ_SRIGHT}
                equalization_selection = {
                    "best": equalization_params,
                    "source": "fixed fallback from VisiumHD P2 reproduction code",
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

            adata = SPIX.ip.equalize_image(
                adata,
                dimensions=SPIX_EMBEDDING_CHANNELS,
                embedding="X_embedding_smooth",
                sleft=float(equalization_params["sleft"]),
                sright=float(equalization_params["sright"]),
            )

            SPIX.ip.cache_embedding_image(
                adata,
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
            ## 8-4. Multiscale segmentation

            2 um부터 500 um까지 여러 scale의 tissue unit을 만듭니다. `r2`는 native
            2 um bin이고, 나머지 scale은 SPIX segment입니다.
            """
        ),
        code(
            """
            stage = "spix_multiscale_segmentation"
            start = time.perf_counter()

            segment_index = SPIX.sp.precompute_multiscale_segments(
                adata,
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
            ## 8-5. SPIX scale별 Moran/SVG

            각 scale의 segment label을 기준으로 Moran's I를 계산합니다. 이 표는 어떤
            gene이 어떤 scale에서 더 뚜렷하게 조직화되는지 보는 데 사용합니다.
            """
        ),
        code(
            """
            stage = "spix_multiscale_moran_svg"
            start = time.perf_counter()

            spix_rank_df, spix_score_df = SPIX.an.multiscale_moran_ranks(
                adata,
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
            ## 8-6. 대표 scale 보기

            화면에서는 50, 100, 500 um scale을 먼저 확인합니다. 필요하면
            `SPIX_WORKSHOP_SPIX_PLOT_SCALES_UM` 값을 바꿔 다른 scale을 볼 수
            있습니다.
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
                adata.obs[f"spix_{scale_id}"] = pd.Categorical(segment_file["seg_codes"].astype(str))

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

            max_points = 140000
            if adata.n_obs <= max_points:
                plot_idx = np.arange(adata.n_obs)
            else:
                rng = np.random.default_rng(7)
                plot_idx = np.sort(rng.choice(adata.n_obs, size=max_points, replace=False))

            fig, axes = plt.subplots(
                1,
                len(plot_segment_index),
                figsize=(4.4 * len(plot_segment_index), 4),
                constrained_layout=True,
            )
            if len(plot_segment_index) == 1:
                axes = [axes]

            for ax, (_, row) in zip(axes, plot_segment_index.iterrows()):
                obs_key = f"spix_{row['scale_id']}"
                color_codes = adata.obs[obs_key].cat.codes.to_numpy()

                ax.scatter(
                    coords[plot_idx, 0],
                    coords[plot_idx, 1],
                    s=2,
                    c=color_codes[plot_idx],
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
            spix_scale_summary["mean_bins_per_unit"] = (
                adata.n_obs / spix_scale_summary["observed_obs_n_segments"]
            )
            spix_scale_summary["approx_scale_area_um2"] = spix_scale_summary["resolution"] ** 2

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
            ## 9. 실행 시간 저장

            마지막으로 실행 시간과 주요 산출물 위치를 JSON으로 저장합니다. Colab에서
            실행한 뒤 이 파일을 보관하면 실제 무료 티어 시간을 확인할 수 있습니다.
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
                "topic": "SVG, spatial clustering, cell-cell interaction, SPIX",
                "validation_passed": True,
                "elapsed_seconds": elapsed,
                "runtime": runtime_info,
                "data_file": str(data_path),
                "data_shape": [int(adata.n_obs), int(adata.n_vars)],
                "standard_tool_shape": [int(tool_adata.n_obs), int(tool_adata.n_vars)],
                "stage_times": STAGE_TIMES,
                "outputs": {
                    "output_dir": str(OUTPUT_DIR),
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


def combined_notebook(data_url: str, data_sha256: str):
    nb = new_notebook(COMBINED_NOTEBOOK)
    nb["cells"] = [
        md(
            """
            # 공간전사체 분석 실습: SVG, spatial clustering, CCI, SPIX

            2026 제20회 통계유전학 워크샵 공간전사체 분석 실습 중 최휘수 담당
            파트입니다.

            실습 순서는 다음과 같습니다.

            1. **SVG**: 공간적으로 조직화된 gene 찾기
            2. **Spatial clustering**: expression 기반 tissue domain 나누기
            3. **Cell-cell interaction**: cluster 사이 ligand-receptor signal 확인
            4. **SPIX**: 2 um bin을 multiscale tissue unit으로 변환
            """
        ),
        md(
            """
            ## 데이터 크기

            원본 P2 2 um 전체 데이터는 약 8.7M bins입니다. Colab 무료 티어에서는
            전체 데이터를 안정적으로 읽고 분석하기 어렵기 때문에, 실습에서는
            `500,000 bins x 2,515 genes` native 2 um ROI를 사용합니다.

            표준 도구 파트는 같은 ROI 안의 50k 연속 sub-ROI로 진행하고, SPIX 파트는
            500k ROI 전체를 사용합니다.
            """
        ),
    ]
    nb["cells"].extend(setup_cells(data_url, data_sha256))
    nb["cells"].extend(data_cells())
    nb["cells"].extend(standard_tool_cells())
    nb["cells"].extend(svg_cells())
    nb["cells"].extend(clustering_cells())
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data_file)
    data_sha256 = sha256sum(data_path) if data_path.exists() else ""
    notebook_dir = Path(args.notebook_dir)

    name, nb = combined_notebook(args.data_url, data_sha256)
    write_notebook(notebook_dir / name, nb)

    print(json.dumps({"written": [str(notebook_dir / name)], "data_sha256": data_sha256}, indent=2))


if __name__ == "__main__":
    main()
