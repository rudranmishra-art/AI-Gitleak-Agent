# AI Gitleaks Agent — VS Code Extension

Real-time secret detection inside VS Code, powered by Gitleaks and AI explanations.

## Features

- 🔍 **Auto-scan on save** — scans staged files every time you save
- 🚨 **Inline warnings** — secrets highlighted directly in the editor (Problems panel)
- 📊 **Status bar** — live scan status always visible
- 🤖 **AI explanations** — detailed remediation advice per finding
- ⌨️ **Keyboard shortcut** — `Ctrl+Shift+G S` to scan anytime
- 🔧 **Setup command** — installs pre-commit hook for teammates

## Requirements

- [Gitleaks](https://github.com/gitleaks/gitleaks/releases) installed and on PATH
- Your `AI-Gitleak-Agent` repo cloned locally

## Installation

### Option A — Install from VSIX (recommended)
```
1. Download gitleaks-agent-1.0.0.vsix
2. Open VS Code
3. Ctrl+Shift+P → "Extensions: Install from VSIX"
4. Select the .vsix file
```

### Option B — Manual
```
1. Copy the gitleaks-agent folder to:
   Windows: %USERPROFILE%\.vscode\extensions\
   Mac/Linux: ~/.vscode/extensions/
2. Restart VS Code
```

## Settings

| Setting | Default | Description |
|---|---|---|
| `gitleaksAgent.gitleaksPath` | `gitleaks` | Path to gitleaks binary |
| `gitleaksAgent.configPath` | `config/gitleaks.toml` | Path to custom rules config |
| `gitleaksAgent.anthropicApiKey` | `""` | API key for AI explanations |
| `gitleaksAgent.scanOnSave` | `true` | Auto-scan on file save |
| `gitleaksAgent.showStatusBar` | `true` | Show status bar item |

## Commands

| Command | Shortcut | Description |
|---|---|---|
| Scan for Secrets Now | `Ctrl+Shift+G S` | Full workspace scan |
| Scan Staged Files | — | Scan only git staged files |
| Run Setup | — | Install pre-commit hook |
