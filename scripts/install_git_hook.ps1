<#
PowerShell helper to install a git post-commit hook that appends commit info
to `log.md` by calling the Python module `ai_agent.log_writer`.

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
py -3 -m ai_agent.log_writer "$COMMIT_MSG" --action COMMIT --files "$FILES" --command "git commit -m \"$COMMIT_MSG\""
'@

Set-Content -Path $hookPath -Value $hookContent -Encoding UTF8
Write-Host "Installed post-commit hook at $hookPath"
