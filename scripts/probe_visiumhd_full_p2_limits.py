#!/usr/bin/env python
"""Probe whether the full Visium HD P2 2 um object is Colab-feasible.

This script is intentionally stage-based.  A full run can fail by memory limit,
timeout, or kernel termination; writing a JSONL event before and after each
stage leaves usable evidence even when the last stage does not complete.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import resource
import sys
import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Any


DEFAULT_FULL_H5AD = (
    "/home/Data_Drive_8TB/chs1151/SPIX_0426/"
    "figure_reproduction_spix_api_0622/intermediates/visiumhd_p2_crc_2um/full/"
    "visiumhd_p2_crc_2um.full.spix_api_intermediate.h5ad"
)
DEFAULT_REFERENCE_H5AD = (
    "/home/Data_Drive_8TB/chs1151/SPIX_0426/spix-colab-workshop/data/"
    "visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-h5ad", default=DEFAULT_FULL_H5AD)
    parser.add_argument("--reference-h5ad", default=DEFAULT_REFERENCE_H5AD)
    parser.add_argument("--output-dir", default="outputs/full_p2_probe")
    parser.add_argument("--mode", choices=["metadata", "read-full", "selected-workflow"], required=True)
    parser.add_argument("--genes", choices=["reference", "all"], default="reference")
    parser.add_argument("--max-obs", type=int, default=None)
    parser.add_argument("--n-jobs", type=int, default=2)
    parser.add_argument("--embedding-dims", type=int, default=30)
    parser.add_argument("--resolutions-um", default="2,8,16,30,40,50,80,100,150,200,250,300,350,400,450,500")
    parser.add_argument("--graph-k", type=int, default=20)
    parser.add_argument("--graph-t", type=int, default=10)
    parser.add_argument("--eq-sleft", type=float, default=2.0)
    parser.add_argument("--eq-sright", type=float, default=2.0)
    parser.add_argument("--pitch-um", type=float, default=2.0)
    parser.add_argument("--skip-embedding", action="store_true")
    parser.add_argument("--skip-cache", action="store_true")
    parser.add_argument("--skip-segmentation", action="store_true")
    parser.add_argument("--skip-moran", action="store_true")
    return parser.parse_args()


def configure_threads(n_jobs: int) -> None:
    for var in [
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ]:
        os.environ.setdefault(var, str(n_jobs))
    os.environ.setdefault("SPIX_ENABLE_THREAD_CAP", "1")
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_spix_full_probe")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl_spix_full_probe")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg_spix_full_probe")


def kb_to_gb(kb: float) -> float:
    return round(kb / 1024 / 1024, 3)


def proc_status() -> dict[str, float]:
    out: dict[str, float] = {}
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith(("VmRSS:", "VmHWM:", "VmSize:", "VmPeak:")):
                key, value = line.split(":", 1)
                out[key] = kb_to_gb(float(value.strip().split()[0]))
    except Exception:
        pass
    return out


def meminfo() -> dict[str, float]:
    out: dict[str, float] = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}:
                out[key] = kb_to_gb(float(value.strip().split()[0]))
    except Exception:
        pass
    return out


def maxrss_gb() -> float:
    return kb_to_gb(float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


class StageLogger:
    def __init__(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        self.path = output_dir / "full_p2_probe_events.jsonl"

    def write(self, event: dict[str, Any]) -> None:
        payload = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "rss_gb": proc_status(),
            "ru_maxrss_gb": maxrss_gb(),
            "system_memory_gb": meminfo(),
            **event,
        }
        with self.path.open("a") as fh:
            fh.write(json.dumps(jsonable(payload), sort_keys=True) + "\n")
            fh.flush()
        print(json.dumps(jsonable(payload), sort_keys=True), flush=True)

    @contextmanager
    def stage(self, name: str, **extra: Any):
        start = time.perf_counter()
        self.write({"event": "start", "stage": name, **extra})
        try:
            yield
        except Exception as exc:
            self.write(
                {
                    "event": "error",
                    "stage": name,
                    "seconds": round(time.perf_counter() - start, 3),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc(limit=8),
                }
            )
            raise
        else:
            gc.collect()
            self.write(
                {
                    "event": "end",
                    "stage": name,
                    "seconds": round(time.perf_counter() - start, 3),
                }
            )


def ensure_spix_importable() -> None:
    if "SPIX" in sys.modules:
        return
    cwd = Path.cwd().resolve()
    for root in [cwd, *cwd.parents]:
        if (root / "SPIX" / "__init__.py").exists():
            sys.path.insert(0, str(root))
            return


def runtime_info(args: argparse.Namespace) -> dict[str, Any]:
    affinity = None
    try:
        affinity = len(os.sched_getaffinity(0))
    except Exception:
        pass
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "cpu_affinity": affinity,
        "n_jobs": args.n_jobs,
        "mode": args.mode,
        "genes": args.genes,
        "max_obs": args.max_obs,
        "full_h5ad": str(Path(args.full_h5ad)),
        "full_h5ad_gb": round(Path(args.full_h5ad).stat().st_size / 1024**3, 3),
        "reference_h5ad": str(Path(args.reference_h5ad)),
    }


def summarize_sparse(name: str, matrix: Any) -> dict[str, Any]:
    import scipy.sparse as sp

    payload = {"name": name, "shape": tuple(int(x) for x in matrix.shape)}
    if sp.issparse(matrix):
        payload.update(
            {
                "format": matrix.getformat(),
                "nnz": int(matrix.nnz),
                "data_dtype": str(matrix.data.dtype),
                "indices_dtype": str(matrix.indices.dtype),
                "indptr_dtype": str(matrix.indptr.dtype) if hasattr(matrix, "indptr") else None,
                "csr_arrays_gb": round(
                    (
                        matrix.data.nbytes
                        + getattr(matrix, "indices", []).nbytes
                        + getattr(matrix, "indptr", []).nbytes
                    )
                    / 1024**3,
                    3,
                ),
            }
        )
    else:
        payload.update({"format": "dense", "dtype": str(matrix.dtype), "nbytes_gb": round(matrix.nbytes / 1024**3, 3)})
    return payload


def import_stack(logger: StageLogger):
    with logger.stage("import_stack"):
        import anndata as ad
        import numpy as np
        import pandas as pd
        import scanpy as sc
        import scipy.sparse as sp

    return ad, np, pd, sc, sp


def read_reference_genes(reference_h5ad: Path, logger: StageLogger) -> list[str]:
    import anndata as ad

    with logger.stage("read_reference_gene_set"):
        ref = ad.read_h5ad(reference_h5ad, backed="r")
        genes = [str(x) for x in ref.var_names]
        ref.file.close()
    return genes


def open_full_backed(ad, full_h5ad: Path, logger: StageLogger):
    with logger.stage("open_full_h5ad_backed"):
        full = ad.read_h5ad(full_h5ad, backed="r")
        logger.write(
            {
                "event": "metadata",
                "stage": "open_full_h5ad_backed",
                "shape": tuple(int(x) for x in full.shape),
                "layers": list(full.layers.keys()),
                "obsm": list(full.obsm.keys()),
                "obs_columns": list(full.obs.columns[:30]),
                "n_obs_columns": int(len(full.obs.columns)),
                "n_var_columns": int(len(full.var.columns)),
            }
        )
    return full


def selected_obs_index(n_obs: int, max_obs: int | None):
    if max_obs is None or max_obs >= n_obs:
        return slice(None)
    return slice(0, int(max_obs))


def materialize_selected_adata(args: argparse.Namespace, ad, np, sp, full, logger: StageLogger):
    if args.genes == "reference":
        genes: Any = read_reference_genes(Path(args.reference_h5ad), logger)
        missing = [g for g in genes if g not in full.var_names]
        if missing:
            raise ValueError(f"{len(missing)} reference genes missing from full object; first={missing[:5]}")
    else:
        genes = slice(None)

    obs_index = selected_obs_index(full.n_obs, args.max_obs)
    with logger.stage("materialize_selected_adata", genes=args.genes, max_obs=args.max_obs):
        view = full[obs_index, genes]
        x = view.X
        x = x.copy() if sp.issparse(x) else np.asarray(x).copy()
        adata = ad.AnnData(X=x, obs=view.obs.copy(), var=view.var.copy())
        if "spatial" in view.obsm:
            adata.obsm["spatial"] = np.asarray(view.obsm["spatial"], dtype=np.float32).copy()
        if "log_norm" in view.layers:
            layer = view.layers["log_norm"]
            adata.layers["log_norm"] = layer.copy() if sp.issparse(layer) else np.asarray(layer).copy()
        logger.write({"event": "matrix_summary", "stage": "materialize_selected_adata", "X": summarize_sparse("X", adata.X)})
        if "log_norm" in adata.layers:
            logger.write(
                {
                    "event": "matrix_summary",
                    "stage": "materialize_selected_adata",
                    "log_norm": summarize_sparse("log_norm", adata.layers["log_norm"]),
                }
            )
        logger.write(
            {
                "event": "adata_summary",
                "stage": "materialize_selected_adata",
                "shape": tuple(int(x) for x in adata.shape),
                "obs_columns": list(adata.obs.columns[:30]),
                "obsm": list(adata.obsm.keys()),
                "layers": list(adata.layers.keys()),
            }
        )
    return adata


def run_selected_workflow(args: argparse.Namespace, adata, logger: StageLogger) -> None:
    ensure_spix_importable()
    with logger.stage("import_spix"):
        import numpy as np
        import pandas as pd
        import SPIX

    dims = list(range(args.embedding_dims))
    output_dir = Path(args.output_dir)
    segment_dir = output_dir / "segments"
    resolutions = [float(x.strip()) for x in args.resolutions_um.split(",") if x.strip()]

    if not args.skip_embedding:
        with logger.stage("spix_generate_embeddings", n_jobs=args.n_jobs, embedding_dims=args.embedding_dims):
            adata = SPIX.tm.generate_embeddings(
                adata,
                dim_reduction="PCA",
                normalization="log_norm",
                dimensions=args.embedding_dims,
                nfeatures=min(2000, adata.n_vars),
                use_coords_as_tiles=True,
                coords_rescale_to_nn=False,
                coords_max_gap_factor=None,
                raster_random_seed=42,
                force=True,
                n_jobs=args.n_jobs,
                verbose=True,
            )
            logger.write(
                {
                    "event": "embedding_summary",
                    "stage": "spix_generate_embeddings",
                    "obsm": {k: tuple(int(x) for x in v.shape) for k, v in adata.obsm.items() if hasattr(v, "shape")},
                }
            )

        with logger.stage("spix_smooth_image", n_jobs=args.n_jobs, graph_k=args.graph_k, graph_t=args.graph_t):
            adata = SPIX.ip.smooth_image(
                adata,
                methods=["graph"],
                embedding="X_embedding",
                embedding_dims=dims,
                output="X_embedding_smooth",
                approx_mode="grid",
                approx_target_n=2_000_000,
                approx_max_bins=2_000_000,
                graph_k=args.graph_k,
                graph_t=args.graph_t,
                n_jobs=args.n_jobs,
                backend="threads",
                implementation="auto",
                rescale_mode="final",
            )

        with logger.stage("spix_equalize_image", n_jobs=args.n_jobs, sleft=args.eq_sleft, sright=args.eq_sright):
            adata = SPIX.ip.equalize_image(
                adata,
                embedding="X_embedding_smooth",
                output="X_embedding_equalize",
                dimensions=dims,
                method="BalanceSimplest",
                sleft=args.eq_sleft,
                sright=args.eq_sright,
                n_jobs=args.n_jobs,
                verbose=True,
            )

    if not args.skip_cache:
        with logger.stage("spix_cache_embedding_image"):
            SPIX.ip.cache_embedding_image(
                adata,
                embedding="X_embedding_equalize",
                dimensions=dims,
                key="image_plot_slic",
                coordinate_mode="spatial",
                origin=True,
                brighten_continuous=True,
                continuous_gamma=0.7,
                runtime_fill_from_boundary=True,
                runtime_fill_closing_radius=1,
                runtime_fill_holes=True,
                resolve_center_collisions=True,
                store="memmap",
                cache_storage="float32_memmap",
                memmap_dir=str(output_dir / "image_cache"),
                cache_namespace="visiumhd_crc_p2_full_probe",
                show=False,
                verbose=True,
            )

    if not args.skip_segmentation:
        with logger.stage("spix_multiscale_segmentation", n_jobs=args.n_jobs, resolutions_um=resolutions):
            SPIX.sp.precompute_multiscale_segments(
                adata,
                resolutions=resolutions,
                compactness_candidates=[0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.5],
                dimensions=dims,
                embedding="X_embedding_equalize",
                image_cache_key="image_plot_slic",
                out_dir=str(segment_dir),
                pitch_um=args.pitch_um,
                origin=True,
                use_cached_image=True,
                save_compressed=True,
                max_workers=args.n_jobs,
                compactness_search_jobs=args.n_jobs,
                cache_kwargs={
                    "coordinate_mode": "spatial",
                    "runtime_fill_from_boundary": True,
                    "runtime_fill_closing_radius": 1,
                    "runtime_fill_holes": True,
                    "resolve_center_collisions": True,
                    "origin": True,
                    "brighten_continuous": True,
                    "continuous_gamma": 0.7,
                    "store": "memmap",
                    "cache_storage": "float32_memmap",
                    "memmap_dir": str(output_dir / "image_cache"),
                    "cache_namespace": "visiumhd_crc_p2_full_probe",
                },
                verbose=True,
            )
            if (segment_dir / "segments_index.csv").exists():
                index = pd.read_csv(segment_dir / "segments_index.csv")
                logger.write(
                    {
                        "event": "segment_index",
                        "stage": "spix_multiscale_segmentation",
                        "rows": index.to_dict(orient="records"),
                    }
                )

    if not args.skip_moran:
        with logger.stage("spix_multiscale_moran", n_jobs=args.n_jobs):
            SPIX.an.multiscale_moran_ranks(
                adata,
                segments_index_csv=str(segment_dir / "segments_index.csv"),
                out_csv=str(segment_dir / "multiscale_moran_ranks.csv"),
                out_score_csv=str(segment_dir / "multiscale_moran_scores.csv"),
                engine="fast",
                backend="threads",
                n_jobs=args.n_jobs,
                threads_per_process=1,
                moran_thresh=-1.0,
                return_scores=True,
                quiet=False,
            )


def main() -> None:
    args = parse_args()
    configure_threads(args.n_jobs)
    logger = StageLogger(Path(args.output_dir))
    logger.write({"event": "runtime", "stage": "start", **runtime_info(args)})

    ad, np, _pd, _sc, sp = import_stack(logger)
    full_h5ad = Path(args.full_h5ad)

    if args.mode == "read-full":
        with logger.stage("read_full_h5ad_in_memory"):
            adata = ad.read_h5ad(full_h5ad)
            logger.write(
                {
                    "event": "adata_summary",
                    "stage": "read_full_h5ad_in_memory",
                    "shape": tuple(int(x) for x in adata.shape),
                    "layers": list(adata.layers.keys()),
                    "obsm": list(adata.obsm.keys()),
                    "X": summarize_sparse("X", adata.X),
                }
            )
        return

    full = open_full_backed(ad, full_h5ad, logger)
    try:
        if args.mode == "metadata":
            return
        adata = materialize_selected_adata(args, ad, np, sp, full, logger)
    finally:
        full.file.close()

    run_selected_workflow(args, adata, logger)
    logger.write({"event": "done", "stage": "finish"})


if __name__ == "__main__":
    main()
