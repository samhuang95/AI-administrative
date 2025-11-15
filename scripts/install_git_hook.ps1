param()

# Install post-commit git hook (PowerShell)
# Writes a LF-only, UTF-8 (no BOM) hook that invokes log_writer.py --from-hook

function Get-RepoRoot {
    $out = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $out) { return (Get-Location).ProviderPath }
    return $out.Trim()
}

$repo = Get-RepoRoot
$hookDir = Join-Path $repo '.git/hooks'
if (-not (Test-Path $hookDir)) { New-Item -ItemType Directory -Path $hookDir | Out-Null }
$hookPath = Join-Path $hookDir 'post-commit'

$hook = @'
#!/usr/bin/env bash
set -e

# Simple post-commit hook that delegates work to Python.
# Python will call git itself to obtain the last commit message and changed files.

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$REPO_ROOT" ]; then
    REPO_ROOT="."
fi

if command -v py >/dev/null 2>&1; then
    PYCMD="py -3"
elif command -v python3 >/dev/null 2>&1; then
    PYCMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYCMD="python"
else
    echo "Python not found in PATH; skipping log append." >&2
    exit 0
fi

LOG_WRITER="$REPO_ROOT/log_writer.py"
if [ -f "$LOG_WRITER" ]; then
    exec $PYCMD "$LOG_WRITER" --from-hook
else
    echo "log_writer.py not found at $LOG_WRITER; skipping." >&2
    exit 0
fi
'

# Ensure LF line endings and UTF8 bytes without BOM
$hook = $hook -replace "`r`n","`n"
[System.IO.File]::WriteAllBytes($hookPath,[System.Text.Encoding]::UTF8.GetBytes($hook))

# Try to set executable bit using bash if available
if (Get-Command bash -ErrorAction SilentlyContinue) {
    bash -lc "chmod +x '$hookPath' || true"
}

Write-Host "Installed post-commit hook at $hookPath"
<#
PowerShell helper to install a git post-commit hook that appends commit info
to `log.md` by calling the Python module `log_writer`.

Run from repository root with PowerShell (recommended):
  .\scripts\install_git_hook.ps1

This will write `.git/hooks/post-commit`. The hook will invoke Python to
append the last commit message and changed files to `log.md`.
#>

param()

try {
    $gitRoot = (& git rev-parse --show-toplevel).Trim()
} catch {
    Write-Error "Not a git repository or git not available. Run this from the repo root."
    exit 1
}

$hookPath = Join-Path $gitRoot ".git/hooks/post-commit"

$hookContent = @'
#!/usr/bin/env bash
# post-commit hook: append commit info to log.md via Python
COMMIT_MSG=$(git log -1 --pretty=%B | tr '\n' ' ')
FILES=$(git diff-tree --no-commit-id --name-only -r HEAD | tr '\n' ',' | sed 's/,$//')
py -3 -m log_writer "$COMMIT_MSG" --action COMMIT --files "$FILES" --command "git commit -m \"$COMMIT_MSG\""
'@

Set-Content -Path $hookPath -Value $hookContent -Encoding UTF8
Write-Host "Installed post-commit hook at $hookPath"
