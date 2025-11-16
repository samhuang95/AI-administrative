<#
scripts/install_hooks.ps1
Install repository-tracked Git hooks by setting core.hooksPath to .githooks

Usage:
  # from repo root (PowerShell)
  .\scripts\install_hooks.ps1

Optional: pass -Global to set global core.hooksPath as well (affects all repos for the current user).
#>
param(
    [switch]$Global
)

# Change working directory to the repository root (script folder's parent)
$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$repoRoot = Join-Path -Path $scriptDir -ChildPath ".."
Push-Location -LiteralPath $repoRoot | Out-Null
Set-Location -LiteralPath (Resolve-Path -LiteralPath $repoRoot) | Out-Null

if (-not (Test-Path -LiteralPath ".githooks")) {
    New-Item -ItemType Directory -Path .githooks | Out-Null
    Write-Output "Created .githooks directory"
} else {
    Write-Output ".githooks already exists"
}

git config core.hooksPath .githooks
Write-Output "Set repository core.hooksPath to .githooks"

if ($Global) {
    git config --global core.hooksPath .githooks
    Write-Output "Also set global core.hooksPath to .githooks"
}

Write-Output "Done. Run 'git config --get core.hooksPath' to verify."
Pop-Location | Out-Null
