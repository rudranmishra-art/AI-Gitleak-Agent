"""
ai_engine.py
------------
Generates human-readable explanations for Gitleaks findings.

If the ANTHROPIC_API_KEY environment variable is set, real AI explanations
are fetched from Claude. Otherwise a high-quality static template is used
so the agent works fully offline / without an API key.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Any

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-3-5-haiku-20241022"   # fast + cheap, ideal for CI

# ── Static severity colours for the Rich console ─────────────────────────────
SEVERITY_STYLE = {
    "CRITICAL": "bold white on red",
    "HIGH":     "bold red",
    "MEDIUM":   "bold yellow",
    "LOW":      "yellow",
}

REMEDIATION = {
    "azure-ad-client-secret": (
        "Revoke this secret in Azure Portal → App Registrations → "
        "Certificates & Secrets. Then store the new value in Azure Key Vault "
        "and reference it via an environment variable."
    ),
    "aws-access-token": (
        "Deactivate the key in the AWS IAM console immediately. "
        "Replace with short-lived credentials via IAM Roles or AWS Secrets Manager."
    ),
    "github-pat": (
        "Revoke the token under GitHub Settings → Developer Settings → "
        "Personal Access Tokens. Prefer fine-grained tokens with minimal scopes."
    ),
    "private-key": (
        "Rotate the key pair. Never commit private keys — use ssh-agent, "
        "a hardware token, or a secrets manager instead."
    ),
}

_DEFAULT_REMEDIATION = (
    "• Move the value to an environment variable (export SECRET=…)\n"
    "• Or use a secrets manager: Azure Key Vault, AWS Secrets Manager, "
    "HashiCorp Vault, etc.\n"
    "• Rotate the exposed credential immediately.\n"
    "• Add the file pattern to .gitignore and run `git filter-repo` to "
    "purge it from history."
)


def _static_explain(finding: dict[str, Any]) -> str:
    rule_id     = finding.get("RuleID", "unknown")
    severity    = finding.get("Severity", "MEDIUM")
    file_path   = finding.get("File", "unknown")
    line        = finding.get("StartLine", "?")
    description = finding.get("Description", "Secret detected")
    masked      = finding.get("MaskedSecret", "****")
    commit      = finding.get("Commit", "")[:8] or "uncommitted"
    link        = finding.get("Link", "")

    remediation = REMEDIATION.get(rule_id, _DEFAULT_REMEDIATION)

    commit_line = f"Commit      : {commit}" if commit else ""
    link_line   = f"Link        : {link}" if link else ""

    extra = "\n".join(filter(None, [commit_line, link_line]))

    return (
        f"\n{'═'*60}\n"
        f"🚨  [{severity}] SECRET DETECTED\n"
        f"{'─'*60}\n"
        f"Rule        : {rule_id}\n"
        f"Description : {description}\n"
        f"File        : {file_path}  (line {line})\n"
        f"Secret      : {masked}\n"
        f"{extra}\n"
        f"{'─'*60}\n"
        f"⚠  Why dangerous?\n"
        f"   Hardcoded secrets are exposed in Git history, CI logs,\n"
        f"   forks, and anyone who clones the repository.\n\n"
        f"✅  Recommended fix:\n"
        f"   {remediation}\n"
        f"{'═'*60}\n"
    )


def _ai_explain(finding: dict[str, Any]) -> str | None:
    """
    Call the Anthropic API to generate a contextual explanation.
    Returns None on any error so the caller can fall back gracefully.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None

    prompt = (
        f"A secret was detected in a Git repository by Gitleaks.\n\n"
        f"Finding details (JSON):\n{json.dumps(finding, indent=2)}\n\n"
        f"Please provide:\n"
        f"1. A plain-English explanation of what this secret is and why "
        f"   its exposure is dangerous.\n"
        f"2. Specific, actionable remediation steps for this type of secret.\n"
        f"3. How to prevent this from happening again.\n"
        f"Keep the response concise (under 200 words) and developer-friendly."
    )

    payload = json.dumps({
        "model": _MODEL,
        "max_tokens": 512,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        _ANTHROPIC_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
            return body["content"][0]["text"]
    except Exception:
        return None


def explain(finding: dict[str, Any]) -> str:
    """Return an explanation string for a single Gitleaks finding."""
    ai_text = _ai_explain(finding)
    if ai_text:
        header = (
            f"\n{'═'*60}\n"
            f"🚨  [{finding.get('Severity','MEDIUM')}] "
            f"{finding.get('RuleID','secret')}  — "
            f"{finding.get('File','?')} line {finding.get('StartLine','?')}\n"
            f"{'─'*60}\n"
        )
        return header + ai_text + f"\n{'═'*60}\n"
    return _static_explain(finding)
