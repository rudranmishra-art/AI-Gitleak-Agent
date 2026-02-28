import subprocess
import os
import shutil

REPORT_PATH = "reports/report.json"
GITLEAKS_CONFIG = "config/gitleaks.toml"


def _find_gitleaks() -> str:
    """Locate the gitleaks binary, raise clearly if missing."""
    path = shutil.which("gitleaks")
    if not path:
        raise FileNotFoundError(
            "gitleaks binary not found on PATH. "
            "Install it from https://github.com/gitleaks/gitleaks/releases"
        )
    return path


def run_scan(source: str = ".") -> tuple[int, str]:
    """
    Run a gitleaks detect scan on *source*.

    Returns:
        (return_code, report_path)
        return_code == 0  → no secrets found
        return_code == 1  → secrets found (report written)
        return_code == 126/127 → gitleaks not installed
    """
    os.makedirs("reports", exist_ok=True)

    try:
        binary = _find_gitleaks()
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 127, REPORT_PATH

    cmd = [
        binary,
        "detect",
        "--source", source,
        "--report-format", "json",
        "--report-path", REPORT_PATH,
        "--exit-code", "1",
    ]

    # Only add --config if the custom toml actually exists
    if os.path.isfile(GITLEAKS_CONFIG):
        cmd += ["--config", GITLEAKS_CONFIG]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, REPORT_PATH
