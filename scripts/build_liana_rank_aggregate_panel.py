#!/usr/bin/env python3
"""Build the bundled LIANA rank-aggregate table for the workshop panel."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc
import squidpy as sq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "notebooks"))

from workshop_helpers import center_nonzero_panel, pseudobulk_visiumhd_2um_to_8um


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="data/visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad",
        help="Native 2 um ROI AnnData used by the workshop.",
    )
    parser.add_argument(
        "--output",
        default="data/liana_rank_aggregate_1m_panel3500.csv",
        help="Output CSV for the bundled LIANA result.",
    )
    parser.add_argument(
        "--cluster-labels",
        default="data/bayesspace_labels_1m_panel3500.csv",
        help="Cluster labels for the fixed 3,500-bin panel.",
    )
    parser.add_argument(
        "--cluster-column",
        default="bayesspace_domain",
        help="Column in --cluster-labels to use as LIANA groups.",
    )
    parser.add_argument("--max-obs", type=int, default=3500)
    parser.add_argument("--hvg-n-top", type=int, default=1200)
    parser.add_argument("--n-pcs", type=int, default=30)
    parser.add_argument("--n-neighbors", type=int, default=25)
    parser.add_argument("--liana-perms", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--top-n", type=int, default=300)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    import liana as li

    adata_2um = sc.read_h5ad(args.input)
    coords_2um = np.asarray(adata_2um.obsm["spatial"], dtype=float)
    adata_8um = pseudobulk_visiumhd_2um_to_8um(adata_2um, coords_2um)
    coords_8um = np.asarray(adata_8um.obsm["spatial"], dtype=float)
    total_counts_8um = np.asarray(adata_8um.X.sum(axis=1)).ravel()

    analysis_adata = adata_8um.copy()
    sc.pp.normalize_total(analysis_adata, target_sum=1e4)
    sc.pp.log1p(analysis_adata)
    analysis_adata.layers["log_norm"] = analysis_adata.X.copy()
    sc.pp.highly_variable_genes(
        analysis_adata,
        n_top_genes=min(args.hvg_n_top, analysis_adata.n_vars),
        flavor="seurat",
    )
    sc.pp.pca(
        analysis_adata,
        n_comps=min(args.n_pcs, analysis_adata.n_obs - 1, analysis_adata.n_vars - 1),
        mask_var="highly_variable",
        svd_solver="arpack",
        random_state=args.seed,
    )
    sc.pp.neighbors(
        analysis_adata,
        n_neighbors=args.n_neighbors,
        n_pcs=min(args.n_pcs, analysis_adata.obsm["X_pca"].shape[1]),
        key_added="expression",
        random_state=args.seed,
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
        random_state=args.seed,
    )

    domain_idx = center_nonzero_panel(coords_8um, total_counts_8um, max_obs=args.max_obs)
    domain_adata = analysis_adata[domain_idx].copy()
    domain_coords = np.asarray(domain_adata.obsm["spatial"], dtype=float)
    label_table = pd.read_csv(args.cluster_labels).set_index("barcode")
    missing = domain_adata.obs_names.difference(label_table.index)
    if len(missing) > 0:
        raise ValueError(f"Cluster label file is missing {len(missing)} panel barcodes")
    domain_adata.obs["cci_domain"] = pd.Categorical(
        label_table.loc[domain_adata.obs_names, args.cluster_column].astype(str).to_numpy()
    )
    print(domain_adata.obs["cci_domain"].value_counts().sort_index())

    liana_resource = li.rs.select_resource("consensus")
    liana_resource = liana_resource[
        liana_resource["ligand"].isin(domain_adata.var_names)
        & liana_resource["receptor"].isin(domain_adata.var_names)
    ].copy()
    print("LIANA resource pairs:", len(liana_resource))

    li.mt.rank_aggregate(
        domain_adata,
        groupby="cci_domain",
        resource=liana_resource,
        use_raw=False,
        layer="log_norm",
        n_perms=args.liana_perms,
        expr_prop=0.05,
        seed=args.seed,
        verbose=False,
    )
    liana_table = domain_adata.uns["liana_res"].copy()
    keep_columns = [
        "source",
        "target",
        "ligand_complex",
        "receptor_complex",
        "magnitude_rank",
        "specificity_rank",
        "lr_means",
        "cellphone_pvals",
    ]
    liana_table = liana_table[keep_columns].sort_values(
        ["magnitude_rank", "specificity_rank", "lr_means"],
        ascending=[True, True, False],
    )
    liana_table = liana_table.head(args.top_n)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    liana_table.to_csv(args.output, index=False)
    print("wrote:", args.output, liana_table.shape)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
