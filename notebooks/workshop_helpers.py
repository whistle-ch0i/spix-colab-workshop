"""Small utilities for the KOGO spatial transcriptomics workshop notebook.

These helpers keep the Colab notebook focused on the analysis steps.  They do
not wrap Scanpy, Squidpy, BANKSY, BayesSpace, SpaGCN, or SPIX analysis calls.
"""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path


def file_sha256(path: str | Path) -> str:
    """Return the SHA-256 checksum of a local file."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def runtime_snapshot(n_jobs: int) -> dict:
    """Record the runtime details that matter for Colab timing reports."""
    meminfo = {}
    meminfo_path = Path("/proc/meminfo")
    if meminfo_path.exists():
        for line in meminfo_path.read_text().splitlines():
            key, value = line.split(":", 1)
            if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}:
                meminfo[key] = round(float(value.strip().split()[0]) / 1024 / 1024, 2)

    disk = shutil.disk_usage(Path.cwd())
    running_in_colab = "google.colab" in sys.modules or "COLAB_RELEASE_TAG" in os.environ
    return {
        "running_in_colab": bool(running_in_colab),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "thread_cap": n_jobs,
        "memory_gb": meminfo,
        "cwd": str(Path.cwd().resolve()),
        "disk_free_gb": round(disk.free / 1024**3, 2),
    }


@contextmanager
def timed_stage(stage: str, stage_times: list[dict]):
    """Time one notebook stage and append a compact record."""
    start = time.perf_counter()
    try:
        yield
    except Exception:
        seconds = round(time.perf_counter() - start, 2)
        stage_times.append({"stage": stage, "seconds": seconds, "ok": False})
        print(f"[timing] {stage}: {seconds} sec | ok=False")
        raise
    else:
        seconds = round(time.perf_counter() - start, 2)
        stage_times.append({"stage": stage, "seconds": seconds, "ok": True})
        print(f"[timing] {stage}: {seconds} sec")


def locate_or_download(
    filename: str | Path,
    url: str,
    *,
    sha256: str = "",
    search_dirs: list[str | Path] | None = None,
    download_dir: str | Path | None = None,
) -> Path:
    """Find a file locally, otherwise download it and verify the checksum."""
    filename = Path(filename).expanduser()
    file_name = filename.name

    if search_dirs is None:
        search_dirs = [
            ".",
            "data",
            "../data",
            Path.cwd() / "data",
            "/content",
        ]

    candidates = [filename]
    candidates.extend(Path(base) / file_name for base in search_dirs)

    for candidate in candidates:
        if candidate.exists():
            path = candidate.resolve()
            break
    else:
        if download_dir is None:
            download_dir = "/content" if ("COLAB_RELEASE_TAG" in os.environ) else "."
        path = Path(download_dir) / file_name
        print("Downloading:", url)
        urllib.request.urlretrieve(url, path)
        path = path.resolve()

    observed_sha256 = file_sha256(path)
    if sha256:
        assert observed_sha256 == sha256, f"SHA-256 mismatch for {path}: {observed_sha256}"
    return path


def sample_indices(n_obs: int, max_points: int = 120_000, seed: int = 7):
    """Return deterministic row indices for a bounded scatter plot."""
    import numpy as np

    if n_obs <= max_points:
        return np.arange(n_obs)
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n_obs, size=max_points, replace=False))


def spatial_scatter(
    ax,
    coords,
    *,
    values=None,
    title: str = "",
    size: float = 2.0,
    cmap: str = "viridis",
):
    """Draw a spatial scatter plot with workshop-default axis styling."""
    if values is None:
        ax.scatter(coords[:, 0], coords[:, 1], s=size, c="#b8b8b8", rasterized=True)
    else:
        ax.scatter(coords[:, 0], coords[:, 1], s=size, c=values, cmap=cmap, rasterized=True)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.set_xticks([])
    ax.set_yticks([])


def sparse_vector(matrix, column_index: int):
    """Extract one dense vector from a dense or sparse matrix."""
    import numpy as np
    import scipy.sparse as sp

    values = matrix[:, column_index]
    if sp.issparse(values):
        values = values.toarray()
    return np.asarray(values).ravel()


def pseudobulk_visiumhd_2um_to_8um(adata_2um, coords_2um):
    """Aggregate native 2 um VisiumHD bins into 8 um bins by 4x4 count sums."""
    import anndata as ad
    import numpy as np
    import pandas as pd
    import scipy.sparse as sp

    row_8um = adata_2um.obs["array_row"].to_numpy(dtype=int) // 4
    col_8um = adata_2um.obs["array_col"].to_numpy(dtype=int) // 4
    group_labels = pd.Series(row_8um.astype(str) + "_" + col_8um.astype(str))
    group_codes, group_names = pd.factorize(group_labels, sort=True)
    group_grid = np.array([name.split("_") for name in group_names], dtype=int)

    aggregation = sp.csr_matrix(
        (
            np.ones(adata_2um.n_obs, dtype=np.float32),
            (group_codes, np.arange(adata_2um.n_obs)),
        ),
        shape=(len(group_names), adata_2um.n_obs),
    )

    X_8um = aggregation @ adata_2um.X
    if not sp.issparse(X_8um):
        X_8um = sp.csr_matrix(X_8um)

    bins_per_8um = np.asarray(aggregation.sum(axis=1)).ravel()
    mean_x = np.asarray(aggregation @ coords_2um[:, 0]).ravel() / bins_per_8um
    mean_y = np.asarray(aggregation @ coords_2um[:, 1]).ravel() / bins_per_8um
    mean_array_row = (
        np.asarray(aggregation @ adata_2um.obs["array_row"].to_numpy(dtype=float)).ravel()
        / bins_per_8um
    )
    mean_array_col = (
        np.asarray(aggregation @ adata_2um.obs["array_col"].to_numpy(dtype=float)).ravel()
        / bins_per_8um
    )

    obs_8um = pd.DataFrame(index=[f"bin8_{name}" for name in group_names])
    obs_8um["n_2um_bins"] = bins_per_8um.astype(int)
    obs_8um["array_row"] = group_grid[:, 0]
    obs_8um["array_col"] = group_grid[:, 1]
    obs_8um["array_row_2um_mean"] = mean_array_row
    obs_8um["array_col_2um_mean"] = mean_array_col

    adata_8um = ad.AnnData(X=X_8um.tocsr(), obs=obs_8um, var=adata_2um.var.copy())
    adata_8um.var_names = adata_2um.var_names.copy()
    adata_8um.var_names_make_unique()
    adata_8um.obsm["spatial"] = np.column_stack([mean_x, mean_y]).astype(np.float32)
    adata_8um.uns["pseudobulk"] = {"source_bin_um": 2, "target_bin_um": 8, "rule": "4x4 sum"}
    return adata_8um


def center_nonzero_panel(coords, counts, max_obs: int):
    """Pick a deterministic central panel after removing zero-count bins."""
    import numpy as np

    nonzero_idx = np.flatnonzero(counts > 0)
    nonzero_coords = coords[nonzero_idx]
    center = np.median(nonzero_coords, axis=0)
    distance_to_center = ((nonzero_coords - center) ** 2).sum(axis=1)
    if len(nonzero_idx) <= max_obs:
        return nonzero_idx
    selected_local_idx = np.argpartition(distance_to_center, max_obs - 1)[:max_obs]
    return np.sort(nonzero_idx[selected_local_idx])


def domain_count_table(adata, method_map: dict[str, str]):
    """Summarize how many bins are assigned to each domain label."""
    import pandas as pd

    tables = []
    for obs_key, method_name in method_map.items():
        one = (
            adata.obs[obs_key]
            .value_counts()
            .sort_index()
            .rename_axis("domain")
            .reset_index(name="n_bins")
        )
        one.insert(0, "method", method_name)
        tables.append(one)
    return pd.concat(tables, ignore_index=True)


def domain_ari_table(adata, method_map: dict[str, str]):
    """Compute pairwise adjusted Rand index across domain methods."""
    import pandas as pd
    from sklearn.metrics import adjusted_rand_score

    rows = []
    items = list(method_map.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            key_a, label_a = items[i]
            key_b, label_b = items[j]
            rows.append(
                {
                    "method_a": label_a,
                    "method_b": label_b,
                    "adjusted_rand_index": adjusted_rand_score(
                        adata.obs[key_a].astype(str),
                        adata.obs[key_b].astype(str),
                    ),
                }
            )
    return pd.DataFrame(rows)


def tidy_ligrec_result(ligrec_result):
    """Turn Squidpy ligrec means/pvalues matrices into a long table."""
    import numpy as np

    means = ligrec_result["means"].copy()
    pvalues = ligrec_result["pvalues"].copy()

    means.index.names = [
        name if name is not None else f"row_{i}" for i, name in enumerate(means.index.names)
    ]
    pvalues.index.names = means.index.names

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
    table = ligrec_means.merge(ligrec_pvalues, on=merge_columns, how="left")
    table = table.replace([np.inf, -np.inf], np.nan).dropna(subset=["mean_expression"])

    if {"source", "target"}.issubset(table.columns):
        table["pair"] = table["source"].astype(str) + "-" + table["target"].astype(str)
    else:
        table["pair"] = table.iloc[:, 0].astype(str)

    table["pvalue_sort"] = table["pvalue"].fillna(1.0)
    table = table.sort_values(["pvalue_sort", "mean_expression"], ascending=[True, False])
    return table.drop(columns=["pvalue_sort"])


def top_rank_table(rank_df, top_n: int = 5):
    """Collect top-ranked genes from each rank column."""
    import pandas as pd

    rows = []
    for column in rank_df.columns:
        scale_id = column.replace("rank_", "")
        top_genes = rank_df[column].dropna().sort_values().head(top_n)
        rows.append(
            pd.DataFrame(
                {
                    "scale": scale_id,
                    "gene": top_genes.index,
                    "rank": top_genes.values,
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def add_segment_labels(adata, segment_index, segment_dir: str | Path, prefix: str = "spix_") -> None:
    """Add saved SPIX segment labels back to AnnData.obs."""
    import numpy as np
    import pandas as pd

    segment_dir = Path(segment_dir)
    for _, row in segment_index.iterrows():
        scale_id = str(row["scale_id"])
        is_native = str(row.get("native_identity", "")).lower() == "true"
        if is_native or str(row.get("path", "")) == "__native_identity__":
            continue

        segment_path = Path(str(row["path"]))
        if not segment_path.is_absolute():
            segment_path = segment_dir / segment_path.name

        segment_file = np.load(segment_path, allow_pickle=True)
        adata.obs[f"{prefix}{scale_id}"] = pd.Categorical(segment_file["seg_codes"].astype(str))
