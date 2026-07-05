#!/usr/bin/env python
"""Write the SPIX Visium HD Colab workshop notebook."""

from __future__ import annotations

import argparse
import hashlib
import json
import textwrap
from pathlib import Path

try:
    import nbformat as nbf
except Exception:  # pragma: no cover - keeps the generator usable in lean envs.
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
        "name": "SPIX_VisiumHD_multiscale_colab.ipynb",
        "provenance": [],
        "toc_visible": True,
    }

    nb["cells"] = [
        md(
            """
            # SPIX Visium HD Mini-Reproduction

            A compact Colab version of the Visium HD multiscale analysis. The full
            slide is too large for a live free-tier exercise, so we use a marker-diverse
            ROI from the public 10x Genomics colon cancer dataset.

            - Fig2A-style tissue-aware multiscale SPIX units.
            - Fig3A/sFig9-style scale-response SVG trajectories.
            - Fig3B/sFig8-style native and segment-averaged gene-expression maps.
            - A Fig5-style check that spatial organization can change by scale and is
              not the same thing as mean expression.

            Use a CPU runtime. The last cell writes a small timing report.
            """
        ),
        md(
            """
            ## What We Will Do

            1. Loaded a small Visium HD ROI as an `AnnData` object.
            2. Converted transcriptomic variation into an SPIX embedding image.
            3. Generated fine, mid, and coarse tissue-aware superpixels.
            4. Ranked spatially variable genes across scales with Moran's I.
            5. Interpreted why the preferred spatial scale can differ by gene.

            This is a mini-reproduction: enough to run live, small enough that a room
            of first-time Colab users should not spend the session waiting on data.
            """
        ),
        md(
            """
            ## Manuscript Result Map

            | Manuscript result | Workshop analogue | Execution mode |
            |---|---|---|
            | Fig2A: Visium HD multiscale SPIX segmentation | Same SPIX route on a marker-diverse CRC P2 ROI | Run live |
            | Fig3A and sFig9: scale-response SVG trajectories | Moran's I trajectories across 48-384 µm scales | Run live |
            | Fig3B and sFig8: native versus SPIX expression maps | Native and segment-averaged maps for top genes | Run live |
            | Fig5A-F: paired NAT/CRC spatial-organization gain | Single-section scale preference and expression/organization contrast | Run live as concept demo |
            | Fig3E/F, Fig4, Fig5G, full supplements | Full reproduction package outputs and manifests | Show as reference |
            """
        ),
        md(
            """
            ## Setup

            The notebook caps CPU threads. Keep the default for the free-tier test.
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
            from pathlib import Path

            RUN_STARTED_AT = time.time()
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
            OUTPUT_DIR = Path("spix_workshop_outputs")
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            def running_in_colab():
                try:
                    import google.colab  # noqa: F401
                    return True
                except Exception:
                    return False

            IN_COLAB = running_in_colab()
            print("Running in Colab:", IN_COLAB)
            print("Thread cap:", N_JOBS)

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

            print(json.dumps(runtime_snapshot(), indent=2))
            """
        ),
        code(
            """
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
                    "Could not import SPIX. Run this notebook inside the SPIX repo, "
                    "or install it with `python -m pip install -e /path/to/SPIX`."
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

            ensure_spix_importable()
            patch_spix_visualization_imports_for_colab()

            import hashlib
            import urllib.request

            import anndata as ad
            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd
            import scanpy as sc
            import scipy.sparse as sp
            import squidpy as sq
            from IPython.display import display

            import SPIX

            print("SPIX import path:", SPIX.__file__)
            """
        ),
        md(
            """
            ## Data

            The bundled `.h5ad` is a spatially contiguous `square_016um` ROI with a
            bounded gene set. It was chosen to include epithelial/secretory, immune,
            stromal, and proliferative signal.
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
                print("Downloading workshop data from:", DATA_URL)
                urllib.request.urlretrieve(DATA_URL, target)
                return target.resolve()

            data_path = locate_or_download_data()
            if DATA_SHA256:
                observed_sha = file_sha256(data_path)
                assert observed_sha == DATA_SHA256, (
                    f"Data SHA-256 mismatch: expected {DATA_SHA256}, observed {observed_sha}"
                )

            adata = sc.read_h5ad(data_path)
            adata.obs_names = adata.obs_names.astype(str)
            adata.var_names = adata.var_names.astype(str)
            print(data_path)
            print(adata)
            print("Source:", adata.uns.get("spix_workshop_source", {}).get("dataset_url", "not recorded"))

            roi_selection = adata.uns.get("spix_workshop_source", {}).get("roi_selection", {})
            if roi_selection:
                print("ROI selection mode:", roi_selection.get("mode"))
                if "marker_groups" in roi_selection and "group_fraction_log" in roi_selection:
                    display(pd.DataFrame({
                        "marker_group": roi_selection["marker_groups"],
                        "log_fraction": roi_selection["group_fraction_log"],
                        "raw_marker_total": roi_selection.get("group_totals", [None] * len(roi_selection["marker_groups"])),
                    }))

            manuscript_reference = {
                "full_reproduction_root": (
                    "figure_reproduction_0608_reproducible/"
                    "revision_0617_plot_gene_expression_v14"
                ),
                "primary_full_manifests": [
                    "manifest/panel_manifest.tsv",
                    "manifest/package_verification.tsv",
                ],
                "workshop_scope": (
                    "Bounded ROI mini-reproduction of the Fig2/Fig3/Fig5 analysis "
                    "logic; not a full manuscript rebuild."
                ),
            }
            print(json.dumps(manuscript_reference, indent=2))
            """
        ),
        code(
            """
            coords = np.asarray(adata.obsm["spatial"], dtype=float)
            total_counts = np.asarray(adata.X.sum(axis=1)).ravel()
            n_genes_by_spot = np.asarray((adata.X > 0).sum(axis=1)).ravel() if sp.issparse(adata.X) else (adata.X > 0).sum(axis=1)

            fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), constrained_layout=True)
            axes[0].scatter(coords[:, 0], coords[:, 1], s=2, c=np.log1p(total_counts), cmap="viridis", rasterized=True)
            axes[0].invert_yaxis()
            axes[0].set_title("ROI total counts")
            axes[0].set_aspect("equal")

            axes[1].hist(total_counts, bins=40, color="#4C78A8")
            axes[1].set_title("Total counts per bin")
            axes[1].set_xlabel("UMIs")

            axes[2].hist(n_genes_by_spot, bins=40, color="#59A14F")
            axes[2].set_title("Detected genes per bin")
            axes[2].set_xlabel("genes")
            plt.show()
            """
        ),
        md(
            """
            ## 1. Build The SPIX Embedding Image

            Convert expression variation into an embedding image for segmentation.
            """
        ),
        code(
            """
            EMBEDDING_DIMS = 16
            EMBEDDING_CHANNELS = list(range(EMBEDDING_DIMS))

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
            """
        ),
        md(
            """
            ## 2. Generate Multiscale SPIX Units

            The scale values are in microns. This ROI uses 16 um Visium HD bins.
            """
        ),
        code(
            """
            SEGMENT_DIR = OUTPUT_DIR / "multiscale_segments"
            RESOLUTIONS_UM = [48, 96, 192, 384]
            PITCH_UM = 16.0

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
            segment_index[[
                "scale_id",
                "resolution",
                "compactness",
                "requested_n_segments",
                "observed_obs_n_segments",
                "seconds",
            ]]
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
            ## 3. Rank SVGs Across Scales

            Aggregate bins to each SPIX scale and compute Moran's I.
            """
        ),
        code(
            """
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

            print(rank_df.shape, score_df.shape)
            rank_df.head()
            """
        ),
        code(
            """
            def top_genes_by_scale(rank_df, n=10):
                rows = []
                for col in rank_df.columns:
                    scale_id = col.replace("rank_", "")
                    top = rank_df[col].dropna().sort_values().head(n)
                    rows.append(pd.DataFrame({"scale": scale_id, "gene": top.index, "rank": top.values}))
                return pd.concat(rows, ignore_index=True)

            top_table = top_genes_by_scale(rank_df, n=10)
            display(top_table)
            """
        ),
        code(
            """
            score_long = (
                score_df.reset_index(names="gene")
                .melt(id_vars="gene", var_name="scale", value_name="moran_i")
                .dropna()
            )
            score_long["scale"] = score_long["scale"].str.replace("I_", "", regex=False)

            selected_genes = list(dict.fromkeys(top_table["gene"].tolist()))[:8]
            plot_df = score_long[score_long["gene"].isin(selected_genes)].copy()

            fig, ax = plt.subplots(figsize=(8, 4.5))
            for gene, sub in plot_df.groupby("gene"):
                sub = sub.set_index("scale").reindex([str(x) if str(x).startswith("r") else f"r{x}" for x in RESOLUTIONS_UM])
                ax.plot(sub.index, sub["moran_i"], marker="o", label=gene)
            ax.set_title("Moran's I trajectory for top workshop genes")
            ax.set_xlabel("SPIX scale")
            ax.set_ylabel("Moran's I")
            ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
            plt.show()
            """
        ),
        code(
            """
            def scale_sort_key(scale_id):
                return int(str(scale_id).replace("r", ""))

            best_scale = (
                score_long.sort_values(["gene", "moran_i"], ascending=[True, False])
                .drop_duplicates("gene")
                .sort_values(["scale", "moran_i"], key=lambda s: s.map(scale_sort_key) if s.name == "scale" else s)
            )
            best_scale_counts = (
                best_scale["scale"]
                .value_counts()
                .rename_axis("best_scale")
                .reset_index(name="n_genes")
                .sort_values("best_scale", key=lambda s: s.map(scale_sort_key))
            )

            display(best_scale_counts)

            top_by_best_scale = (
                best_scale.sort_values(["scale", "moran_i"], ascending=[True, False])
                .groupby("scale", as_index=False)
                .head(5)
                [["scale", "gene", "moran_i"]]
            )
            display(top_by_best_scale)
            """
        ),
        md(
            """
            ## 4. Native And SPIX-Averaged Expression Maps

            Plot native expression beside the SPIX-averaged expression at the gene's
            strongest scale in this ROI.
            """
        ),
        code(
            """
            def expression_vector(adata, gene):
                layer = adata.layers.get("log_norm", adata.X)
                idx = adata.var_names.get_loc(gene)
                vec = layer[:, idx]
                if sp.issparse(vec):
                    vec = vec.toarray()
                return np.asarray(vec).ravel()

            def segment_mean(values, labels):
                df = pd.DataFrame({"value": values, "segment": labels.astype(str)})
                return df.groupby("segment")["value"].transform("mean").to_numpy()

            representative_genes = []
            for scale_id in sorted(top_by_best_scale["scale"].unique(), key=scale_sort_key):
                genes = top_by_best_scale.loc[top_by_best_scale["scale"] == scale_id, "gene"].tolist()
                for gene in genes[:2]:
                    if gene in adata.var_names and gene not in representative_genes:
                        representative_genes.append(gene)
            representative_genes = representative_genes[:6]

            nrows = len(representative_genes)
            fig, axes = plt.subplots(nrows, 2, figsize=(8, max(3, 2.4 * nrows)), constrained_layout=True)
            if nrows == 1:
                axes = np.asarray([axes])

            expression_map_summary = []
            for row_idx, gene in enumerate(representative_genes):
                native = expression_vector(adata, gene)
                row = best_scale.loc[best_scale["gene"] == gene].iloc[0]
                scale_id = str(row["scale"])
                labels = adata.obs[f"spix_{scale_id}"].astype(str).to_numpy()
                averaged = segment_mean(native, labels)

                vmax = np.quantile(native[native > 0], 0.98) if np.any(native > 0) else np.max(native)
                for ax, values, title in [
                    (axes[row_idx, 0], native, f"{gene} native"),
                    (axes[row_idx, 1], averaged, f"{gene} SPIX {scale_id} mean"),
                ]:
                    ax.scatter(
                        coords[:, 0],
                        coords[:, 1],
                        s=2,
                        c=values,
                        cmap="magma",
                        vmin=0,
                        vmax=vmax,
                        rasterized=True,
                    )
                    ax.invert_yaxis()
                    ax.set_aspect("equal")
                    ax.set_title(title)
                    ax.set_xticks([])
                    ax.set_yticks([])

                expression_map_summary.append({
                    "gene": gene,
                    "best_scale": scale_id,
                    "native_mean": float(np.mean(native)),
                    "best_scale_moran_i": float(row["moran_i"]),
                })
            plt.show()

            expression_map_summary = pd.DataFrame(expression_map_summary)
            display(expression_map_summary)
            """
        ),
        md(
            """
            ## 5. Spatial Organization Versus Mean Expression

            A small single-section version of the same idea: expression abundance and
            spatial organization are related, but they are not the same measurement.
            """
        ),
        code(
            """
            mean_expression = pd.Series(
                np.asarray(adata.layers.get("log_norm", adata.X).mean(axis=0)).ravel(),
                index=adata.var_names,
                name="mean_log_expression",
            )
            organization = best_scale.set_index("gene")[["scale", "moran_i"]].rename(
                columns={"scale": "best_scale", "moran_i": "peak_moran_i"}
            )
            expression_organization = organization.join(mean_expression, how="left").dropna()

            fig, ax = plt.subplots(figsize=(6, 4.8))
            for scale_id, sub in expression_organization.groupby("best_scale"):
                ax.scatter(
                    sub["mean_log_expression"],
                    sub["peak_moran_i"],
                    s=8,
                    alpha=0.45,
                    label=scale_id,
                    rasterized=True,
                )
            for gene in representative_genes:
                if gene in expression_organization.index:
                    row = expression_organization.loc[gene]
                    ax.text(row["mean_log_expression"], row["peak_moran_i"], gene, fontsize=8)
            ax.set_xlabel("Mean log-normalized expression")
            ax.set_ylabel("Peak Moran's I across SPIX scales")
            ax.set_title("Expression abundance and spatial organization are distinct")
            ax.legend(title="Best scale", frameon=False, markerscale=2)
            plt.show()

            display(
                expression_organization.sort_values("peak_moran_i", ascending=False)
                .head(15)
                .reset_index()
                .rename(columns={"index": "gene"})
            )
            """
        ),
        md(
            """
            ## Checks

            Basic checks before trusting the run.
            """
        ),
        code(
            """
            assert not segment_index.empty
            assert all(f"spix_{sid}" in adata.obs for sid in segment_index["scale_id"].astype(str))
            assert rank_df.shape[0] > 0 and score_df.shape[0] > 0
            observed_counts = segment_index["observed_obs_n_segments"].to_numpy()
            assert np.all(observed_counts > 0)

            verification = {
                "validation_passed": True,
                "runtime": runtime_snapshot(),
                "elapsed_seconds": round(time.time() - RUN_STARTED_AT, 2),
                "data_file": str(data_path),
                "data_sha256": DATA_SHA256,
                "shape": {"n_obs": int(adata.n_obs), "n_vars": int(adata.n_vars)},
                "resolutions_um": [int(x) for x in RESOLUTIONS_UM],
                "segment_counts": {
                    str(scale): int(count)
                    for scale, count in zip(segment_index["scale_id"], observed_counts)
                },
                "rank_shape": [int(x) for x in rank_df.shape],
                "score_shape": [int(x) for x in score_df.shape],
                "best_scale_counts": dict(zip(best_scale_counts["best_scale"], best_scale_counts["n_genes"].astype(int))),
                "representative_genes": representative_genes,
                "expression_map_summary": expression_map_summary.to_dict(orient="records"),
                "manuscript_reference": manuscript_reference,
                "rank_csv": str(SEGMENT_DIR / "multiscale_moran_ranks.csv"),
                "score_csv": str(SEGMENT_DIR / "multiscale_moran_scores.csv"),
                "free_tier_note": (
                    "Colab account tier is a manual condition. For a true free-tier check, "
                    "run this in a Google account without Colab Pro/Pay As You Go compute units."
                ),
            }
            report_path = OUTPUT_DIR / "colab_free_tier_verification_report.json"
            report_path.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\\n")

            print("Validation passed")
            print("segment counts:", verification["segment_counts"])
            print("elapsed seconds:", verification["elapsed_seconds"])
            print("rank table:", SEGMENT_DIR / "multiscale_moran_ranks.csv")
            print("score table:", SEGMENT_DIR / "multiscale_moran_scores.csv")
            print("verification report:", report_path)
            """
        ),
        md(
            """
            ## Next Steps

            - Try changing `RESOLUTIONS_UM` to see how the fine/mid/coarse units shift.
            - Compare a gene that is strong at fine scale with one that is stronger at
              coarse scale.
            - For the full manuscript, use the full reproduction package. This notebook
              teaches the runnable logic; the complete figures require full-resolution
              raw datasets and target-route provenance.
            """
        ),
    ]
    return nb


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--data-url", default=DEFAULT_DATA_URL)
    parser.add_argument("--data-file", default=None, help="Optional local data file used to compute SHA-256.")
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
