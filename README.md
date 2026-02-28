# AI-Gitleak-Agent

Enterprise-ready secret detection agent for Git repositories.  
Wraps [Gitleaks](https://github.com/gitleaks/gitleaks) with AI-powered explanations (Claude), structured logging, and CI/CD-ready workflows.

---

## Architecture

```
main.py
└── agent/
    ├── scanner.py    — runs gitleaks, returns (exit_code, report_path)
    ├── analyzer.py   — parses + enriches JSON report (severity, masking)
    ├── ai_engine.py  — generates explanations (Claude API or static fallback)
    ├── reporter.py   — Rich console output + structured JSON logs
    └── utils.py      — directory helpers
config/
    ├── config.yaml   — agent configuration
    └── gitleaks.toml — custom detection rules
.github/workflows/
    └── security.yml  — GitHub Actions CI pipeline
hooks/
    └── pre-commit    — local Git hook (blocks commits with secrets)
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Gitleaks

```bash
# macOS
brew install gitleaks

# Linux / Windows — download from releases:
# https://github.com/gitleaks/gitleaks/releases
```

### 3. (Optional) Enable AI explanations

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

If the key is not set, the agent still works using high-quality static explanations.

### 4. Run a scan

```bash
python main.py
```

---

## Pre-commit Hook (local blocking)

Copy the hook into `.git/hooks/` to block commits that contain secrets:

```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Or use `pre-commit` framework (see `.pre-commit-config.yaml`):

```bash
pip install pre-commit
pre-commit install
```

---

## CI/CD (GitHub Actions)

The workflow at `.github/workflows/security.yml`:

- Runs on every push and pull request
- Uses the official `gitleaks/gitleaks-action` for the scan
- Then runs this agent for enriched AI output
- Uploads `reports/report.json` and `logs/` as build artefacts (retained 30 days)

**Add your Anthropic API key as a repository secret:**  
`Settings → Secrets and variables → Actions → New repository secret`  
Name: `ANTHROPIC_API_KEY`

---

## Output

```
🔍 Running Gitleaks scan…

┌─────────────────────────────────────────────────────┐
│              🔐 Secret Scan Results                 │
├──────────┬────────────────────────┬──────┬──────────┤
│ Severity │ Rule ID                │ File │ Line     │
├──────────┼────────────────────────┼──────┼──────────┤
│ CRITICAL │ azure-ad-client-secret │ code │ 1        │
│ MEDIUM   │ generic-api-key        │ code │ 2        │
└──────────┴────────────────────────┴──────┴──────────┘

════════════════════════════════════════════════════════════
🚨  [CRITICAL] azure-ad-client-secret — code line 1
…AI or static explanation…
════════════════════════════════════════════════════════════

📁 Full log written to: logs/security_20260228_210122.log
⛔  Commit blocked — 2 secret(s) detected.
```

---

## Security Notes

> ⚠️ **The `code` file in this repository contains example credentials used to demonstrate detection.**  
> If you forked this repo, rotate those credentials immediately.  
> Real secrets should **never** be committed — use environment variables or a secrets manager.

---

## VS Code Integration

Install the **Gitleaks** and **Error Lens** extensions for real-time highlighting.

Add a workspace task (`.vscode/tasks.json`):

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Security Scan",
      "type": "shell",
      "command": "python main.py",
      "group": "build",
      "presentation": { "reveal": "always" }
    }
  ]
}
```
