/**
 * AI Gitleaks Agent — VS Code Extension
 * Provides real-time secret detection using Gitleaks with AI explanations.
 */

const vscode = require('vscode');
const { exec, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// ── State ─────────────────────────────────────────────────────────────────────
let statusBarItem;
let diagnosticCollection;
let outputChannel;

// ── Activation ────────────────────────────────────────────────────────────────
function activate(context) {
    outputChannel = vscode.window.createOutputChannel('AI Gitleaks Agent');
    diagnosticCollection = vscode.languages.createDiagnosticCollection('gitleaks');
    
    // Status bar
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBarItem.command = 'gitleaksAgent.scanNow';
    statusBarItem.text = '$(shield) Gitleaks';
    statusBarItem.tooltip = 'Click to scan for secrets';
    statusBarItem.show();

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('gitleaksAgent.scanNow', () => scanWorkspace(false)),
        vscode.commands.registerCommand('gitleaksAgent.scanStaged', () => scanWorkspace(true)),
        vscode.commands.registerCommand('gitleaksAgent.runSetup', runSetup),
        diagnosticCollection,
        statusBarItem,
        outputChannel
    );

    // Auto-scan on save if enabled
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(() => {
            const config = vscode.workspace.getConfiguration('gitleaksAgent');
            if (config.get('scanOnSave')) {
                scanWorkspace(true);
            }
        })
    );

    // Run initial scan on startup
    scanWorkspace(true);
    outputChannel.appendLine('✅ AI Gitleaks Agent activated.');
}

// ── Core Scan Logic ───────────────────────────────────────────────────────────
async function scanWorkspace(stagedOnly) {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) return;

    const workspaceRoot = workspaceFolders[0].uri.fsPath;
    const config = vscode.workspace.getConfiguration('gitleaksAgent');
    const gitleaksPath = config.get('gitleaksPath') || 'gitleaks';
    const configFile = path.join(workspaceRoot, config.get('configPath') || 'config/gitleaks.toml');
    const reportPath = path.join(workspaceRoot, 'reports', 'report.json');

    // Ensure reports directory exists
    const reportsDir = path.join(workspaceRoot, 'reports');
    if (!fs.existsSync(reportsDir)) fs.mkdirSync(reportsDir, { recursive: true });

    // Build command
    const args = [
        stagedOnly ? 'protect' : 'detect',
        stagedOnly ? '--staged' : '--source', 
        stagedOnly ? '' : '.',
        '--report-format', 'json',
        '--report-path', reportPath,
        '--exit-code', '1'
    ].filter(Boolean);

    if (fs.existsSync(configFile)) {
        args.push('--config', configFile);
    }

    // Update status bar
    setStatusBar('scanning');
    outputChannel.appendLine(`\n🔍 Running: ${gitleaksPath} ${args.join(' ')}`);

    return new Promise((resolve) => {
        const proc = spawn(gitleaksPath, args, { cwd: workspaceRoot });
        let stderr = '';

        proc.stderr.on('data', (data) => { stderr += data.toString(); });

        proc.on('close', (code) => {
            if (code === 0) {
                // Clean
                diagnosticCollection.clear();
                setStatusBar('clean');
                outputChannel.appendLine('✅ No secrets found.');
            } else if (code === 1) {
                // Secrets found — parse report
                parseAndShowFindings(reportPath, workspaceRoot);
            } else {
                // Error (gitleaks not installed etc.)
                setStatusBar('error');
                outputChannel.appendLine(`❌ Gitleaks error (exit ${code}): ${stderr}`);
                if (code === 127 || stderr.includes('not found')) {
                    showGitleaksNotInstalledError();
                }
            }
            resolve();
        });

        proc.on('error', (err) => {
            setStatusBar('error');
            outputChannel.appendLine(`❌ Failed to run gitleaks: ${err.message}`);
            showGitleaksNotInstalledError();
            resolve();
        });
    });
}

// ── Parse Report & Show Diagnostics ──────────────────────────────────────────
function parseAndShowFindings(reportPath, workspaceRoot) {
    if (!fs.existsSync(reportPath)) return;

    let findings;
    try {
        findings = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    } catch {
        return;
    }

    if (!findings || findings.length === 0) return;

    // Group diagnostics by file
    const diagMap = new Map();

    findings.forEach(finding => {
        const filePath = path.join(workspaceRoot, finding.File || '');
        const line = Math.max(0, (finding.StartLine || 1) - 1);
        const col = Math.max(0, (finding.StartColumn || 1) - 1);

        const range = new vscode.Range(line, col, line, col + (finding.Secret || '').length);
        const severity = getSeverity(finding.RuleID);

        const message = buildDiagnosticMessage(finding);
        const diagnostic = new vscode.Diagnostic(range, message, severity);
        diagnostic.source = 'Gitleaks';
        diagnostic.code = finding.RuleID;

        const uri = vscode.Uri.file(filePath);
        const key = uri.toString();
        if (!diagMap.has(key)) diagMap.set(key, { uri, diags: [] });
        diagMap.get(key).diags.push(diagnostic);
    });

    // Apply diagnostics
    diagnosticCollection.clear();
    diagMap.forEach(({ uri, diags }) => {
        diagnosticCollection.set(uri, diags);
    });

    // Update status bar
    setStatusBar('found', findings.length);

    // Log to output channel
    outputChannel.appendLine(`\n🚨 ${findings.length} secret(s) detected:`);
    findings.forEach(f => {
        outputChannel.appendLine(`  • [${f.RuleID}] ${f.File}:${f.StartLine} — ${maskSecret(f.Secret)}`);
    });

    // Show notification
    vscode.window.showWarningMessage(
        `🚨 Gitleaks: ${findings.length} secret(s) detected in workspace!`,
        'Show Details',
        'Fix Now'
    ).then(action => {
        if (action === 'Show Details') outputChannel.show();
        if (action === 'Fix Now') vscode.commands.executeCommand('workbench.action.problems.focus');
    });
}

// ── Setup Command ─────────────────────────────────────────────────────────────
async function runSetup() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) return;

    const workspaceRoot = workspaceFolders[0].uri.fsPath;
    const setupScript = path.join(workspaceRoot, 'setup.py');

    if (!fs.existsSync(setupScript)) {
        vscode.window.showErrorMessage('setup.py not found in workspace root.');
        return;
    }

    const terminal = vscode.window.createTerminal('Gitleaks Setup');
    terminal.show();
    terminal.sendText('python setup.py');
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function buildDiagnosticMessage(finding) {
    const masked = maskSecret(finding.Secret || '');
    const remediation = getRemediation(finding.RuleID);
    return [
        `🚨 SECRET DETECTED [${finding.RuleID}]`,
        `Secret: ${masked}`,
        ``,
        `Why dangerous: Hardcoded secrets leak via Git history, forks, and CI logs.`,
        `Fix: ${remediation}`
    ].join('\n');
}

function maskSecret(secret) {
    if (!secret || secret.length <= 8) return '****';
    return secret.slice(0, 4) + '*'.repeat(secret.length - 8) + secret.slice(-4);
}

function getSeverity(ruleId) {
    const critical = ['azure-ad-client-secret', 'aws-access-token', 'aws-secret-key', 'private-key'];
    const high = ['github-pat', 'github-oauth', 'slack-token'];
    if (critical.includes(ruleId)) return vscode.DiagnosticSeverity.Error;
    if (high.includes(ruleId)) return vscode.DiagnosticSeverity.Warning;
    return vscode.DiagnosticSeverity.Warning;
}

function getRemediation(ruleId) {
    const map = {
        'azure-ad-client-secret': 'Revoke in Azure Portal → App Registrations → Certificates & Secrets. Use Azure Key Vault.',
        'aws-access-token': 'Deactivate in AWS IAM console. Use IAM Roles or AWS Secrets Manager.',
        'github-pat': 'Revoke under GitHub Settings → Developer Settings → Personal Access Tokens.',
        'private-key': 'Rotate the key pair. Use ssh-agent or a hardware token.',
        'generic-password': 'Move to environment variable or secrets manager.',
    };
    return map[ruleId] || 'Move to environment variable or use a secrets manager (Azure Key Vault, AWS Secrets Manager, HashiCorp Vault).';
}

function setStatusBar(state, count) {
    const icons = { scanning: '$(sync~spin)', clean: '$(shield)', found: '$(warning)', error: '$(error)' };
    const labels = {
        scanning: '$(sync~spin) Gitleaks: Scanning…',
        clean: '$(shield) Gitleaks: Clean ✓',
        found: `$(warning) Gitleaks: ${count} secret(s)!`,
        error: '$(error) Gitleaks: Error'
    };
    statusBarItem.text = labels[state] || '$(shield) Gitleaks';
    statusBarItem.backgroundColor = state === 'found' || state === 'error'
        ? new vscode.ThemeColor('statusBarItem.warningBackground')
        : undefined;
}

function showGitleaksNotInstalledError() {
    vscode.window.showErrorMessage(
        '❌ Gitleaks not found. Please install it to use this extension.',
        'Install Guide'
    ).then(action => {
        if (action === 'Install Guide') {
            vscode.env.openExternal(vscode.Uri.parse('https://github.com/gitleaks/gitleaks#installing'));
        }
    });
}

function deactivate() {
    diagnosticCollection?.clear();
}

module.exports = { activate, deactivate };
