Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '_common.ps1')

$repoRoot = Get-RepoRoot
$targets = @(
    (Join-Path $repoRoot 'build'),
    (Join-Path $repoRoot 'dist'),
    (Join-Path $repoRoot 'release')
)

Write-Host '==> Cleaning packaging output directories...'
foreach ($target in $targets) {
    if (Test-Path $target) {
        Write-Host "   Removing: $target"
        Remove-Item -Path $target -Recurse -Force
    }
    else {
        Write-Host "   Not found: $target"
    }
}

Write-Host '==> Clean step completed successfully.'
