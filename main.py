"""
main.py — AI-Gitleak-Agent entry point
"""

import sys

from agent.scanner import run_scan
from agent.analyzer import analyze
from agent.ai_engine import explain
from agent.reporter import log_findings, print_output, print_summary_table
from agent.utils import ensure_directories


def main() -> None:
    ensure_directories()

    print("🔍 Running Gitleaks scan…")
    code, report_path = run_scan()

    if code == 127:
        print("❌ gitleaks is not installed. Cannot proceed.")
        sys.exit(2)

    if code == 0:
        print("✅ No secrets found. You're good to go!")
        sys.exit(0)

    findings = analyze(report_path)
    if not findings:
        print("⚠  Scan flagged issues but the report could not be parsed.")
        sys.exit(1)

    # Summary table first
    print_summary_table(findings)

    # Per-finding AI explanations
    for finding in findings:
        message = explain(finding)
        print_output(message)

    # Structured log
    log_file = log_findings(findings)
    print(f"\n📁 Full log written to: {log_file}")
    print(
        f"\n⛔  Commit blocked — {len(findings)} secret(s) detected. "
        "Rotate and remove before pushing."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
