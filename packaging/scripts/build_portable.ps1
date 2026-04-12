Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '_common.ps1')

$repoRoot = Get-RepoRoot
$meta = Get-AppMetadata -RepoRoot $repoRoot
$appName = $meta.AppName
$version = $meta.Version

$specFile = Join-Path $repoRoot 'packaging/pyinstaller/ctrlv.spec'
$distPortableDir = Join-Path $repoRoot 'dist/CtrlV-portable'
$releasePortableRoot = Join-Path $repoRoot 'release/portable'
$releasePortableDir = Join-Path $releasePortableRoot ("{0}-{1}-portable" -f $appName, $version)
$portableReadmeTemplate = Join-Path $repoRoot 'packaging/templates/portable_README.txt'

Write-Host ("==> Building portable package: {0} v{1}" -f $appName, $version)

if (-not (Test-Path $specFile)) {
    throw "PyInstaller spec file not found: $specFile"
}

$pyInstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyInstaller) {
    throw 'PyInstaller is not available. Activate the virtual environment and install build requirements.'
}

Write-Host "   PyInstaller: $($pyInstaller.Source)"
Write-Host "   Spec file  : $specFile"

Push-Location $repoRoot
try {
    & $pyInstaller.Source '--noconfirm' '--clean' $specFile
    Assert-CommandSucceeded -CommandName 'PyInstaller'
}
finally {
    Pop-Location
}

if (-not (Test-Path $distPortableDir)) {
    throw "Portable output directory was not generated: $distPortableDir"
}

$versionFileDist = Join-Path $distPortableDir 'VERSION.txt'
Set-Content -Path $versionFileDist -Value $version -NoNewline

if (Test-Path $portableReadmeTemplate) {
    Copy-Item -Path $portableReadmeTemplate -Destination (Join-Path $distPortableDir 'README.txt') -Force
}

New-DirectoryIfMissing -Path $releasePortableRoot
if (Test-Path $releasePortableDir) {
    Remove-Item -Path $releasePortableDir -Recurse -Force
}
Copy-Item -Path $distPortableDir -Destination $releasePortableDir -Recurse -Force

Write-Host ("==> Portable dist folder   : {0}" -f $distPortableDir)
Write-Host ("==> Portable release folder: {0}" -f $releasePortableDir)
Write-Host '==> Portable package build completed successfully.'
