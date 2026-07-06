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
import time
import urllib.request
from pathlib import Path


DIRECT_PACKAGE_MODULES = {
    "anndata": "anndata",
    "scanpy": "scanpy",
    "squidpy": "squidpy",
    "zarr": "zarr",
    "numcodecs": "numcodecs",
    "tqdm-joblib": "tqdm_joblib",
    "python-igraph": "igraph",
    "leidenalg": "leidenalg",
    "SpaGCN": "SpaGCN",
    "pybanksy": "banksy",
}


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


def _read_requirement_pins(requirements_path: str | Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw_line in Path(requirements_path).read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, version = line.split("==", 1)
        pins[name.strip()] = version.strip()
    return pins


def _run_command(command: list[str], label: str) -> None:
    print(f"[setup] {label} ...", flush=True)
    start = time.perf_counter()
    subprocess.check_call(command)
    print(f"[setup] {label} done in {time.perf_counter() - start:.1f} sec", flush=True)


def ensure_python_requirements(requirements_path: str | Path, *, in_colab: bool | None = None) -> None:
    """Install only missing direct Python packages in Colab.

    A full ``pip install --upgrade -r requirements-colab.txt`` is too slow for a
    live workshop because it can reinstall Colab's base scientific stack.  This
    function keeps the pins as the source of truth, but only installs packages
    whose import module is missing, plus zarr v2 if Colab supplies zarr v3.
    """
    if in_colab is None:
        in_colab = running_in_colab()

    force_install = os.environ.get("SPIX_WORKSHOP_FORCE_INSTALL", "0") == "1"
    if not in_colab and not force_install:
        print("Local run: skipping pip install. Current environment will be used.")
        return

    pins = _read_requirement_pins(requirements_path)
    strict = os.environ.get("SPIX_WORKSHOP_STRICT_REQUIREMENTS", "0") == "1"
    install_specs: list[str] = []

    print("[setup] checking Python packages", flush=True)
    for package_name, module_name in DIRECT_PACKAGE_MODULES.items():
        pinned_version = pins.get(package_name)
        spec = f"{package_name}=={pinned_version}" if pinned_version else package_name
        module_spec = importlib.util.find_spec(module_name)

        if module_spec is None:
            install_specs.append(spec)
            print(f"[setup] missing {module_name}; will install {spec}", flush=True)
            continue

        if package_name == "zarr":
            observed = metadata.version("zarr")
            if observed.split(".", 1)[0] == "3":
                install_specs.append(spec)
                print(f"[setup] zarr {observed} detected; will install {spec}", flush=True)
            continue

        if strict and pinned_version:
            try:
                observed = metadata.version(package_name)
            except metadata.PackageNotFoundError:
                observed = ""
            if observed != pinned_version:
                install_specs.append(spec)
                print(
                    f"[setup] {package_name} {observed or 'unknown'} != {pinned_version}; "
                    f"will install {spec}",
                    flush=True,
                )

    if install_specs and "zarr==2.18.3" not in install_specs:
        install_specs.append("zarr==2.18.3")
    if install_specs and "numcodecs==0.13.1" not in install_specs:
        install_specs.append("numcodecs==0.13.1")

    if not install_specs:
        print("[setup] Python packages already importable", flush=True)
        return

    _run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--progress-bar",
            "off",
            *dict.fromkeys(install_specs),
        ],
        "pip install direct workshop packages",
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
        print("[setup] SPIX already importable", flush=True)
        return

    if in_colab is None:
        in_colab = running_in_colab()

    if not in_colab and _add_local_spix_checkout():
        return

    if not in_colab:
        raise ImportError("SPIX repo 안에서 실행하거나 SPIX를 설치하세요.")

    _run_command(
        [sys.executable, "-m", "pip", "install", "--progress-bar", "off", spix_install_url],
        "pip install SPIX",
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


def ensure_bayesspace(*, in_colab: bool | None = None) -> bool:
    """Check the R BayesSpace package.

    By default Colab does not install BayesSpace during the live class because
    Bioconductor installation can dominate the session.  Set
    ``SPIX_WORKSHOP_INSTALL_BAYESSPACE=1`` to force a live R installation.
    """
    if os.environ.get("SPIX_WORKSHOP_FORCE_BAYESSPACE_LABELS", "0") == "1":
        print("[setup] forced bundled BayesSpace labels", flush=True)
        return False

    if shutil.which("Rscript") is None:
        print("[setup] Rscript not found; BayesSpace will use bundled labels", flush=True)
        return False

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
        print("[setup] BayesSpace R package already available", flush=True)
        return True

    if in_colab is None:
        in_colab = running_in_colab()
    install_requested = os.environ.get("SPIX_WORKSHOP_INSTALL_BAYESSPACE", "0") == "1"
    if not in_colab:
        print("[setup] BayesSpace R package missing; bundled labels will be used", flush=True)
        return False
    if not install_requested:
        print(
            "[setup] BayesSpace R package missing; bundled labels will be used. "
            "Set SPIX_WORKSHOP_INSTALL_BAYESSPACE=1 for a live R install.",
            flush=True,
        )
        return False

    _run_command(
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
        ],
        "R install BayesSpace",
    )
    return True


def package_versions(package_names: list[str]) -> dict[str, str]:
    """Return installed versions for the timing report."""
    versions = {}
    for package_name in package_names:
        try:
            versions[package_name] = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            versions[package_name] = "not installed"
    return versions
