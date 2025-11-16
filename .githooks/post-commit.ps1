<#
.githooks/post-commit.ps1 - PowerShell post-commit wrapper
Calls repo log_writer.py --from-hook. Designed for Windows/PowerShell environments.
#>
try {
    $repo = git rev-parse --show-toplevel 2>$null
} catch {
    $repo = $null
}
if (-not $repo) {
    $repo = (Get-Location).Path
}
$repo = $repo.Trim()
if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 "$repo\log_writer.py" --from-hook
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python "$repo\log_writer.py" --from-hook
} else {
    & "$repo\log_writer.py" --from-hook
}
