#!/usr/bin/env python
"""Execute notebook code cells in order when nbclient/nbconvert are unavailable."""

from __future__ import annotations

import argparse
import json
import os
import traceback
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook")
    parser.add_argument("--workdir", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    notebook = Path(args.notebook).resolve()
    if args.workdir:
        os.chdir(args.workdir)

    os.environ.setdefault("MPLBACKEND", "Agg")
    payload = json.loads(notebook.read_text())
    namespace = {"__name__": "__main__"}
    code_cells = [cell for cell in payload.get("cells", []) if cell.get("cell_type") == "code"]
    for idx, cell in enumerate(code_cells, start=1):
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        print(f"[cell {idx}/{len(code_cells)}]", flush=True)
        try:
            exec(compile(source, f"{notebook.name}:cell{idx}", "exec"), namespace)
        except Exception:
            print(f"Notebook execution failed in code cell {idx}:")
            print(source[:1200])
            traceback.print_exc()
            raise
    print(f"Executed {len(code_cells)} code cells successfully.")


if __name__ == "__main__":
    main()
