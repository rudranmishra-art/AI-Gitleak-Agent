import json
import os
from typing import Any

# Map Gitleaks rule IDs → human severity labels
SEVERITY_MAP: dict[str, str] = {
    "azure-ad-client-secret": "CRITICAL",
    "aws-access-token": "CRITICAL",
    "aws-secret-key": "CRITICAL",
    "github-pat": "HIGH",
    "private-key": "HIGH",
    "generic-api-key": "MEDIUM",
    "generic-secret": "MEDIUM",
}

REQUIRED_FIELDS = {"RuleID", "File", "StartLine", "Secret", "Description"}


def _enrich(finding: dict[str, Any]) -> dict[str, Any]:
    """Add a severity field and sanitise the secret for display."""
    rule_id = finding.get("RuleID", "")
    finding["Severity"] = SEVERITY_MAP.get(rule_id, "MEDIUM")
    # Mask the middle of the secret so it's not fully printed to console
    secret: str = finding.get("Secret", "")
    if len(secret) > 8:
        finding["MaskedSecret"] = secret[:4] + "*" * (len(secret) - 8) + secret[-4:]
    else:
        finding["MaskedSecret"] = "****"
    return finding


def analyze(report_path: str) -> list[dict[str, Any]]:
    """
    Parse and enrich findings from a Gitleaks JSON report.

    Returns an empty list on any read/parse error.
    """
    if not os.path.isfile(report_path):
        return []

    try:
        with open(report_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(raw, list):
        return []

    findings = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        # Only keep findings that have the minimum expected fields
        if REQUIRED_FIELDS.issubset(item.keys()):
            findings.append(_enrich(item))

    return findings
