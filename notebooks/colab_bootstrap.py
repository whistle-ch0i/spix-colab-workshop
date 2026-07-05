"""Colab setup helpers for the KOGO spatial transcriptomics practical.

The notebook keeps the actual analysis calls in the visible cells.  This file
only handles runtime setup: downloading small repo files, installing pinned
packages, checking SPIX, and checking the R BayesSpace package.
"""

from __future__ import annotations

import importlib.metadata as metadata
import importlib.util
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


def running_in_colab() -> bool:
    return "google.colab" in sys.modules or "COLAB_RELEASE_TAG" in os.environ


def locate_or_download_repo_file(
    filename: str,
    url: str,
    *,
    search_dirs: list[str | Path] | None = None,
    download_dir: str | Path | None = None,
) -> Path:
    """Find a small repo file locally, otherwise download it from GitHub raw."""
    if search_dirs is None:
        search_dirs = [".", "notebooks", Path.cwd() / "notebooks", "/content"]

    candidates = [Path(filename)]
    candidates.extend(Path(base) / filename for base in search_dirs)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    if download_dir is None:
        download_dir = "/content" if running_in_colab() else "."

    target = Path(download_dir) / filename
    print("Downloading:", url)
    urllib.request.urlretrieve(url, target)
    return target.resolve()


def ensure_python_requirements(requirements_path: str | Path, *, in_colab: bool | None = None) -> None:
    """Install pinned Python packages in Colab; skip automatic installs locally."""
    if in_colab is None:
        in_colab = running_in_colab()

    force_install = os.environ.get("SPIX_WORKSHOP_FORCE_INSTALL", "0") == "1"
    if not in_colab and not force_install:
        print("Local run: skipping pip install. Current environment will be used.")
        return

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "--upgrade",
            "-r",
            str(requirements_path),
        ]
    )


def _add_local_spix_checkout() -> bool:
    """Use a neighboring SPIX checkout when the notebook is run locally."""
    cwd = Path.cwd().resolve()
    roots = [cwd, *cwd.parents]
    candidates: list[Path] = []
    for root in roots:
        candidates.extend([root, root / "SPIX", root.parent / "SPIX"])

    for candidate in candidates:
        if (candidate / "SPIX" / "__init__.py").exists():
            sys.path.insert(0, str(candidate))
            return True
    return False


def ensure_spix(spix_install_url: str, *, in_colab: bool | None = None) -> None:
    """Make sure the SPIX Python package can be imported."""
    if importlib.util.find_spec("SPIX") is not None:
        return

    if in_colab is None:
        in_colab = running_in_colab()

    if not in_colab and _add_local_spix_checkout():
        return

    if not in_colab:
        raise ImportError("SPIX repo 안에서 실행하거나 SPIX를 설치하세요.")

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--quiet", spix_install_url]
    )


def patch_spix_optional_imports() -> None:
    """Keep optional SPIX modules from blocking the workshop functions."""
    spix_spec = importlib.util.find_spec("SPIX")
    if spix_spec is None or spix_spec.origin is None:
        raise ImportError("SPIX를 먼저 설치해야 합니다.")

    spix_root = Path(spix_spec.origin).parent

    visualization_init = spix_root / "visualization" / "__init__.py"
    if visualization_init.exists():
        visualization_init.write_text(
            "from .plotting import *\n"
            "from .origin_display import *\n"
        )

    analysis_init = spix_root / "analysis" / "__init__.py"
    if analysis_init.exists():
        analysis_init.write_text(
            "import os\n"
            "os.environ.setdefault('NUMBA_CACHE_DIR', '/tmp/numba_spix')\n"
            "from .multiscale_moran_ranks import *\n"
        )


def ensure_bayesspace(*, in_colab: bool | None = None) -> None:
    """Check the R BayesSpace package and install it only in Colab."""
    if shutil.which("Rscript") is None:
        raise ImportError("BayesSpace 실행을 위해 Rscript가 필요합니다.")

    check = subprocess.run(
        [
            "Rscript",
            "-e",
            "quit(status=ifelse(requireNamespace('BayesSpace', quietly=TRUE), 0, 1))",
        ],
        capture_output=True,
        text=True,
    )
    if check.returncode == 0:
        return

    if in_colab is None:
        in_colab = running_in_colab()
    if not in_colab:
        raise ImportError("R package BayesSpace가 설치되어 있지 않습니다.")

    subprocess.check_call(
        [
            "Rscript",
            "-e",
            (
                "if (!requireNamespace('BiocManager', quietly=TRUE)) "
                "install.packages('BiocManager', repos='https://cloud.r-project.org'); "
                "BiocManager::install('BayesSpace', update=FALSE, ask=FALSE); "
                "if (!requireNamespace('BayesSpace', quietly=TRUE)) "
                "stop('BayesSpace install failed')"
            ),
        ]
    )


def package_versions(package_names: list[str]) -> dict[str, str]:
    """Return installed versions for the timing report."""
    versions = {}
    for package_name in package_names:
        try:
            versions[package_name] = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            versions[package_name] = "not installed"
    return versions
