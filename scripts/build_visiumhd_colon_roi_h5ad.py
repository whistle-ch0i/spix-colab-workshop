#!/usr/bin/env python
"""Build a small Visium HD ROI AnnData file for the SPIX Colab workshop.

The source input is a Space Ranger Visium HD bin directory, for example
`binned_outputs/square_016um`. The output intentionally keeps a spatially
contiguous ROI and a bounded gene set so it can be used in free Colab runtimes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import anndata as ad
import h5py
import numpy as np
import pandas as pd
import scipy.sparse as sp


MARKER_GROUPS = {
    "epithelial_tumor": (
        "EPCAM",
        "KRT8",
        "KRT18",
        "KRT19",
        "TACSTD2",
        "CEACAM5",
    ),
    "intestinal_secretory": (
        "OLFM4",
        "REG1A",
        "REG1B",
        "REG4",
        "CLCA4",
        "MUC2",
        "TFF3",
    ),
    "immune_inflammatory": (
        "PTPRC",
        "CD74",
        "IGHA1",
        "IGHG3",
        "IGHM",
        "IGLC1",
        "LYZ",
        "SPP1",
        "CXCL10",
    ),
    "stromal_matrix": (
        "COL1A1",
        "COL1A2",
        "COL3A1",
        "DCN",
        "VIM",
        "TAGLN",
        "ACTA2",
        "FMOD",
    ),
    "proliferation": (
        "MKI67",
        "TOP2A",
        "UBE2C",
        "MCM10",
        "FOXM1",
    ),
}


DEFAULT_MARKER_GENES = (
    "EPCAM",
    "KRT8",
    "KRT18",
    "MKI67",
    "MCM10",
    "PBX3",
    "OLFM4",
    "SPP1",
    "REG4",
    "MUC2",
    "COL1A1",
    "COL1A2",
    "VIM",
    "PECAM1",
    "PTPRC",
    "CD3D",
    "MS4A1",
    "CEACAM5",
    "TACSTD2",
    "KRT19",
    "REG1A",
    "REG1B",
    "TFF3",
    "CD74",
    "IGHA1",
    "IGHG3",
    "IGLC1",
    "LYZ",
    "CXCL10",
    "COL3A1",
    "DCN",
    "TAGLN",
    "ACTA2",
    "FMOD",
    "TOP2A",
    "UBE2C",
    "FOXM1",
)


def decode_h5_strings(values: Iterable[object]) -> list[str]:
    decoded: list[str] = []
    for value in values:
        if isinstance(value, bytes):
            decoded.append(value.decode("utf-8"))
        else:
            decoded.append(str(value))
    return decoded


def find_positions_path(bin_dir: Path) -> Path:
    candidates = [
        bin_dir / "spatial" / "tissue_positions.parquet",
        bin_dir / "spatial" / "tissue_positions.csv",
        bin_dir / "spatial" / "tissue_positions_list.csv",
        bin_dir.parent.parent / "spatial" / "tissue_positions.parquet",
        bin_dir.parent.parent / "spatial" / "tissue_positions.csv",
        bin_dir.parent.parent / "spatial" / "tissue_positions_list.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"No tissue_positions file found for {bin_dir}")


def read_positions(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        positions = pd.read_parquet(path)
    else:
        positions = pd.read_csv(path)
        if "barcode" not in positions.columns and positions.shape[1] >= 6:
            positions.columns = [
                "barcode",
                "in_tissue",
                "array_row",
                "array_col",
                "pxl_row_in_fullres",
                "pxl_col_in_fullres",
            ][: positions.shape[1]]
    if "barcode" not in positions.columns:
        raise ValueError(f"Could not find barcode column in {path}")
    return positions.dropna(subset=["barcode"]).set_index("barcode")


def choose_spatial_roi(
    coords: np.ndarray,
    *,
    max_obs: int,
    seed: int,
    center_col: float | None,
    center_row: float | None,
) -> np.ndarray:
    finite = np.flatnonzero(np.isfinite(coords).all(axis=1))
    if finite.size == 0:
        raise ValueError("No barcodes with finite spatial coordinates.")
    if finite.size <= max_obs:
        return np.sort(finite.astype(np.int64, copy=False))

    if center_col is not None and center_row is not None:
        center = np.array([float(center_col), float(center_row)], dtype=float)
    else:
        rng = np.random.default_rng(seed)
        center = coords[int(rng.choice(finite))]

    delta = coords[finite] - center
    dist2 = np.einsum("ij,ij->i", delta, delta)
    selected = finite[np.argpartition(dist2, max_obs - 1)[:max_obs]]
    return np.sort(selected.astype(np.int64, copy=False))


def compute_marker_group_scores(
    matrix_h5: Path,
    *,
    feature_names: np.ndarray,
    marker_groups: dict[str, tuple[str, ...]],
) -> tuple[np.ndarray, np.ndarray, dict[str, list[str]]]:
    group_names = list(marker_groups)
    group_lookup = {name: i for i, name in enumerate(group_names)}
    feature_to_group = np.full(feature_names.shape[0], -1, dtype=np.int16)
    present: dict[str, list[str]] = {name: [] for name in group_names}
    for group, genes in marker_groups.items():
        group_idx = group_lookup[group]
        for gene in genes:
            matches = np.flatnonzero(feature_names.astype(str) == str(gene))
            if matches.size:
                feature_to_group[matches] = group_idx
                present[group].append(str(gene))

    with h5py.File(matrix_h5, "r") as h5:
        matrix = h5["matrix"]
        n_barcodes = int(matrix["shape"][()][1])
        data_ds = matrix["data"]
        indices_ds = matrix["indices"]
        indptr_ds = matrix["indptr"]
        scores = np.zeros((n_barcodes, len(group_names)), dtype=np.float32)
        total_counts = np.zeros(n_barcodes, dtype=np.float32)
        for col in range(n_barcodes):
            start = int(indptr_ds[col])
            stop = int(indptr_ds[col + 1])
            if stop <= start:
                continue
            rows = indices_ds[start:stop]
            values = data_ds[start:stop].astype(np.float32, copy=False)
            total_counts[col] = float(values.sum())
            groups = feature_to_group[rows]
            mask = groups >= 0
            if np.any(mask):
                np.add.at(scores[col], groups[mask], values[mask])
    return scores, total_counts, present


def choose_marker_diverse_roi(
    coords: np.ndarray,
    marker_scores: np.ndarray,
    total_counts: np.ndarray,
    *,
    max_obs: int,
    seed: int,
    candidate_count: int,
) -> tuple[np.ndarray, dict[str, object]]:
    from sklearn.neighbors import NearestNeighbors

    finite = np.flatnonzero(np.isfinite(coords).all(axis=1))
    if finite.size == 0:
        raise ValueError("No barcodes with finite spatial coordinates.")
    if finite.size <= max_obs:
        return np.sort(finite.astype(np.int64, copy=False)), {
            "mode": "marker_diverse",
            "reason": "finite_barcodes_le_max_obs",
            "n_candidates": int(finite.size),
        }

    rng = np.random.default_rng(seed)
    log_marker = np.log1p(marker_scores).sum(axis=1)
    finite_marker = log_marker[finite]
    threshold = float(np.quantile(finite_marker, 0.65))
    eligible = finite[finite_marker >= threshold]
    if eligible.size == 0:
        eligible = finite
    if eligible.size > candidate_count:
        candidates = rng.choice(eligible, size=int(candidate_count), replace=False)
    else:
        candidates = eligible

    nn = NearestNeighbors(n_neighbors=int(max_obs), algorithm="kd_tree")
    nn.fit(coords[finite])
    best_score = -np.inf
    best_neighbors_global: np.ndarray | None = None
    best_summary: dict[str, object] = {}

    batch_size = 64
    for start in range(0, len(candidates), batch_size):
        cand = candidates[start : start + batch_size]
        _, neighbor_local = nn.kneighbors(coords[cand], return_distance=True)
        neighbor_global = finite[neighbor_local]
        for center, neighbors in zip(cand, neighbor_global):
            group_totals = marker_scores[neighbors].sum(axis=0)
            group_log = np.log1p(group_totals)
            group_sum = float(group_log.sum())
            if group_sum <= 0:
                continue
            frac = group_log / group_sum
            entropy = float(-(frac * np.log(frac + 1e-12)).sum() / np.log(len(frac)))
            positive_groups = int(np.count_nonzero(group_totals > 0))
            dominance_penalty = float(1.0 - frac.max())
            count_term = float(np.log1p(total_counts[neighbors].mean()))
            marker_term = float(np.log1p(marker_scores[neighbors].sum(axis=1).mean()))
            score = entropy * (0.5 + dominance_penalty) * (0.2 + marker_term) * max(0.25, positive_groups / len(frac))
            score += 0.05 * count_term
            if score > best_score:
                best_score = score
                best_neighbors_global = neighbors.copy()
                best_summary = {
                    "mode": "marker_diverse",
                    "center_barcode_index": int(center),
                    "center_col": float(coords[center, 0]),
                    "center_row": float(coords[center, 1]),
                    "score": float(score),
                    "entropy": float(entropy),
                    "positive_groups": positive_groups,
                    "group_totals": [float(x) for x in group_totals],
                    "group_fraction_log": [float(x) for x in frac],
                    "mean_total_counts": float(total_counts[neighbors].mean()),
                    "mean_marker_counts": float(marker_scores[neighbors].sum(axis=1).mean()),
                    "n_candidates": int(len(candidates)),
                    "candidate_marker_threshold": threshold,
                }

    if best_neighbors_global is None:
        raise ValueError("Marker-diverse ROI search did not find a valid candidate.")
    return np.sort(best_neighbors_global.astype(np.int64, copy=False)), best_summary


def read_selected_columns(matrix_h5: Path, selected_cols: np.ndarray, positions: pd.DataFrame) -> ad.AnnData:
    with h5py.File(matrix_h5, "r") as h5:
        matrix = h5["matrix"]
        barcodes = np.asarray(decode_h5_strings(matrix["barcodes"][()]), dtype=object)
        selected_barcodes = barcodes[selected_cols].astype(str)

        data_ds = matrix["data"]
        indices_ds = matrix["indices"]
        indptr_ds = matrix["indptr"]
        shape = tuple(int(x) for x in matrix["shape"][()])

        chunks_data = []
        chunks_indices = []
        new_indptr = [0]
        for col in selected_cols:
            start = int(indptr_ds[col])
            stop = int(indptr_ds[col + 1])
            chunks_data.append(data_ds[start:stop])
            chunks_indices.append(indices_ds[start:stop])
            new_indptr.append(new_indptr[-1] + (stop - start))

        data = np.concatenate(chunks_data) if chunks_data else np.array([], dtype=data_ds.dtype)
        indices = np.concatenate(chunks_indices) if chunks_indices else np.array([], dtype=indices_ds.dtype)
        indptr = np.asarray(new_indptr, dtype=indptr_ds.dtype)
        x_features_by_barcodes = sp.csc_matrix((data, indices, indptr), shape=(shape[0], len(selected_cols)))
        x_obs_by_features = x_features_by_barcodes.T.tocsr()

        feature_names = decode_h5_strings(matrix["features"]["name"][()])
        feature_ids = decode_h5_strings(matrix["features"]["id"][()])
        feature_types = decode_h5_strings(matrix["features"]["feature_type"][()])

    obs = pd.DataFrame(index=pd.Index(selected_barcodes, name=None))
    pos = positions.reindex(obs.index)
    for col in pos.columns:
        obs[col] = pos[col].to_numpy()

    var = pd.DataFrame(
        {
            "gene_ids": feature_ids,
            "feature_types": feature_types,
        },
        index=pd.Index(feature_names, name=None).astype(str),
    )
    adata = ad.AnnData(X=x_obs_by_features, obs=obs, var=var)
    adata.var_names_make_unique()
    adata.obsm["spatial"] = adata.obs[["array_col", "array_row"]].to_numpy(dtype=float)
    return adata


def select_genes(adata: ad.AnnData, *, max_genes: int, marker_genes: Iterable[str]) -> ad.AnnData:
    x = adata.X.tocsc() if sp.issparse(adata.X) else np.asarray(adata.X)
    if sp.issparse(x):
        cells_expressing = np.diff(x.indptr)
        total_counts = np.asarray(x.sum(axis=0)).ravel()
    else:
        cells_expressing = np.count_nonzero(x, axis=0)
        total_counts = x.sum(axis=0)

    expressed = np.flatnonzero(total_counts > 0)
    if expressed.size == 0:
        raise ValueError("No expressed genes found in selected ROI.")
    order = np.lexsort((-total_counts[expressed], -cells_expressing[expressed]))
    selected = list(expressed[order[: max(1, int(max_genes))]])

    gene_to_idx = {str(name): idx for idx, name in enumerate(adata.var_names)}
    for gene in marker_genes:
        idx = gene_to_idx.get(str(gene))
        if idx is not None and total_counts[idx] > 0 and idx not in selected:
            selected.append(idx)

    selected = np.asarray(sorted(set(selected)), dtype=int)
    return adata[:, selected].copy()


def build_roi(args: argparse.Namespace) -> dict[str, object]:
    bin_dir = Path(args.input_bin_dir).expanduser().resolve()
    matrix_h5 = bin_dir / "filtered_feature_bc_matrix.h5"
    if not matrix_h5.exists():
        raise FileNotFoundError(matrix_h5)

    positions_path = find_positions_path(bin_dir)
    positions = read_positions(positions_path)

    with h5py.File(matrix_h5, "r") as h5:
        matrix = h5["matrix"]
        barcodes = np.asarray(decode_h5_strings(matrix["barcodes"][()]), dtype=object).astype(str)
        feature_names = np.asarray(decode_h5_strings(matrix["features"]["name"][()]), dtype=object).astype(str)
    pos = positions.reindex(pd.Index(barcodes))
    coords = pos[["array_col", "array_row"]].to_numpy(dtype=float)
    roi_summary: dict[str, object]
    if args.selection_mode == "marker_diverse":
        marker_scores, total_counts, present_markers = compute_marker_group_scores(
            matrix_h5,
            feature_names=feature_names,
            marker_groups=MARKER_GROUPS,
        )
        selected_cols, roi_summary = choose_marker_diverse_roi(
            coords,
            marker_scores,
            total_counts,
            max_obs=int(args.max_obs),
            seed=int(args.seed),
            candidate_count=int(args.candidate_count),
        )
        roi_summary["marker_groups"] = list(MARKER_GROUPS)
        roi_summary["present_markers"] = present_markers
    else:
        selected_cols = choose_spatial_roi(
            coords,
            max_obs=int(args.max_obs),
            seed=int(args.seed),
            center_col=args.center_col,
            center_row=args.center_row,
        )
        roi_summary = {
            "mode": "spatial_nearest",
            "center_col": args.center_col,
            "center_row": args.center_row,
            "seed": int(args.seed),
        }

    adata = read_selected_columns(matrix_h5, selected_cols, positions)
    adata = select_genes(adata, max_genes=int(args.max_genes), marker_genes=args.marker_gene)
    adata.obs_names_make_unique()
    adata.var_names_make_unique()
    adata.uns["spix_workshop_source"] = {
        "dataset": "Visium HD Spatial Gene Expression Library, Human Colon Cancer (FF), 11 mm Capture Area",
        "dataset_url": "https://www.10xgenomics.com/datasets/visium-hd-cytassist-11mm-human-colon-cancer-HE",
        "license": "Creative Commons Attribution 4.0 International",
        "space_ranger": "4.1.0",
        "bin_size_um": int(args.bin_size_um),
        "source_bin_dir": str(bin_dir),
        "source_matrix_h5": str(matrix_h5),
        "source_positions": str(positions_path),
        "roi_seed": int(args.seed),
        "roi_selection_mode": args.selection_mode,
        "roi_selection": roi_summary,
        "max_obs": int(args.max_obs),
        "max_genes": int(args.max_genes),
    }

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(output, compression="gzip")

    manifest = {
        "output": str(output),
        "n_obs": int(adata.n_obs),
        "n_vars": int(adata.n_vars),
        "nnz": int(adata.X.nnz) if sp.issparse(adata.X) else int(np.count_nonzero(adata.X)),
        "file_size_bytes": int(output.stat().st_size),
        "source_matrix_h5": str(matrix_h5),
        "source_positions": str(positions_path),
        "bin_size_um": int(args.bin_size_um),
        "seed": int(args.seed),
        "selection_mode": args.selection_mode,
        "roi_selection": roi_summary,
        "selected_obs_preview": list(map(str, adata.obs_names[:5])),
        "selected_gene_preview": list(map(str, adata.var_names[:20])),
    }
    manifest_path = output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-bin-dir", required=True, help="Space Ranger Visium HD bin directory.")
    parser.add_argument("--output", required=True, help="Output .h5ad path.")
    parser.add_argument("--max-obs", type=int, default=5000)
    parser.add_argument("--max-genes", type=int, default=1800)
    parser.add_argument("--bin-size-um", type=int, default=16)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--selection-mode",
        choices=["spatial_nearest", "marker_diverse"],
        default="spatial_nearest",
        help="Choose ROI by random/manual spatial center or marker-diverse local tissue context.",
    )
    parser.add_argument("--candidate-count", type=int, default=512)
    parser.add_argument("--center-col", type=float, default=None)
    parser.add_argument("--center-row", type=float, default=None)
    parser.add_argument("--marker-gene", action="append", default=list(DEFAULT_MARKER_GENES))
    return parser.parse_args()


def main() -> None:
    manifest = build_roi(parse_args())
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
