#!/usr/bin/env python3
"""Write the Korean Colab workshop notebook."""

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
    import platform
    import shutil
    import subprocess
    import time
    import importlib.util
    import warnings
    from contextlib import contextmanager
    from pathlib import Path

    LECTURE_ID = "choi_whisoo_combined"
    RUN_STARTED_AT = time.perf_counter()
    STAGE_TIMES = []

    N_JOBS = int(os.environ.get("SPIX_WORKSHOP_N_JOBS", "2"))
    for var in [
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ]:
        os.environ.setdefault(var, str(N_JOBS))
    os.environ.setdefault("SPIX_ENABLE_THREAD_CAP", "1")
    os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_spix_workshop")

    DATA_FILE = os.environ.get("SPIX_WORKSHOP_DATA_FILE", __DATA_FILE__)
    DATA_URL = os.environ.get("SPIX_WORKSHOP_DATA_URL", __DATA_URL__)
    DATA_SHA256 = os.environ.get("SPIX_WORKSHOP_DATA_SHA256", __DATA_SHA256__)
    OUTPUT_DIR = Path("spix_korean_lecture_outputs") / LECTURE_ID
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def running_in_colab():
        try:
            import google.colab  # noqa: F401
            return True
        except Exception:
            return False

    IN_COLAB = running_in_colab()

    def read_meminfo_gb():
        out = {}
        try:
            for line in Path("/proc/meminfo").read_text().splitlines():
                key, value = line.split(":", 1)
                kb = float(value.strip().split()[0])
                out[key] = round(kb / 1024 / 1024, 2)
        except Exception:
            pass
        return out

    def runtime_snapshot():
        disk = shutil.disk_usage(Path.cwd())
        return {
            "running_in_colab": bool(IN_COLAB),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "thread_cap": N_JOBS,
            "memory_gb": read_meminfo_gb(),
            "cwd": str(Path.cwd().resolve()),
            "disk_free_gb": round(disk.free / 1024**3, 2),
        }

    @contextmanager
    def timed_stage(name):
        start = time.perf_counter()
        try:
            yield
            ok = True
        except Exception:
            ok = False
            raise
        finally:
            seconds = round(time.perf_counter() - start, 2)
            STAGE_TIMES.append({"stage": name, "seconds": seconds, "ok": ok})
            print(f"[timing] {name}: {seconds} sec | ok={ok}")

    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")

    print(json.dumps(runtime_snapshot(), indent=2))
    """
    setup_code = (
        setup_code.replace("__DATA_FILE__", json.dumps(DATA_FILE))
        .replace("__DATA_URL__", json.dumps(data_url))
        .replace("__DATA_SHA256__", json.dumps(data_sha256))
    )

    return [
        md(
            """
            ## 0. 실행 환경 기록

            Colab 무료 티어는 CPU 수와 RAM이 고정되어 있지 않습니다. 그래서 첫
            셀에서 실제 런타임 정보를 남깁니다. 기본 실습은 CPU runtime,
            `N_JOBS=2`로 맞춥니다.
            """
        ),
        code(setup_code),
        md(
            """
            ## 1. 패키지 불러오기

            이번 실습에서 사용할 도구입니다. SVG, spatial clustering,
            cell-cell interaction은 많이 쓰이는 Scanpy/Squidpy 흐름으로 먼저
            확인하고, 마지막에 같은 Visium HD 자료를 SPIX 방식으로 다시 다룹니다.

            - SVG: `Squidpy`의 Moran's I
            - spatial clustering: `Scanpy`의 PCA, neighbor graph, Leiden
            - cell-cell interaction: `Squidpy`의 `ligrec`
            - SPIX: embedding, graph smoothing, equalization,
              `image_plot_slic` multiscale segmentation

            Colab에서는 GitHub에서 SPIX를 설치하고, 로컬 repo에서는 현재
            체크아웃을 우선 사용합니다.
            """
        ),
        code(
            """
            with timed_stage("import_or_install"):
                def ensure_spix_importable():
                    if importlib.util.find_spec("SPIX") is not None:
                        return
                    cwd = Path.cwd().resolve()
                    for root in [cwd, *cwd.parents]:
                        if (root / "SPIX" / "__init__.py").exists():
                            sys.path.insert(0, str(root))
                            return
                    if IN_COLAB:
                        subprocess.check_call([
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "-q",
                            "git+https://github.com/whistle-ch0i/SPIX.git",
                        ])
                        return
                    raise ImportError("SPIX를 import할 수 없습니다. SPIX repo 안에서 실행하거나 SPIX를 설치하세요.")

                def patch_spix_visualization_imports_for_colab():
                    if not IN_COLAB:
                        return
                    spec = importlib.util.find_spec("SPIX")
                    if spec is None or spec.origin is None:
                        return
                    init_path = Path(spec.origin).parent / "visualization" / "__init__.py"
                    if not init_path.exists():
                        return
                    text = init_path.read_text()
                    if "workshop-safe optional visualization imports" in text:
                        return
                    if "from .scale_hotspot_biology import *" not in text:
                        return
                    init_path.write_text(
                        "\\n".join([
                            "from .plotting import *",
                            "from .origin_display import *",
                            "",
                            "# workshop-safe optional visualization imports",
                            "for _module in (",
                            "    'scale_hotspot_biology',",
                            "    'figure4_hotspot_story',",
                            "    'figure4_hotspot_0509',",
                            "):",
                            "    try:",
                            "        exec(f'from .{_module} import *')",
                            "    except ModuleNotFoundError:",
                            "        pass",
                            "",
                        ])
                    )

                def patch_spix_analysis_imports_for_colab():
                    if not IN_COLAB:
                        return
                    spec = importlib.util.find_spec("SPIX")
                    if spec is None or spec.origin is None:
                        return
                    init_path = Path(spec.origin).parent / "analysis" / "__init__.py"
                    if not init_path.exists():
                        return
                    text = init_path.read_text()
                    if "workshop-safe optional analysis imports" in text:
                        return
                    if "from .cluster_comparison import *" not in text:
                        return
                    init_path.write_text(
                        "\\n".join([
                            "import os",
                            "",
                            "os.environ.setdefault('NUMBA_CACHE_DIR', '/tmp/numba_spix')",
                            "",
                            "from .calculate_original_moranI import *",
                            "from .enrichment_analysis import *",
                            "from .perform_pseudo_bulk_analysis import *",
                            "from .gene_expression_embedding import *",
                            "from .gene_expression_gallery import *",
                            "from .multiscale_moran_ranks import *",
                            "from .segment_svg_enrichment import *",
                            "from .celltype_enrichment import *",
                            "from .svg_specificity import *",
                            "from .svg_gain_explanation import *",
                            "from .moran_geary_comparison import *",
                            "from .geary_supplementary_figure import *",
                            "",
                            "# workshop-safe optional analysis imports",
                            "for _module in (",
                            "    'cluster_comparison',",
                            "    'scale_biology',",
                            "    'scale_hotspot_biology',",
                            "    'figure4_hotspot_workflow',",
                            "    'paired_multiscale',",
                            "    'manuscript_scale_svg_figures',",
                            "):",
                            "    try:",
                            "        exec(f'from .{_module} import *')",
                            "    except ModuleNotFoundError:",
                            "        pass",
                            "",
                        ])
                    )

                ensure_spix_importable()
                patch_spix_visualization_imports_for_colab()
                patch_spix_analysis_imports_for_colab()

                import hashlib
                import urllib.request

                import matplotlib.pyplot as plt
                import numpy as np
                import pandas as pd
                import scanpy as sc
                import scipy.sparse as sp
                import squidpy as sq
                from IPython.display import display

                import SPIX

            print("Scanpy:", sc.__version__)
            print("Squidpy:", sq.__version__)
            print("SPIX import path:", SPIX.__file__)
            """
        ),
        md(
            """
            ## 2. 데이터 불러오기

            실습 데이터는 10x Genomics 공개 Visium HD Human Colon Cancer P2에서
            잘라낸 native 2 um ROI입니다. 원본 P2 전체는 약 8.7M bins라 Colab
            무료 티어에서 바로 다루기 어렵습니다. 여기서는 해상도는 그대로 두고,
            영역과 gene 수만 실습 시간에 맞게 줄인 500k ROI를 사용합니다.
            """
        ),
        code(
            """
            def file_sha256(path):
                h = hashlib.sha256()
                with Path(path).open("rb") as fh:
                    for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                        h.update(chunk)
                return h.hexdigest()

            def locate_or_download_data():
                data_file_path = Path(DATA_FILE).expanduser()
                data_file_name = data_file_path.name
                candidates = [
                    data_file_path,
                    Path("data") / data_file_name,
                    Path("..") / "data" / data_file_name,
                    Path.cwd() / "data" / data_file_name,
                    Path("/content") / data_file_name,
                ]
                for candidate in candidates:
                    if candidate.exists():
                        return candidate.resolve()
                target = Path("/content" if IN_COLAB else ".") / data_file_name
                print("Downloading data from:", DATA_URL)
                urllib.request.urlretrieve(DATA_URL, target)
                return target.resolve()

            with timed_stage("load_data"):
                data_path = locate_or_download_data()
                if DATA_SHA256:
                    observed_sha = file_sha256(data_path)
                    assert observed_sha == DATA_SHA256, (
                        f"Data SHA-256 mismatch: expected {DATA_SHA256}, observed {observed_sha}"
                    )
                adata = sc.read_h5ad(data_path)
                adata.obs_names = adata.obs_names.astype(str)
                adata.var_names = adata.var_names.astype(str)
                coords = np.asarray(adata.obsm["spatial"], dtype=float)

            source = adata.uns.get("spix_workshop_source", {})
            data_summary = pd.DataFrame([{
                "n_bins": adata.n_obs,
                "n_genes": adata.n_vars,
                "nnz": int(adata.X.nnz) if sp.issparse(adata.X) else int(np.count_nonzero(adata.X)),
                "file_mb": round(Path(data_path).stat().st_size / 1024**2, 2),
                "bin_size_um": source.get("bin_size_um", "unknown"),
                "source_shape": str(source.get("full_shape", "unknown")),
            }])
            display(data_summary)
            """
        ),
        md(
            """
            ## 3. 빠른 QC와 공통 helper

            오늘의 목적은 QC 자체가 아니라 분석 흐름을 따라가는 것입니다. 그래도
            counts와 검출 gene 수가 공간적으로 이상하게 깨져 있으면 뒤의 결과를
            읽기 어렵기 때문에, 최소한의 분포만 먼저 확인합니다.
            """
        ),
        code(
            """
            def sample_indices(n, max_points=100000, seed=7):
                if n <= max_points:
                    return np.arange(n)
                rng = np.random.default_rng(seed)
                return np.sort(rng.choice(n, size=max_points, replace=False))

            def plot_spatial_values(xy, values, title, cmap="viridis", max_points=100000, s=2):
                idx = sample_indices(len(values), max_points=max_points)
                fig, ax = plt.subplots(figsize=(5, 4.5))
                ax.scatter(xy[idx, 0], xy[idx, 1], s=s, c=np.asarray(values)[idx], cmap=cmap, rasterized=True)
                ax.invert_yaxis()
                ax.set_aspect("equal")
                ax.set_title(title)
                ax.set_xticks([])
                ax.set_yticks([])
                plt.show()

            def expr_vector(anndata_obj, gene, layer="log_norm"):
                matrix = anndata_obj.layers[layer] if layer in anndata_obj.layers else anndata_obj.X
                col = anndata_obj.var_names.get_loc(gene)
                vec = matrix[:, col]
                if sp.issparse(vec):
                    vec = vec.toarray()
                return np.asarray(vec).ravel()

            with timed_stage("quick_qc"):
                total_counts = np.asarray(adata.X.sum(axis=1)).ravel()
                n_genes_by_bin = (
                    np.asarray((adata.X > 0).sum(axis=1)).ravel()
                    if sp.issparse(adata.X)
                    else (adata.X > 0).sum(axis=1)
                )
                plot_spatial_values(coords, np.log1p(total_counts), "log1p(total counts)")
                fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), constrained_layout=True)
                axes[0].hist(total_counts, bins=50, color="#4C78A8")
                axes[0].set_title("UMI counts per 2 um bin")
                axes[1].hist(n_genes_by_bin, bins=50, color="#59A14F")
                axes[1].set_title("Detected genes per 2 um bin")
                plt.show()

            display(pd.DataFrame([{
                "median_counts": float(np.median(total_counts)),
                "median_detected_genes": float(np.median(n_genes_by_bin)),
                "max_counts": float(np.max(total_counts)),
            }]))
            """
        ),
    ]


def standard_tool_cells() -> list:
    return [
        md(
            """
            ## 4. 표준 도구용 teaching subset 준비

            Scanpy와 Squidpy는 많이 쓰이는 표준 도구지만, 2 um bin 500k 전체에
            PCA-neighbor-Leiden-ligrec을 모두 얹으면 Colab 무료 티어에서 수업
            시간이 흔들릴 수 있습니다. 그래서 표준 도구 파트는 같은 500k ROI 안의
            중심부 50k sub-ROI로 진행합니다. 랜덤 샘플이 아니라 서로 붙어 있는
            영역을 쓰기 때문에, 공간 패턴을 해석하는 데 필요한 구조는 남습니다.

            SPIX 파트에서는 500k ROI 전체를 사용합니다.
            """
        ),
        code(
            """
            TOOL_MAX_OBS = int(os.environ.get("SPIX_WORKSHOP_TOOL_MAX_OBS", "50000"))
            TOOL_HVG_N_TOP = int(os.environ.get("SPIX_WORKSHOP_TOOL_HVG_N_TOP", "1200"))
            TOOL_N_PCS = int(os.environ.get("SPIX_WORKSHOP_TOOL_N_PCS", "30"))
            TOOL_N_NEIGHBORS = int(os.environ.get("SPIX_WORKSHOP_TOOL_N_NEIGHBORS", "30"))
            SCANPY_LEIDEN_RESOLUTION = float(os.environ.get("SPIX_WORKSHOP_SCANPY_RESOLUTION", "0.01"))

            def central_subroi_indices(xy, max_obs):
                if xy.shape[0] <= max_obs:
                    return np.arange(xy.shape[0])
                center = np.median(xy, axis=0)
                dist2 = ((xy - center) ** 2).sum(axis=1)
                return np.sort(np.argpartition(dist2, max_obs - 1)[:max_obs])

            with timed_stage("standard_tool_preprocessing_scanpy_squidpy"):
                tool_idx = central_subroi_indices(coords, min(TOOL_MAX_OBS, adata.n_obs))
                tool_adata = adata[tool_idx].copy()
                tool_coords = np.asarray(tool_adata.obsm["spatial"], dtype=float)

                tool_counts = np.asarray(tool_adata.X.sum(axis=1)).ravel()
                keep_nonzero = tool_counts > 0
                if keep_nonzero.sum() < tool_adata.n_obs:
                    tool_adata = tool_adata[keep_nonzero].copy()
                    tool_coords = np.asarray(tool_adata.obsm["spatial"], dtype=float)

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

            print(f"Standard-tool sub-ROI: {tool_adata.n_obs:,} bins x {tool_adata.n_vars:,} genes")
            print(f"Scanpy neighbors={TOOL_N_NEIGHBORS}, Leiden resolution={SCANPY_LEIDEN_RESOLUTION}")
            display(cluster_summary)
            """
        ),
    ]


def svg_cells() -> list:
    return [
        md(
            """
            ## 5. SVG: 공간적으로 조직화된 gene 찾기

            먼저 공간적으로 한쪽에 모여 있거나 경계를 따라 나타나는 gene을
            찾습니다. 이런 gene을 먼저 봐야 뒤에서 cluster를 나눴을 때 그
            cluster가 epithelial, stromal, immune program 중 무엇과 가까운지
            해석할 수 있습니다.

            여기서는 Squidpy의 Moran's I를 사용합니다. 실습 기본값은 marker가
            섞이도록 고른 panel이고, 전체 2,515 genes를 보고 싶으면
            `SPIX_WORKSHOP_SVG_MODE=all`로 바꾸면 됩니다.
            """
        ),
        code(
            """
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
                svg_genes = [g for g in SVG_MARKER_PANEL if g in tool_adata.var_names]
            assert svg_genes, "SVG gene panel에서 현재 데이터에 존재하는 gene이 없습니다."

            with timed_stage("svg_squidpy_moran"):
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

            display(svg_moran.head(15))
            """
        ),
        md(
            """
            ## 5-1. SVG 결과를 공간 위에서 확인하기

            Moran's I가 높으면 주변 bin끼리 발현이 비슷하다는 뜻입니다. 숫자만
            보고 넘어가지 않고, 상위 gene을 다시 tissue 위에 올려서 실제 패턴이
            보이는지 확인합니다.
            """
        ),
        code(
            """
            with timed_stage("svg_gene_maps"):
                genes_to_plot = top_svg_genes[:4]
                fig, axes = plt.subplots(1, len(genes_to_plot), figsize=(4.2 * len(genes_to_plot), 4), constrained_layout=True)
                if len(genes_to_plot) == 1:
                    axes = [axes]
                for ax, gene in zip(axes, genes_to_plot):
                    values = expr_vector(tool_adata, gene)
                    ax.scatter(tool_coords[:, 0], tool_coords[:, 1], s=2, c=values, cmap="magma", rasterized=True)
                    ax.invert_yaxis()
                    ax.set_aspect("equal")
                    ax.set_title(gene)
                    ax.set_xticks([])
                    ax.set_yticks([])
                plt.show()
            """
        ),
        md(
            """
            여기서 중요한 것은 순위표 자체보다 공간적으로 분리되는 marker의
            성격입니다. 이 결과를 옆에 두고 다음 clustering 결과를 해석합니다.
            """
        ),
    ]


def clustering_cells() -> list:
    return [
        md(
            """
            ## 6. Spatial clustering: 조직 domain 나누기

            다음은 expression profile이 비슷한 bin을 묶어 tissue domain을 나누는
            단계입니다. Scanpy에서 가장 익숙한 normalization, HVG, PCA, neighbor
            graph, Leiden clustering 순서로 진행합니다.

            여기서 얻는 cluster는 cell type annotation의 완성본이라기보다,
            공간적으로 구분되는 영역을 marker와 함께 읽기 위한 초안입니다.
            """
        ),
        code(
            """
            with timed_stage("spatial_clustering_scanpy_plot"):
                cluster_codes = tool_adata.obs["scanpy_leiden"].cat.codes.to_numpy()
                fig, ax = plt.subplots(figsize=(5.2, 4.8))
                scatter = ax.scatter(
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

            display(cluster_summary)
            """
        ),
        md(
            """
            ## 6-1. Cluster marker로 domain 의미 읽기

            색깔이 나뉘는 것만으로는 해석이 끝나지 않습니다. 각 cluster에서 어떤
            marker가 올라오는지 확인하고, 앞에서 본 SVG 결과와 같이 읽습니다.
            """
        ),
        code(
            """
            with timed_stage("spatial_clustering_scanpy_markers"):
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
                marker_df = (
                    marker_df.sort_values(["group", "scores"], ascending=[True, False])
                    .groupby("group", as_index=False)
                    .head(5)
                    .loc[:, ["group", "names", "scores", "logfoldchanges", "pvals_adj"]]
                )

            display(marker_df)
            """
        ),
        md(
            """
            여기까지 하면 조직을 몇 개의 domain으로 볼지, 각 domain을 어떤 gene
            program으로 설명할지 정리할 수 있습니다. 다음 단계에서는 이 cluster들
            사이의 ligand-receptor signal을 확인합니다.
            """
        ),
    ]


def cci_cells() -> list:
    return [
        md(
            """
            ## 7. Cell-cell interaction: cluster 사이 ligand-receptor signal

            세 번째는 cluster 사이 ligand-receptor signal입니다. 여기서는
            Squidpy의 `ligrec`을 사용합니다. `ligrec`은 CellPhoneDB-style
            cluster-pair ligand-receptor permutation test를 수행하는 방식이라,
            공간전사체 실습에서 빠르게 보여주기 좋습니다.

            실습 시간에는 OmniPath 전체 DB를 새로 내려받지 않고, colorectal tissue
            예제에서 해석하기 쉬운 후보 pair만 작은 표로 넣어 둡니다. 어떤 pair를
            테스트하는지 직접 확인할 수 있게 하기 위한 선택입니다.
            """
        ),
        code(
            """
            LR_CANDIDATES = pd.DataFrame({
                "source": ["SPP1", "MIF", "CD74", "COL1A1", "COL1A2", "FN1", "LAMB1", "JAG1", "APOE", "LGALS3", "TGFBI"],
                "target": ["CD44", "CD74", "MIF", "ITGB1", "ITGB1", "ITGA5", "ITGB1", "NOTCH1", "LRP1", "ITGB1", "ITGB5"],
            })
            ligrec_interactions = LR_CANDIDATES[
                LR_CANDIDATES["source"].isin(tool_adata.var_names)
                & LR_CANDIDATES["target"].isin(tool_adata.var_names)
            ].copy()
            assert not ligrec_interactions.empty, "현재 gene set에서 사용할 수 있는 LR 후보가 없습니다."

            LIGREC_PERMUTATIONS = int(os.environ.get("SPIX_WORKSHOP_LIGREC_PERMUTATIONS", "20"))

            def tidy_ligrec_matrix(matrix, value_name):
                matrix = matrix.copy()
                row_names = [name if name is not None else f"row_{i}" for i, name in enumerate(matrix.index.names)]
                matrix.index.names = row_names
                if matrix.columns.nlevels == 2:
                    matrix.columns.names = ["sender_cluster", "receiver_cluster"]
                    stacked = matrix.stack(["sender_cluster", "receiver_cluster"], dropna=False)
                else:
                    matrix.columns.name = "cluster_pair"
                    stacked = matrix.stack(dropna=False)
                return stacked.rename(value_name).reset_index()

            with timed_stage("cell_cell_interaction_squidpy_ligrec"):
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
                ligrec_means = tidy_ligrec_matrix(ligrec_result["means"], "mean_expression")
                ligrec_pvalues = tidy_ligrec_matrix(ligrec_result["pvalues"], "pvalue")
                merge_keys = [c for c in ligrec_means.columns if c != "mean_expression"]
                ligrec_table = ligrec_means.merge(ligrec_pvalues, on=merge_keys, how="left")
                ligrec_table = ligrec_table.replace([np.inf, -np.inf], np.nan)
                ligrec_table = ligrec_table.dropna(subset=["mean_expression"])
                if "source" in ligrec_table.columns and "target" in ligrec_table.columns:
                    ligrec_table["pair"] = ligrec_table["source"].astype(str) + "-" + ligrec_table["target"].astype(str)
                else:
                    ligrec_table["pair"] = ligrec_table.iloc[:, 0].astype(str)
                ligrec_table["pvalue_status"] = np.where(ligrec_table["pvalue"].isna(), "not_tested", "tested")
                ligrec_table["pvalue_sort"] = ligrec_table["pvalue"].fillna(1.0)
                ligrec_table = ligrec_table.sort_values(["pvalue_sort", "mean_expression"], ascending=[True, False])
                ligrec_display = ligrec_table.drop(columns=["pvalue_sort"])

            display(ligrec_interactions)
            display(ligrec_display.head(20))
            """
        ),
        md(
            """
            ## 7-1. 상위 LR pair를 cluster-pair matrix로 보기

            cluster-pair가 많아지면 긴 표만으로는 보기 어렵습니다. 상위 pair 하나를
            골라 sender cluster와 receiver cluster 조합으로 펼쳐 봅니다.
            """
        ),
        code(
            """
            with timed_stage("cell_cell_interaction_heatmap"):
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

            display(heatmap_table)
            """
        ),
        md(
            """
            이 결과만으로 cell-cell communication이 확정되는 것은 아닙니다. 다만
            어떤 cluster 조합에서 어떤 LR 후보를 더 검토할지 정하는 데에는 충분히
            유용합니다.
            """
        ),
    ]


def spix_cells() -> list:
    return [
        md(
            """
            ## 8. SPIX: 2 um bins를 multiscale tissue unit으로 바꾸기

            앞에서는 표준 도구로 SVG, clustering, CCI를 각각 확인했습니다. 이제
            같은 Visium HD 2 um 자료를 SPIX 방식으로 처리합니다. 2 um bin을 그대로
            쓰면 관측치가 너무 많아지고, scale을 바꿔 가며 해석하기도 어렵습니다.
            SPIX는 expression embedding과 공간 구조를 함께 사용해 여러 물리적
            scale의 tissue unit을 만듭니다.

            아래 코드는 `SPIX/VisiumHD_CRC_P2/VisiumHD_CRC_P2.ipynb`와
            `visiumhd_fig2a.py`의 VisiumHD P2 경로에 맞춘 것입니다. Colab 실습
            때문에 데이터 크기와 `N_JOBS`만 조절했습니다.

            실행 순서는 `embedding -> graph smoothing -> equalization -> image cache
            -> image_plot_slic multiscale segmentation -> multiscale Moran/SVG`
            입니다.
            """
        ),
        code(
            """
            SPIX_EMBEDDING_DIMS = int(os.environ.get("SPIX_WORKSHOP_SPIX_EMBEDDING_DIMS", "30"))
            SPIX_EMBEDDING_CHANNELS = list(range(SPIX_EMBEDDING_DIMS))
            SPIX_RUN_TUNING = os.environ.get("SPIX_WORKSHOP_SPIX_RUN_TUNING", "0").lower() in {"1", "true", "yes"}
            SPIX_GRAPH_K = int(os.environ.get("SPIX_WORKSHOP_SPIX_GRAPH_K", "20"))
            SPIX_GRAPH_T = int(os.environ.get("SPIX_WORKSHOP_SPIX_GRAPH_T", "10"))
            SPIX_EQ_SLEFT = float(os.environ.get("SPIX_WORKSHOP_SPIX_EQ_SLEFT", "2.0"))
            SPIX_EQ_SRIGHT = float(os.environ.get("SPIX_WORKSHOP_SPIX_EQ_SRIGHT", "2.0"))
            RESOLUTIONS_UM = [
                float(x.strip())
                for x in os.environ.get(
                    "SPIX_WORKSHOP_RESOLUTIONS_UM",
                    "2,8,16,30,40,50,80,100,150,200,250,300,350,400,450,500",
                ).split(",")
                if x.strip()
            ]
            PITCH_UM = float(os.environ.get("SPIX_WORKSHOP_PITCH_UM", "2.0"))
            SPIX_MAX_WORKERS = int(os.environ.get("SPIX_WORKSHOP_SPIX_MAX_WORKERS", str(N_JOBS)))
            SPIX_CACHE_NAMESPACE = "visiumhd_crc_p2_workshop_colab"
            SEGMENT_DIR = OUTPUT_DIR / "spix_multiscale_segments"
            SPIX_CACHE_DIR = OUTPUT_DIR / "image_cache"

            with timed_stage("spix_generate_embeddings"):
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

            with timed_stage("spix_smoothing_selection"):
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
                    smoothing_selection = {
                        "recommendation": {
                            "params": {"graph_k": SPIX_GRAPH_K, "graph_t": SPIX_GRAPH_T},
                            "summary": f"graph_k={SPIX_GRAPH_K}, graph_t={SPIX_GRAPH_T}",
                            "source": "fixed fallback from VisiumHD reproduction code with run_tuning=False",
                        }
                    }
                    smooth_params = {"graph_k": SPIX_GRAPH_K, "graph_t": SPIX_GRAPH_T}
                (OUTPUT_DIR / "spix_smoothing_selection.json").write_text(json.dumps(smoothing_selection, indent=2, default=str))

            with timed_stage("spix_smooth_image"):
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

            with timed_stage("spix_equalization_selection"):
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
                    equalization_selection = {
                        "best": {"sleft": SPIX_EQ_SLEFT, "sright": SPIX_EQ_SRIGHT},
                        "recommendation": {
                            "params": {"sleft": SPIX_EQ_SLEFT, "sright": SPIX_EQ_SRIGHT},
                            "summary": f"BalanceSimplest sleft={SPIX_EQ_SLEFT}, sright={SPIX_EQ_SRIGHT}",
                            "source": "fixed fallback from VisiumHD reproduction code with run_tuning=False",
                        },
                    }
                    equalization_params = {"sleft": SPIX_EQ_SLEFT, "sright": SPIX_EQ_SRIGHT}
                (OUTPUT_DIR / "spix_equalization_selection.json").write_text(json.dumps(equalization_selection, indent=2, default=str))

            with timed_stage("spix_equalize_and_cache_image"):
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

            with timed_stage("spix_multiscale_segmentation"):
                SPIX.sp.precompute_multiscale_segments(
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

            with timed_stage("spix_multiscale_moran_svg"):
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
                spix_top_rows = []
                for col in spix_rank_df.columns:
                    scale_id = col.replace("rank_", "")
                    top = spix_rank_df[col].dropna().sort_values().head(5)
                    spix_top_rows.append(pd.DataFrame({"scale": scale_id, "gene": top.index, "rank": top.values}))
                spix_top_svg_table = pd.concat(spix_top_rows, ignore_index=True)

            display(segment_index[[
                "scale_id",
                "resolution",
                "requested_n_segments",
                "observed_obs_n_segments",
                "seconds",
            ]])
            display(spix_top_svg_table)
            """
        ),
        md(
            """
            ## 8-1. VisiumHD Fig2A scale 확인

            P2 원본 노트북은 2, 8, 16, 30, 40, 50, 80, 100, 150, 200,
            250, 300, 350, 400, 450, 500 um scale을 계산합니다. 화면에서는 먼저
            Fig2A에서 보기 좋은 50, 100, 500 um scale을 확인합니다.
            """
        ),
        code(
            """
            def resolve_segment_path(row):
                path = Path(str(row["path"]))
                if path.is_absolute():
                    return path
                return (SEGMENT_DIR / path.name).resolve()

            def add_spix_labels(anndata_obj, segment_table):
                for _, row in segment_table.iterrows():
                    scale_id = str(row["scale_id"])
                    if str(row.get("native_identity", "")).lower() == "true" or str(row.get("path", "")) == "__native_identity__":
                        continue
                    z = np.load(resolve_segment_path(row), allow_pickle=True)
                    labels = z["seg_codes"].astype(str)
                    anndata_obj.obs[f"spix_{scale_id}"] = pd.Categorical(labels)

            with timed_stage("spix_scale_overview"):
                add_spix_labels(adata, segment_index)
                plot_scales_um = [
                    float(x.strip())
                    for x in os.environ.get("SPIX_WORKSHOP_SPIX_PLOT_SCALES_UM", "50,100,500").split(",")
                    if x.strip()
                ]
                plot_segment_index = segment_index[segment_index["resolution"].astype(float).isin(plot_scales_um)].copy()
                if plot_segment_index.empty:
                    plot_segment_index = segment_index[segment_index["native_identity"].astype(str).str.lower() != "true"].head(3).copy()
                fig, axes = plt.subplots(1, len(plot_segment_index), figsize=(4.4 * len(plot_segment_index), 4), constrained_layout=True)
                if len(plot_segment_index) == 1:
                    axes = [axes]
                idx = sample_indices(adata.n_obs, max_points=140000)
                for ax, (_, row) in zip(axes, plot_segment_index.iterrows()):
                    key = f"spix_{row['scale_id']}"
                    codes = adata.obs[key].cat.codes.to_numpy()
                    ax.scatter(coords[idx, 0], coords[idx, 1], s=2, c=codes[idx], cmap="tab20", rasterized=True)
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
                spix_scale_summary["mean_bins_per_unit"] = adata.n_obs / spix_scale_summary["observed_obs_n_segments"]
                spix_scale_summary["approx_scale_area_um2"] = spix_scale_summary["resolution"] ** 2

            display(spix_scale_summary)
            """
        ),
        md(
            """
            SPIX 결과의 핵심은 gene list가 아니라 분석 단위입니다. 2 um bin을
            그대로 쓰기 어려운 상황에서 scale이 명시된 tissue unit을 만들고, 이후
            SVG, clustering, CCI, enrichment 분석을 같은 단위 위에서 다시 설계할
            수 있습니다.
            """
        ),
    ]


def final_cells() -> list:
    return [
        md(
            """
            ## 9. 실행 시간 저장

            마지막으로 실행 시간과 주요 산출물 위치를 JSON으로 저장합니다. Colab
            무료 티어에서 실제로 걸린 시간을 확인할 때 이 파일을 사용합니다.
            """
        ),
        code(
            """
            with timed_stage("final_report"):
                elapsed = round(time.perf_counter() - RUN_STARTED_AT, 2)
                report = {
                    "lecture_id": LECTURE_ID,
                    "topic": "SVG, spatial clustering, cell-cell interaction, SPIX",
                    "validation_passed": True,
                    "elapsed_seconds": elapsed,
                    "runtime": runtime_snapshot(),
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
                print("Validation passed")
                print("Report:", report_path)
                print(json.dumps(report, indent=2)[:2000])

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
    name = COMBINED_NOTEBOOK
    nb = new_notebook(name)
    nb["cells"] = [
        md(
            """
            # 공간전사체 분석 실습: SVG, spatial clustering, CCI, SPIX

            2026 제20회 통계유전학 워크샵 공간전사체 분석 실습 중 최휘수 담당
            파트입니다.

            Session 4에서는 많이 쓰이는 표준 도구로 SVG, spatial clustering,
            cell-cell interaction을 연결해서 봅니다. Session 6에서는 같은 Visium
            HD P2 자료를 SPIX 파이프라인으로 처리해 multiscale tissue unit을
            만듭니다.

            실습 순서는 다음과 같습니다.

            1. **SVG**: 공간적으로 조직화된 gene 찾기
            2. **Spatial clustering**: expression 기반 tissue domain 나누기
            3. **Cell-cell interaction**: cluster 사이 ligand-receptor signal 확인
            4. **SPIX**: 2 um bin을 multiscale tissue unit으로 변환
            """
        ),
        md(
            """
            ## 데이터 크기 선택

            원본 P2 2 um 전체 데이터는 약 8.7M bins입니다. 로컬 high-memory
            서버에서는 `8M x 2515 genes` 경로가 동작했지만, 12GB 안팎의 Colab
            무료 티어에서는 full read와 selected-gene materialization이 모두
            실패했습니다.

            그래서 실습 기본 데이터는 `500,000 bins x 2,515 genes` native 2 um
            ROI로 맞췄습니다. 표준 도구 파트는 같은 ROI 안의 50k 연속 sub-ROI로
            진행하고, SPIX 파트는 500k ROI 전체를 사용합니다.
            """
        ),
    ]
    nb["cells"].extend(setup_cells(data_url, data_sha256))
    nb["cells"].extend(standard_tool_cells())
    nb["cells"].extend(svg_cells())
    nb["cells"].extend(clustering_cells())
    nb["cells"].extend(cci_cells())
    nb["cells"].extend(spix_cells())
    nb["cells"].extend(final_cells())
    return name, nb


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

    filename, nb = combined_notebook(args.data_url, data_sha256)
    path = notebook_dir / filename
    write_notebook(path, nb)
    print(json.dumps({"written": [str(path)], "data_sha256": data_sha256}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
