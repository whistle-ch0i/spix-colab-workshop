#!/usr/bin/env python3
"""Check that the workshop files needed by Colab are present.

Run locally before pushing.  After pushing, add ``--check-urls`` to confirm the
GitHub raw URLs used by the notebook are reachable.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path


RAW_BASE = "https://raw.githubusercontent.com/whistle-ch0i/spix-colab-workshop/main"

EXPECTED_SHA256 = {
    "data/visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad": (
        "abf1f7848397869a1abd7b329d0dd86c9aea80bf87c71e93d727585a4c41802f"
    ),
    "data/visiumhd_p2_roi_context_1000000_downsample.csv": (
        "5b429739f7901cfa92b45afbaf7d6b4b191beafd547829d5f8fa5c7042e0e5a4"
    ),
    "data/bayesspace_labels_1m_panel3500.csv": (
        "927f13e098dd1558e88bb90074b02de52078918c010cc4db3c647b04c96c7a14"
    ),
    "data/spagcn_labels_1m_panel3500.csv": (
        "de3f7a7907ff6bd0d67afd2aa216538b834d3c1d8b6a9368c723770235287d73"
    ),
    "data/liana_rank_aggregate_1m_panel3500.csv": (
        "ecf27b3386c4acce2e964bb6cfe0397c29a9f9b32d10da8063519ffb4ad6db16"
    ),
    "data/crc_scale_svg_ontology_reference.csv": (
        "ada790a40fa84c248cebca152022c1dedbcb6fdc88f0b351278f6866222980ea"
    ),
    "data/crc_ontology_layer_summary_by_scale.csv": (
        "3c00aef83046532dca4702bad67e9dddf4e0817911a2d41809ef3846668ece60"
    ),
}

REQUIRED_FILES = [
    "notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb",
    "notebooks/Choi_Whisoo_KOGO_spatial_downstream_colab.ipynb",
    "notebooks/workshop_helpers.py",
    "notebooks/colab_bootstrap.py",
    "requirements-colab.txt",
    *EXPECTED_SHA256.keys(),
]

REQUIRED_URLS = [
    f"{RAW_BASE}/notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb",
    f"{RAW_BASE}/notebooks/Choi_Whisoo_KOGO_spatial_downstream_colab.ipynb",
    f"{RAW_BASE}/notebooks/workshop_helpers.py",
    f"{RAW_BASE}/notebooks/colab_bootstrap.py",
    f"{RAW_BASE}/requirements-colab.txt",
    f"{RAW_BASE}/data/visiumhd_colon_crc_p2_2um_roi_1000000x2515.h5ad",
    f"{RAW_BASE}/data/visiumhd_p2_roi_context_1000000_downsample.csv",
    f"{RAW_BASE}/data/bayesspace_labels_1m_panel3500.csv",
    f"{RAW_BASE}/data/spagcn_labels_1m_panel3500.csv",
    f"{RAW_BASE}/data/liana_rank_aggregate_1m_panel3500.csv",
    f"{RAW_BASE}/data/crc_scale_svg_ontology_reference.csv",
    f"{RAW_BASE}/data/crc_ontology_layer_summary_by_scale.csv",
]


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_local_files(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.exists():
            errors.append(f"missing file: {relative}")
            continue
        expected_sha = EXPECTED_SHA256.get(relative)
        if expected_sha and sha256sum(path) != expected_sha:
            errors.append(f"sha256 mismatch: {relative}")

    requirements = root / "requirements-colab.txt"
    if requirements.exists():
        text = requirements.read_text()
        for required_line in ["scanpy==1.11.5", "squidpy==1.6.5", "zarr==2.18.3"]:
            if required_line not in text:
                errors.append(f"requirements-colab.txt missing {required_line}")

    notebook_files = [
        "notebooks/Choi_Whisoo_SPIX_spatial_clustering_SVG_CCI_colab.ipynb",
        "notebooks/Choi_Whisoo_KOGO_spatial_downstream_colab.ipynb",
    ]
    for notebook_relative in notebook_files:
        notebook = root / notebook_relative
        if not notebook.exists():
            continue
        text = notebook.read_text()
        for token in [
            "requirements-colab.txt",
            "colab_bootstrap.py",
            "workshop_helpers.py",
            "bayesspace_labels_1m_panel3500.csv",
            "spagcn_labels_1m_panel3500.csv",
            "liana_rank_aggregate_1m_panel3500.csv",
            "crc_scale_svg_ontology_reference.csv",
            "crc_ontology_layer_summary_by_scale.csv",
        ]:
            if token not in text:
                errors.append(f"{notebook_relative} does not reference {token}")

    return errors


def check_urls() -> list[str]:
    errors: list[str] = []
    for url in REQUIRED_URLS:
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                status = getattr(response, "status", 200)
                if status >= 400:
                    errors.append(f"url failed [{status}]: {url}")
        except Exception as exc:
            errors.append(f"url failed: {url} ({exc})")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--check-urls", action="store_true", help="also check GitHub raw URLs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()

    errors = check_local_files(root)
    if args.check_urls:
        errors.extend(check_urls())

    if errors:
        print("Colab publish check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Colab publish check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
