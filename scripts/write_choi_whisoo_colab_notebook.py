#!/usr/bin/env python
"""Write the Colab notebook for Choi Whisoo's SPIX workshop section."""

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


DATA_FILE = "visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad"
DEFAULT_DATA_URL = (
    "https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main/"
    f"data/{DATA_FILE}"
)


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


def build_notebook(data_url: str, data_sha256: str):
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
    nb["metadata"]["colab"] = {
        "name": "Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb",
        "provenance": [],
        "toc_visible": True,
    }

    nb["cells"] = [
        md(
            """
            # SPIX Colab: Clustering, SVGs, and Spatial LR Signals

            Hands-on notebook for Choi Whisoo's workshop part.

            Start from a small Visium HD colon cancer ROI and walk through four pieces
            from the manuscript analysis:

            - SPIX multiscale units
            - spatial clustering
            - scale-response SVGs
            - spatial ligand-receptor scoring

            The full 2 um slide is too large for a room of free Colab runtimes. This
            version uses a compact public ROI and records timing at each stage.
            """
        ),
        md(
            """
            ## Before Running

            Use a CPU runtime and keep `N_JOBS=2` for the free-tier check.

            The cell-cell interaction section is deliberately small: it scores a curated
            ligand-receptor panel across neighboring SPIX/state regions. The heavier
            LIANA-style analysis is kept for the full manuscript pipeline.
            """
        ),
        md(
            """
            ## 0. Setup

            The timing helper below is here for the Colab check. The last cell writes a
            small JSON report with the runtime and stage timings.
            """
        ),
        code(
            f"""
            import os
            import sys
            import json
            import platform
            import shutil
            import subprocess
            import time
            import importlib.util
            from contextlib import contextmanager
            from pathlib import Path

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

            DATA_FILE = "{DATA_FILE}"
            DATA_URL = os.environ.get("SPIX_WORKSHOP_DATA_URL", "{data_url}")
            DATA_SHA256 = "{data_sha256}"
            OUTPUT_DIR = Path("spix_choi_whisoo_outputs")
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            def running_in_colab():
                try:
                    import google.colab  # noqa: F401
                    return True
                except Exception:
                    return False

            IN_COLAB = running_in_colab()

            def read_meminfo_gb():
                out = {{}}
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
                return {{
                    "running_in_colab": bool(IN_COLAB),
                    "python": sys.version.split()[0],
                    "platform": platform.platform(),
                    "cpu_count": os.cpu_count(),
                    "thread_cap": N_JOBS,
                    "memory_gb": read_meminfo_gb(),
                    "cwd": str(Path.cwd().resolve()),
                    "disk_free_gb": round(disk.free / 1024**3, 2),
                }}

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
                    STAGE_TIMES.append({{"stage": name, "seconds": seconds, "ok": ok}})
                    print(f"[timing] {{name}}: {{seconds}} sec | ok={{ok}}")

            print("Running in Colab:", IN_COLAB)
            print("Thread cap:", N_JOBS)
            print(json.dumps(runtime_snapshot(), indent=2))
            """
        ),
        md(
            """
            ## 1. Load SPIX

            Colab installs SPIX from GitHub. A local checkout uses the package already
            on disk.
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
                    raise ImportError(
                        "Could not import SPIX. Run inside the SPIX repo or install SPIX first."
                    )

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
                    print("Patched SPIX visualization imports for Colab:", init_path)

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
                    print("Patched SPIX analysis imports for Colab:", init_path)

                ensure_spix_importable()
                patch_spix_visualization_imports_for_colab()
                patch_spix_analysis_imports_for_colab()

                import hashlib
                import urllib.request

                import anndata as ad
                import matplotlib.pyplot as plt
                import numpy as np
                import pandas as pd
                import scanpy as sc
                import scipy.sparse as sp
                from scipy.spatial import cKDTree
                from sklearn.cluster import KMeans
                from sklearn.decomposition import PCA
                from sklearn.preprocessing import StandardScaler
                from IPython.display import display

                import SPIX

            print("SPIX import path:", SPIX.__file__)
            """
        ),
        md(
            """
            ## 2. Load The Visium HD ROI

            This ROI comes from the public 10x Genomics Visium HD Human Colon Cancer P2
            dataset. It keeps 10,000 spatial bins and a marker-diverse gene set.
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
                candidates = [
                    Path("data") / DATA_FILE,
                    Path("..") / "data" / DATA_FILE,
                    Path.cwd() / "data" / DATA_FILE,
                    Path("/content") / DATA_FILE,
                ]
                for candidate in candidates:
                    if candidate.exists():
                        return candidate.resolve()
                target = Path("/content" if IN_COLAB else ".") / DATA_FILE
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

            print(data_path)
            print(adata)
            print("Source:", adata.uns.get("spix_workshop_source", {}).get("dataset_url", "not recorded"))
            display(pd.DataFrame([{
                "n_obs": adata.n_obs,
                "n_vars": adata.n_vars,
                "nnz": int(adata.X.nnz) if sp.issparse(adata.X) else int(np.count_nonzero(adata.X)),
                "file_mb": round(Path(data_path).stat().st_size / 1024**2, 2),
            }]))
            """
        ),
        md(
            """
            ## 3. Quick Look

            A small sanity check before segmentation.
            """
        ),
        code(
            """
            with timed_stage("qc_and_marker_overview"):
                total_counts = np.asarray(adata.X.sum(axis=1)).ravel()
                n_genes_by_bin = (
                    np.asarray((adata.X > 0).sum(axis=1)).ravel()
                    if sp.issparse(adata.X)
                    else (adata.X > 0).sum(axis=1)
                )

                fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), constrained_layout=True)
                axes[0].scatter(coords[:, 0], coords[:, 1], s=2, c=np.log1p(total_counts), cmap="viridis", rasterized=True)
                axes[0].invert_yaxis()
                axes[0].set_title("ROI total counts")
                axes[0].set_aspect("equal")
                axes[0].set_xticks([])
                axes[0].set_yticks([])

                axes[1].hist(total_counts, bins=40, color="#4C78A8")
                axes[1].set_title("Total counts per bin")
                axes[1].set_xlabel("UMIs")

                axes[2].hist(n_genes_by_bin, bins=40, color="#59A14F")
                axes[2].set_title("Detected genes per bin")
                axes[2].set_xlabel("genes")
                plt.show()

                roi_selection = adata.uns.get("spix_workshop_source", {}).get("roi_selection", {})
                present_markers = roi_selection.get("present_markers", {})
                marker_summary = pd.DataFrame([
                    {"marker_group": group, "present_markers": ", ".join(genes)}
                    for group, genes in present_markers.items()
                ])

            display(marker_summary)
            """
        ),
        md(
            """
            ## 4. SPIX Units

            We turn expression variation into an embedding image, then segment that
            image at several physical scales.
            """
        ),
        code(
            """
            EMBEDDING_DIMS = 16
            EMBEDDING_CHANNELS = list(range(EMBEDDING_DIMS))
            RESOLUTIONS_UM = [48, 96, 192, 384]
            PITCH_UM = 16.0
            SEGMENT_DIR = OUTPUT_DIR / "multiscale_segments"

            with timed_stage("spix_embedding_and_image_cache"):
                adata = SPIX.tm.generate_embeddings(
                    adata,
                    dim_reduction="PCA",
                    normalization="log_norm",
                    use_counts="raw",
                    dimensions=EMBEDDING_DIMS,
                    nfeatures=min(1200, adata.n_vars),
                    use_hvg_only=True,
                    use_coords_as_tiles=True,
                    force=True,
                    n_jobs=N_JOBS,
                    pca_blas_threads=N_JOBS,
                    pca_sparse_strategy="auto",
                    verbose=True,
                )

                adata = SPIX.ip.equalize_image(
                    adata,
                    embedding="X_embedding",
                    output="X_embedding_equalize",
                    dimensions=EMBEDDING_CHANNELS,
                    method="BalanceSimplest",
                    n_jobs=N_JOBS,
                    verbose=True,
                )

                SPIX.ip.cache_embedding_image(
                    adata,
                    embedding="X_embedding_equalize",
                    dimensions=EMBEDDING_CHANNELS,
                    key="image_plot_slic",
                    coordinate_mode="spatial",
                    origin=True,
                    runtime_fill_from_boundary=True,
                    runtime_fill_closing_radius=3,
                    runtime_fill_holes=False,
                    resolve_center_collisions=True,
                    store="memmap",
                    cache_storage="float32_memmap",
                    memmap_dir=str(OUTPUT_DIR / "image_cache"),
                    show=False,
                    verbose=True,
                )

            with timed_stage("spix_multiscale_segmentation"):
                segment_index = SPIX.sp.precompute_multiscale_segments(
                    adata,
                    resolutions=RESOLUTIONS_UM,
                    compactness_candidates=[0.1, 0.3, 0.6, 1.0],
                    dimensions=EMBEDDING_CHANNELS,
                    embedding="X_embedding_equalize",
                    image_cache_key="image_plot_slic",
                    out_dir=str(SEGMENT_DIR),
                    pitch_um=PITCH_UM,
                    origin=True,
                    use_cached_image=True,
                    native_identity=False,
                    save_compressed=True,
                    max_workers=N_JOBS,
                    compactness_search_jobs=N_JOBS,
                    cache_kwargs={
                        "coordinate_mode": "spatial",
                        "runtime_fill_from_boundary": True,
                        "runtime_fill_closing_radius": 3,
                        "runtime_fill_holes": False,
                        "resolve_center_collisions": True,
                    },
                    verbose=True,
                )
                segment_index = pd.read_csv(SEGMENT_DIR / "segments_index.csv")

            display(segment_index[[
                "scale_id",
                "resolution",
                "compactness",
                "requested_n_segments",
                "observed_obs_n_segments",
                "seconds",
            ]])
            """
        ),
        code(
            """
            def resolve_segment_path(row):
                path = Path(str(row["path"]))
                if path.is_absolute():
                    return path
                return (SEGMENT_DIR / path.name).resolve()

            def add_segment_labels(adata, segment_index):
                for _, row in segment_index.iterrows():
                    scale_id = str(row["scale_id"])
                    z = np.load(resolve_segment_path(row), allow_pickle=True)
                    labels = z["seg_codes"].astype(str)
                    adata.obs[f"spix_{scale_id}"] = pd.Categorical(labels)

            with timed_stage("spix_label_projection_and_plot"):
                add_segment_labels(adata, segment_index)
                fig, axes = plt.subplots(1, len(segment_index), figsize=(4.2 * len(segment_index), 4), constrained_layout=True)
                if len(segment_index) == 1:
                    axes = [axes]
                for ax, (_, row) in zip(axes, segment_index.iterrows()):
                    key = f"spix_{row['scale_id']}"
                    codes = adata.obs[key].cat.codes.to_numpy()
                    ax.scatter(coords[:, 0], coords[:, 1], s=2, c=codes, cmap="tab20", rasterized=True)
                    ax.invert_yaxis()
                    ax.set_aspect("equal")
                    ax.set_title(f"{row['scale_id']} ({int(row['observed_obs_n_segments'])} units)")
                    ax.set_xticks([])
                    ax.set_yticks([])
                plt.show()
            """
        ),
        md(
            """
            ## 5. Spatial Clustering

            Cluster `r96` SPIX units by segment-level expression and project the domain
            labels back to the original bins.
            """
        ),
        code(
            """
            def get_expression_layer(adata):
                layer = adata.layers.get("log_norm", None)
                return layer if layer is not None else adata.X

            def aggregate_by_labels(matrix, labels):
                labels = np.asarray(labels)
                n_groups = int(labels.max()) + 1
                indicator = sp.csr_matrix(
                    (np.ones(labels.size, dtype=np.float32), (labels, np.arange(labels.size))),
                    shape=(n_groups, labels.size),
                )
                matrix = sp.csr_matrix(matrix)
                sums = indicator @ matrix
                sizes = np.bincount(labels, minlength=n_groups).astype(np.float32)
                means = sums.toarray() / np.maximum(sizes[:, None], 1.0)
                return means, sizes

            with timed_stage("spatial_clustering"):
                CLUSTER_SCALE = "r96"
                CLUSTER_KEY = f"spix_{CLUSTER_SCALE}"
                labels = adata.obs[CLUSTER_KEY].cat.codes.to_numpy()
                segment_means, segment_sizes = aggregate_by_labels(get_expression_layer(adata), labels)

                variances = segment_means.var(axis=0)
                top_gene_idx = np.argsort(variances)[-min(800, adata.n_vars):]
                X_domain = segment_means[:, top_gene_idx]
                X_domain = StandardScaler(with_mean=True, with_std=True).fit_transform(X_domain)
                n_pcs = min(15, X_domain.shape[0] - 1, X_domain.shape[1])
                domain_pcs = PCA(n_components=n_pcs, random_state=7).fit_transform(X_domain)

                N_DOMAINS = 6
                domain_labels = KMeans(n_clusters=N_DOMAINS, n_init=10, random_state=7).fit_predict(domain_pcs)
                domain_names = np.asarray([f"D{int(x) + 1}" for x in domain_labels])
                adata.obs["spatial_domain_r96"] = pd.Categorical(domain_names[labels])

                domain_summary = (
                    pd.DataFrame({
                        "spix_segment": np.arange(len(domain_names)),
                        "domain": domain_names,
                        "n_bins": segment_sizes.astype(int),
                    })
                    .groupby("domain", as_index=False)
                    .agg(n_segments=("spix_segment", "count"), n_bins=("n_bins", "sum"))
                    .sort_values("domain")
                )

                fig, ax = plt.subplots(figsize=(5, 4.5))
                codes = adata.obs["spatial_domain_r96"].cat.codes.to_numpy()
                ax.scatter(coords[:, 0], coords[:, 1], s=2, c=codes, cmap="tab10", rasterized=True)
                ax.invert_yaxis()
                ax.set_aspect("equal")
                ax.set_title("Spatial domains from SPIX r96 units")
                ax.set_xticks([])
                ax.set_yticks([])
                plt.show()

            display(domain_summary)
            """
        ),
        md(
            """
            ## 6. SVGs Across Scales

            Moran's I is computed after aggregation to each SPIX scale. Genes that peak
            at different scales become the scale-response SVG examples.
            """
        ),
        code(
            """
            with timed_stage("multiscale_svg_moran"):
                rank_df, score_df = SPIX.an.multiscale_moran_ranks(
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

                def top_genes_by_scale(rank_df, n=10):
                    rows = []
                    for col in rank_df.columns:
                        scale_id = col.replace("rank_", "")
                        top = rank_df[col].dropna().sort_values().head(n)
                        rows.append(pd.DataFrame({"scale": scale_id, "gene": top.index, "rank": top.values}))
                    return pd.concat(rows, ignore_index=True)

                top_table = top_genes_by_scale(rank_df, n=10)
                score_long = (
                    score_df.reset_index(names="gene")
                    .melt(id_vars="gene", var_name="scale", value_name="moran_i")
                    .dropna()
                )
                score_long["scale"] = score_long["scale"].str.replace("I_", "", regex=False)

                best_scale = (
                    score_long.sort_values(["gene", "moran_i"], ascending=[True, False])
                    .drop_duplicates("gene")
                )
                best_scale_counts = (
                    best_scale["scale"]
                    .value_counts()
                    .rename_axis("best_scale")
                    .reset_index(name="n_genes")
                    .sort_values("best_scale", key=lambda s: s.str.replace("r", "").astype(int))
                )

            display(top_table)
            display(best_scale_counts)
            """
        ),
        code(
            """
            with timed_stage("svg_trajectory_plot"):
                selected_genes = list(dict.fromkeys(top_table["gene"].tolist()))[:8]
                plot_df = score_long[score_long["gene"].isin(selected_genes)].copy()

                fig, ax = plt.subplots(figsize=(8, 4.5))
                scale_order = [f"r{x}" for x in RESOLUTIONS_UM]
                for gene, sub in plot_df.groupby("gene"):
                    sub = sub.set_index("scale").reindex(scale_order)
                    ax.plot(sub.index, sub["moran_i"], marker="o", label=gene)
                ax.set_title("Scale-response SVG trajectories")
                ax.set_xlabel("SPIX scale")
                ax.set_ylabel("Moran's I")
                ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
                plt.show()
            """
        ),
        md(
            """
            ## 7. Lightweight Cell-State Labels

            Marker modules give us rough state labels for the spatial LR example.
            """
        ),
        code(
            """
            MARKER_PANELS = {
                "epithelial": ["EPCAM", "KRT8", "KRT19", "TACSTD2", "CEACAM5"],
                "secretory": ["OLFM4", "REG1A", "REG1B", "REG4", "CLCA4", "MUC2", "TFF3"],
                "immune": ["PTPRC", "CD74", "LYZ", "SPP1", "CXCL10"],
                "stromal": ["COL1A1", "COL1A2", "COL3A1", "DCN", "VIM", "TAGLN", "ACTA2", "FMOD"],
                "proliferation": ["MKI67", "TOP2A", "UBE2C", "MCM10", "FOXM1"],
            }

            def expr_vector(adata, gene):
                layer = get_expression_layer(adata)
                idx = adata.var_names.get_loc(gene)
                vec = layer[:, idx]
                if sp.issparse(vec):
                    vec = vec.toarray()
                return np.asarray(vec).ravel()

            with timed_stage("cell_state_scoring"):
                score_columns = {}
                present_panel_genes = {}
                for state, genes in MARKER_PANELS.items():
                    present = [g for g in genes if g in adata.var_names]
                    present_panel_genes[state] = present
                    if present:
                        mat = np.vstack([expr_vector(adata, g) for g in present]).T
                        raw_score = mat.mean(axis=1)
                    else:
                        raw_score = np.zeros(adata.n_obs)
                    std = raw_score.std()
                    score_columns[state] = (raw_score - raw_score.mean()) / (std if std > 0 else 1.0)

                state_scores = pd.DataFrame(score_columns, index=adata.obs_names)
                sorted_scores = np.sort(state_scores.to_numpy(), axis=1)
                top_score = sorted_scores[:, -1]
                margin = sorted_scores[:, -1] - sorted_scores[:, -2]
                state_label = state_scores.idxmax(axis=1).to_numpy()
                state_label[(top_score < 0.2) | (margin < 0.1)] = "ambiguous"
                adata.obs["workshop_state"] = pd.Categorical(state_label)

                state_summary = adata.obs["workshop_state"].value_counts().rename_axis("state").reset_index(name="n_bins")

                fig, ax = plt.subplots(figsize=(5, 4.5))
                codes = adata.obs["workshop_state"].cat.codes.to_numpy()
                ax.scatter(coords[:, 0], coords[:, 1], s=2, c=codes, cmap="tab10", rasterized=True)
                ax.invert_yaxis()
                ax.set_aspect("equal")
                ax.set_title("Marker-derived workshop states")
                ax.set_xticks([])
                ax.set_yticks([])
                plt.show()

            display(pd.DataFrame([
                {"state": state, "genes_used": ", ".join(genes)}
                for state, genes in present_panel_genes.items()
            ]))
            display(state_summary)
            """
        ),
        md(
            """
            ## 8. Spatial Ligand-Receptor Signals

            We score directed neighboring SPIX fine-segment pairs. For each candidate
            pair, the score is the average of
            `ligand(sender segment) x receptor(receiver segment)` over neighboring
            state pairs.
            """
        ),
        code(
            """
            LR_CANDIDATES = [
                ("SPP1", "CD44", "SPP1-CD44"),
                ("MIF", "CD74", "MIF-CD74"),
                ("CD74", "MIF", "CD74-MIF"),
                ("COL1A1", "ITGB1", "COL1A1-ITGB1"),
                ("COL1A2", "ITGB1", "COL1A2-ITGB1"),
                ("LAMB1", "ITGB1", "LAMB1-ITGB1"),
                ("FN1", "ITGA5", "FN1-ITGA5"),
                ("FN1", "ITGAV", "FN1-ITGAV"),
                ("JAG1", "NOTCH1", "JAG1-NOTCH1"),
                ("APOE", "LRP1", "APOE-LRP1"),
                ("LGALS3", "ITGB1", "LGALS3-ITGB1"),
                ("TGFBI", "ITGB5", "TGFBI-ITGB5"),
            ]
            CCI_SEGMENT_SCALE = os.environ.get("SPIX_WORKSHOP_CCI_SEGMENT_SCALE", "r48")
            CCI_RADIUS_UM = float(os.environ.get("SPIX_WORKSHOP_CCI_RADIUS_UM", "160"))

            with timed_stage("cell_cell_interaction_scoring"):
                lr_pairs = [
                    (lig, rec, name)
                    for lig, rec, name in LR_CANDIDATES
                    if lig in adata.var_names and rec in adata.var_names
                ]
                assert lr_pairs, "No ligand-receptor candidate pairs are present in this ROI gene set."

                cci_label_key = f"spix_{CCI_SEGMENT_SCALE}"
                cci_labels = adata.obs[cci_label_key].cat.codes.to_numpy()
                cci_segment_expr, cci_segment_sizes = aggregate_by_labels(get_expression_layer(adata), cci_labels)
                n_cci_segments = cci_segment_expr.shape[0]

                cci_segment_centroids = np.zeros((n_cci_segments, 2), dtype=float)
                np.add.at(cci_segment_centroids[:, 0], cci_labels, coords[:, 0])
                np.add.at(cci_segment_centroids[:, 1], cci_labels, coords[:, 1])
                cci_segment_centroids = cci_segment_centroids / np.maximum(cci_segment_sizes[:, None], 1.0)

                segment_state_votes = (
                    pd.DataFrame({
                        "segment": cci_labels,
                        "state": adata.obs["workshop_state"].astype(str).to_numpy(),
                    })
                    .query("state != 'ambiguous'")
                    .value_counts(["segment", "state"])
                    .rename("n")
                    .reset_index()
                    .sort_values(["segment", "n"], ascending=[True, False])
                    .drop_duplicates("segment")
                )
                cci_segment_states = np.full(n_cci_segments, "ambiguous", dtype=object)
                cci_segment_states[segment_state_votes["segment"].to_numpy()] = segment_state_votes["state"].to_numpy()

                tree = cKDTree(cci_segment_centroids)
                undirected_pairs = tree.query_pairs(r=CCI_RADIUS_UM, output_type="ndarray")
                if undirected_pairs.size == 0:
                    raise RuntimeError("No spatial neighbor pairs found; increase CCI_RADIUS_UM.")
                src = np.concatenate([undirected_pairs[:, 0], undirected_pairs[:, 1]])
                dst = np.concatenate([undirected_pairs[:, 1], undirected_pairs[:, 0]])

                valid = (cci_segment_states[src] != "ambiguous") & (cci_segment_states[dst] != "ambiguous")
                src = src[valid]
                dst = dst[valid]
                sender = cci_segment_states[src]
                receiver = cci_segment_states[dst]
                contact_df = pd.DataFrame({"sender": sender, "receiver": receiver})
                contact_summary = (
                    contact_df.value_counts(["sender", "receiver"])
                    .rename("n_neighbor_edges")
                    .reset_index()
                    .sort_values("n_neighbor_edges", ascending=False)
                )

                cci_rows = []
                for ligand, receptor, pair_name in lr_pairs:
                    ligand_expr = cci_segment_expr[:, adata.var_names.get_loc(ligand)]
                    receptor_expr = cci_segment_expr[:, adata.var_names.get_loc(receptor)]
                    scores = ligand_expr[src] * receptor_expr[dst]
                    tmp = contact_df.copy()
                    tmp["lr_score"] = scores
                    grouped = (
                        tmp.groupby(["sender", "receiver"], as_index=False)
                        .agg(mean_lr_score=("lr_score", "mean"), n_edges=("lr_score", "size"))
                    )
                    grouped["ligand"] = ligand
                    grouped["receptor"] = receptor
                    grouped["lr_pair"] = pair_name
                    cci_rows.append(grouped)

                cci_scores = pd.concat(cci_rows, ignore_index=True)
                cci_scores = cci_scores.sort_values(["mean_lr_score", "n_edges"], ascending=False)
                cci_top = cci_scores.head(25)

            print(f"CCI segment scale: {CCI_SEGMENT_SCALE}")
            print(f"Spatial radius: {CCI_RADIUS_UM} um")
            print(f"Segments used: {n_cci_segments:,}")
            print(f"Directed segment-neighbor edges after removing ambiguous states: {len(src):,}")
            display(pd.DataFrame(lr_pairs, columns=["ligand", "receptor", "lr_pair"]))
            display(contact_summary.head(15))
            display(cci_top)
            """
        ),
        code(
            """
            with timed_stage("cci_plot"):
                heatmap_source = (
                    cci_scores.head(80)
                    .assign(state_pair=lambda d: d["sender"] + " -> " + d["receiver"])
                    .pivot_table(index="lr_pair", columns="state_pair", values="mean_lr_score", aggfunc="max", fill_value=0)
                )
                fig, ax = plt.subplots(figsize=(max(8, 0.55 * heatmap_source.shape[1]), max(4, 0.38 * heatmap_source.shape[0])))
                im = ax.imshow(heatmap_source.to_numpy(), aspect="auto", cmap="magma")
                ax.set_xticks(np.arange(heatmap_source.shape[1]))
                ax.set_xticklabels(heatmap_source.columns, rotation=60, ha="right")
                ax.set_yticks(np.arange(heatmap_source.shape[0]))
                ax.set_yticklabels(heatmap_source.index)
                ax.set_title("Spatial ligand-receptor candidate scores")
                fig.colorbar(im, ax=ax, label="mean ligand(sender) x receptor(receiver)")
                plt.show()
            """
        ),
        md(
            """
            ## 9. Timing Report

            Save this JSON after the Colab run. It is the evidence for the free-tier
            timing check.
            """
        ),
        code(
            """
            with timed_stage("final_report"):
                assert "spatial_domain_r96" in adata.obs
                assert "workshop_state" in adata.obs
                assert not segment_index.empty
                assert rank_df.shape[0] > 0 and score_df.shape[0] > 0
                assert len(cci_scores) > 0

                elapsed_seconds = round(time.perf_counter() - RUN_STARTED_AT, 2)
                report = {
                    "validation_passed": True,
                    "runtime": runtime_snapshot(),
                    "elapsed_seconds": elapsed_seconds,
                    "stage_times": STAGE_TIMES,
                    "data_file": str(data_path),
                    "data_sha256": DATA_SHA256,
                    "shape": {"n_obs": int(adata.n_obs), "n_vars": int(adata.n_vars)},
                    "spix_segment_counts": {
                        str(scale): int(count)
                        for scale, count in zip(
                            segment_index["scale_id"],
                            segment_index["observed_obs_n_segments"],
                        )
                    },
                    "spatial_domain_summary": domain_summary.to_dict(orient="records"),
                    "svg_rank_shape": [int(x) for x in rank_df.shape],
                    "svg_score_shape": [int(x) for x in score_df.shape],
                    "best_scale_counts": dict(zip(best_scale_counts["best_scale"], best_scale_counts["n_genes"].astype(int))),
                    "state_summary": state_summary.to_dict(orient="records"),
                    "lr_pairs_used": [
                        {"ligand": lig, "receptor": rec, "lr_pair": name}
                        for lig, rec, name in lr_pairs
                    ],
                    "cci_segment_scale": CCI_SEGMENT_SCALE,
                    "cci_radius_um": CCI_RADIUS_UM,
                    "cci_top": cci_top.to_dict(orient="records"),
                    "outputs": {
                        "segment_index": str(SEGMENT_DIR / "segments_index.csv"),
                        "moran_ranks": str(SEGMENT_DIR / "multiscale_moran_ranks.csv"),
                        "moran_scores": str(SEGMENT_DIR / "multiscale_moran_scores.csv"),
                    },
                    "free_tier_note": (
                        "A real free-tier check requires running this notebook in a Google "
                        "account without Colab Pro/Pay As You Go/enterprise allocation."
                    ),
                }
                report_path = OUTPUT_DIR / "choi_whisoo_colab_timing_report.json"
                report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\\n")

            timing_table = pd.DataFrame(STAGE_TIMES)
            display(timing_table)
            print("Validation passed")
            print("Total elapsed seconds:", elapsed_seconds)
            print("Timing report:", report_path)
            if IN_COLAB:
                try:
                    from google.colab import files
                    files.download(str(report_path))
                except Exception as exc:
                    print("Could not auto-download report:", exc)
            """
        ),
    ]
    return nb


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--data-url", default=DEFAULT_DATA_URL)
    parser.add_argument("--data-file", default=None, help="Optional data file used to compute SHA-256.")
    parser.add_argument("--data-sha256", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_sha = args.data_sha256 or ""
    if args.data_file:
        data_sha = sha256sum(Path(args.data_file))
    nb = build_notebook(args.data_url, data_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if nbf is not None:
        nbf.write(nb, output)
    else:
        output.write_text(json.dumps(nb, indent=1) + "\n")
    print(output)


if __name__ == "__main__":
    main()
