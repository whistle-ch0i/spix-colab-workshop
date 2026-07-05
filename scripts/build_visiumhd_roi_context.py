#!/usr/bin/env python
"""Build a small coordinate file for showing the selected ROI in the full P2 slide."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc


DEFAULT_FULL_H5AD = (
    "/home/Data_Drive_8TB/chs1151/SPIX_0426/"
    "figure_reproduction_spix_api_0622/intermediates/visiumhd_p2_crc_2um/full/"
    "visiumhd_p2_crc_2um.full.spix_api_intermediate.h5ad"
)
DEFAULT_ROI_H5AD = "data/visiumhd_colon_crc_p2_2um_roi_500000x2515.h5ad"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-h5ad", default=DEFAULT_FULL_H5AD)
    parser.add_argument("--roi-h5ad", default=DEFAULT_ROI_H5AD)
    parser.add_argument("--output-csv", default="data/visiumhd_p2_roi_context_downsample.csv")
    parser.add_argument("--output-json", default="data/visiumhd_p2_roi_context.json")
    parser.add_argument("--sample-size", type=int, default=120000)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def coordinate_frame(obs: pd.DataFrame, obsm_spatial=None) -> pd.DataFrame:
    if {"pxl_col_in_fullres", "pxl_row_in_fullres"}.issubset(obs.columns):
        return pd.DataFrame(
            {
                "x": obs["pxl_col_in_fullres"].to_numpy(dtype=float),
                "y": obs["pxl_row_in_fullres"].to_numpy(dtype=float),
            },
            index=obs.index,
        )
    if obsm_spatial is None:
        raise ValueError("No full-resolution coordinate columns or spatial obsm found.")
    spatial = np.asarray(obsm_spatial, dtype=float)
    return pd.DataFrame({"x": spatial[:, 0], "y": spatial[:, 1]}, index=obs.index)


def main() -> None:
    args = parse_args()
    output_csv = Path(args.output_csv)
    output_json = Path(args.output_json)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    full = ad.read_h5ad(args.full_h5ad, backed="r")
    full_coords = coordinate_frame(full.obs)

    finite = np.flatnonzero(np.isfinite(full_coords["x"]) & np.isfinite(full_coords["y"]))
    rng = np.random.default_rng(args.seed)
    if finite.size > args.sample_size:
        selected = np.sort(rng.choice(finite, size=args.sample_size, replace=False))
    else:
        selected = finite

    downsample = full_coords.iloc[selected].copy()
    downsample["kind"] = "full_p2_downsample"
    full_shape = [int(x) for x in full.shape]
    full.file.close()

    roi = sc.read_h5ad(args.roi_h5ad)
    roi_coords = coordinate_frame(roi.obs, roi.obsm.get("spatial"))
    roi_bbox = {
        "x_min": float(roi_coords["x"].min()),
        "x_max": float(roi_coords["x"].max()),
        "y_min": float(roi_coords["y"].min()),
        "y_max": float(roi_coords["y"].max()),
    }

    roi_outline = pd.DataFrame(
        [
            {"x": roi_bbox["x_min"], "y": roi_bbox["y_min"], "kind": "roi_bbox"},
            {"x": roi_bbox["x_max"], "y": roi_bbox["y_min"], "kind": "roi_bbox"},
            {"x": roi_bbox["x_max"], "y": roi_bbox["y_max"], "kind": "roi_bbox"},
            {"x": roi_bbox["x_min"], "y": roi_bbox["y_max"], "kind": "roi_bbox"},
            {"x": roi_bbox["x_min"], "y": roi_bbox["y_min"], "kind": "roi_bbox"},
        ]
    )

    out = pd.concat([downsample.reset_index(drop=True), roi_outline], ignore_index=True)
    out.to_csv(output_csv, index=False)

    metadata = {
        "full_h5ad": str(Path(args.full_h5ad)),
        "roi_h5ad": str(Path(args.roi_h5ad)),
        "full_shape": full_shape,
        "roi_shape": [int(roi.n_obs), int(roi.n_vars)],
        "downsample_points": int(len(downsample)),
        "roi_bbox": roi_bbox,
        "seed": int(args.seed),
    }
    output_json.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
