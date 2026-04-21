# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import json
import subprocess
import uuid

from common import PYTHON_EXECUTABLE, SCRIPT_DIR, ensure_directory


def read_multiline_json_from_stdin() -> dict:
    print("Paste JSON payload, then press Ctrl+Z and Enter on Windows to finish.")
    collected_lines: list[str] = []
    try:
        while True:
            collected_lines.append(input())
    except EOFError:
        pass
    return json.loads("\n".join(collected_lines))


def main() -> None:
    payload = read_multiline_json_from_stdin()
    temp_payload_dir = SCRIPT_DIR / "temp_payloads"
    ensure_directory(temp_payload_dir)
    temp_payload_path = temp_payload_dir / f"manual-submit-{uuid.uuid4()}.json"
    with temp_payload_path.open("w", encoding="utf-8") as temp_payload_file:
        json.dump(payload, temp_payload_file, indent=2)

    subprocess.run(
        [PYTHON_EXECUTABLE, str(SCRIPT_DIR / "submit_session.py"), "--payload-file", str(temp_payload_path)],
        check=True,
    )


if __name__ == "__main__":
    main()
