Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host '==> Full packaging pipeline started'

& (Join-Path $PSScriptRoot 'clean.ps1')
if ($LASTEXITCODE -ne 0) {
    throw "Clean failed with exit code $LASTEXITCODE"
}

& (Join-Path $PSScriptRoot 'build_portable.ps1')
if ($LASTEXITCODE -ne 0) {
    throw "Portable build failed with exit code $LASTEXITCODE"
}

& (Join-Path $PSScriptRoot 'build_installer.ps1')
if ($LASTEXITCODE -ne 0) {
    throw "Installer build failed with exit code $LASTEXITCODE"
}

Write-Host '==> Full packaging pipeline completed successfully'
