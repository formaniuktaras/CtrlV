Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '_common.ps1')

$repoRoot = Get-RepoRoot
$meta = Get-AppMetadata -RepoRoot $repoRoot

Write-Host ("==> Full packaging pipeline started for {0} v{1}" -f $meta.AppName, $meta.Version)

& (Join-Path $PSScriptRoot 'clean.ps1')
Assert-CommandSucceeded -CommandName 'clean.ps1'

& (Join-Path $PSScriptRoot 'build_portable.ps1')
Assert-CommandSucceeded -CommandName 'build_portable.ps1'

& (Join-Path $PSScriptRoot 'build_installer.ps1')
Assert-CommandSucceeded -CommandName 'build_installer.ps1'

Write-Host '==> Full packaging pipeline completed successfully.'
Write-Host ("==> Portable output : {0}" -f (Join-Path $repoRoot 'release/portable'))
Write-Host ("==> Installer output: {0}" -f (Join-Path $repoRoot 'release/installer'))
