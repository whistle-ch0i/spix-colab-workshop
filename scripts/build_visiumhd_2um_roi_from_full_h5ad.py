#!/usr/bin/env python
"""Build a Colab probe ROI from a full Visium HD 2 um AnnData file.

The workshop default uses a compact 16 um ROI. This script creates a more
native-resolution probe by taking a spatially contiguous subset from the full
2 um P2 file while keeping the same gene set as the workshop data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import anndata as ad
import numpy as np
import scanpy as sc
import scipy.sparse as sp


DEFAULT_FULL_H5AD = (
    "/home/Data_Drive_8TB/chs1151/SPIX_0426/"
    "figure_reproduction_spix_api_0622/intermediates/visiumhd_p2_crc_2um/full/"
    "visiumhd_p2_crc_2um.full.spix_api_intermediate.h5ad"
)
DEFAULT_REFERENCE_H5AD = (
    "data/visiumhd_colon_crc_p2_square016um_markerdiverse_roi_10000x2500.h5ad"
)


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-h5ad", default=DEFAULT_FULL_H5AD)
    parser.add_argument("--reference-h5ad", default=DEFAULT_REFERENCE_H5AD)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-obs", type=int, required=True)
    parser.add_argument("--bin-size-um", type=float, default=2.0)
    parser.add_argument("--center-pxl-row", type=float, default=None)
    parser.add_argument("--center-pxl-col", type=float, default=None)
    parser.add_argument("--gene-source", choices=["reference"], default="reference")
    parser.add_argument("--compression", default="gzip")
    return parser.parse_args()


def reference_center(reference_h5ad: Path) -> tuple[float, float]:
    ref = sc.read_h5ad(reference_h5ad)
    if {"pxl_row_in_fullres", "pxl_col_in_fullres"}.issubset(ref.obs.columns):
        return (
            float(np.nanmedian(ref.obs["pxl_row_in_fullres"].to_numpy(dtype=float))),
            float(np.nanmedian(ref.obs["pxl_col_in_fullres"].to_numpy(dtype=float))),
        )
    coords = np.asarray(ref.obsm["spatial"], dtype=float)
    return float(np.nanmedian(coords[:, 1])), float(np.nanmedian(coords[:, 0]))


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    reference_path = Path(args.reference_h5ad)
    center_row = args.center_pxl_row
    center_col = args.center_pxl_col
    if center_row is None or center_col is None:
        center_row, center_col = reference_center(reference_path)

    reference = sc.read_h5ad(reference_path)
    gene_names = [str(g) for g in reference.var_names]
    reference_source = reference.uns.get("spix_workshop_source", {})
    reference_roi_selection = reference_source.get("roi_selection", {})

    full = ad.read_h5ad(args.full_h5ad, backed="r")
    missing = [g for g in gene_names if g not in full.var_names]
    if missing:
        full.file.close()
        raise ValueError(f"{len(missing)} reference genes are missing from full h5ad; first={missing[:5]}")

    obs = full.obs
    if {"pxl_row_in_fullres", "pxl_col_in_fullres"}.issubset(obs.columns):
        row = obs["pxl_row_in_fullres"].to_numpy(dtype=np.float32)
        col = obs["pxl_col_in_fullres"].to_numpy(dtype=np.float32)
    else:
        spatial = np.asarray(full.obsm["spatial"], dtype=np.float32)
        col = spatial[:, 0]
        row = spatial[:, 1]

    finite = np.flatnonzero(np.isfinite(row) & np.isfinite(col))
    if finite.size <= args.max_obs:
        selected = finite
    else:
        dist2 = (row[finite] - float(center_row)) ** 2 + (col[finite] - float(center_col)) ** 2
        selected = finite[np.argpartition(dist2, args.max_obs - 1)[: args.max_obs]]
    selected = np.sort(selected.astype(np.int64, copy=False))

    view = full[selected, gene_names]
    x = view.X
    if sp.issparse(x):
        x = x.copy()
    else:
        x = np.asarray(x)

    adata = ad.AnnData(X=x, obs=view.obs.copy(), var=view.var.copy())
    if "spatial" in view.obsm:
        adata.obsm["spatial"] = np.asarray(view.obsm["spatial"], dtype=np.float32).copy()
    elif {"array_col", "array_row"}.issubset(adata.obs.columns):
        adata.obsm["spatial"] = adata.obs[["array_col", "array_row"]].to_numpy(dtype=np.float32)

    full_shape = [int(x) for x in full.shape]
    full.file.close()

    roi_selection = {
        "mode": "nearest_fullres_pixel_contiguous_2um_roi",
        "center_pxl_row": float(center_row),
        "center_pxl_col": float(center_col),
        "source_reference_mode": reference_roi_selection.get("mode", "unknown"),
        "present_markers": reference_roi_selection.get("present_markers", {}),
        "marker_groups": reference_roi_selection.get("marker_groups", []),
    }
    adata.uns["spix_workshop_source"] = {
        "dataset_url": "https://www.10xgenomics.com/datasets/visium-hd-cytassist-11mm-human-colon-cancer-HE",
        "source_h5ad": str(Path(args.full_h5ad)),
        "reference_h5ad": str(reference_path),
        "selection_mode": roi_selection["mode"],
        "bin_size_um": float(args.bin_size_um),
        "center_pxl_row": float(center_row),
        "center_pxl_col": float(center_col),
        "full_shape": full_shape,
        "kept_reference_gene_set": True,
        "roi_selection": roi_selection,
    }

    adata.write_h5ad(output, compression=args.compression)
    manifest = {
        "output": str(output),
        "sha256": sha256sum(output),
        "file_size_bytes": output.stat().st_size,
        "n_obs": int(adata.n_obs),
        "n_vars": int(adata.n_vars),
        "nnz": int(adata.X.nnz) if sp.issparse(adata.X) else int(np.count_nonzero(adata.X)),
        "bin_size_um": float(args.bin_size_um),
        "center_pxl_row": float(center_row),
        "center_pxl_col": float(center_col),
        "source_h5ad": str(Path(args.full_h5ad)),
        "reference_h5ad": str(reference_path),
        "full_shape": full_shape,
    }
    manifest_path = output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
