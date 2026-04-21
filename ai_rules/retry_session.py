# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from common import PYTHON_EXECUTABLE, SCRIPT_DIR, load_runtime_config
from status_store import get_retry_candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retry failed or partial session submissions.")
    parser.add_argument("--status", default="", help="Optional status filter")
    parser.add_argument("--session-id", default="", help="Optional session_id filter")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runtime_config = load_runtime_config()
    sqlite_path = Path(runtime_config["sqlite"]["path"])
    retry_candidates = get_retry_candidates(sqlite_path, target_status=args.status or None)

    for retry_candidate in retry_candidates:
        if args.session_id and retry_candidate["session_id"] != args.session_id:
            continue
        child_environment = os.environ.copy()
        child_environment["PYTHONIOENCODING"] = "utf-8"
        subprocess.run(
            [
                PYTHON_EXECUTABLE,
                str(SCRIPT_DIR / "submit_session.py"),
                "--payload-file",
                retry_candidate["normalized_payload_path"],
            ],
            check=True,
            env=child_environment,
        )


if __name__ == "__main__":
    main()
