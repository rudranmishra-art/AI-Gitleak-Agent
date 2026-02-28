import os
import json
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()

SEVERITY_COLOUR = {
    "CRITICAL": "bold white on red",
    "HIGH":     "bold red",
    "MEDIUM":   "bold yellow",
    "LOW":      "yellow",
}


def log_findings(findings: list[dict[str, Any]]) -> str:
    """
    Write a structured JSON log file and return its path.
    Each entry includes timestamp, file, rule, severity, masked secret,
    and commit info — but NOT the full plaintext secret.
    """
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/security_{timestamp}.log"

    log_entries = []
    for f in findings:
        log_entries.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity":  f.get("Severity", "MEDIUM"),
            "rule_id":   f.get("RuleID", ""),
            "file":      f.get("File", ""),
            "line":      f.get("StartLine"),
            "masked_secret": f.get("MaskedSecret", "****"),
            "commit":    f.get("Commit", "")[:8],
            "author":    f.get("Author", ""),
            "link":      f.get("Link", ""),
        })

    with open(log_file, "w", encoding="utf-8") as fh:
        json.dump(log_entries, fh, indent=2)

    return log_file


def print_summary_table(findings: list[dict[str, Any]]) -> None:
    """Print a Rich summary table before the detailed explanations."""
    table = Table(title="🔐 Secret Scan Results", show_lines=True)
    table.add_column("Severity", style="bold", width=10)
    table.add_column("Rule ID", width=28)
    table.add_column("File", width=20)
    table.add_column("Line", justify="right", width=6)
    table.add_column("Masked Secret", width=24)

    for f in findings:
        severity = f.get("Severity", "MEDIUM")
        colour   = SEVERITY_COLOUR.get(severity, "white")
        table.add_row(
            Text(severity, style=colour),
            f.get("RuleID", ""),
            f.get("File", ""),
            str(f.get("StartLine", "")),
            f.get("MaskedSecret", "****"),
        )

    console.print(table)


def print_output(message: str) -> None:
    """Print a single finding explanation to the console."""
    console.print(message, style="bold red")
