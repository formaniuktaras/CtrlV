Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '_common.ps1')

$repoRoot = Get-RepoRoot
$version = Get-Version -RepoRoot $repoRoot
$specFile = Join-Path $repoRoot 'packaging/pyinstaller/ctrlv.spec'
$portableDir = Join-Path $repoRoot 'dist/CtrlV-portable'
$portableReleaseDir = Join-Path $repoRoot 'release/portable'
$portableReadmeTemplate = Join-Path $repoRoot 'packaging/templates/portable_README.txt'
$portableVersionFile = Join-Path $portableDir 'VERSION.txt'

Write-Host "==> Building CtrlV portable (version $version)"

if (-not (Test-Path $specFile)) {
    throw "PyInstaller spec file not found: $specFile"
}

$pyInstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyInstaller) {
    throw 'PyInstaller is not available. Activate your virtual environment and install requirements.'
}

Write-Host "   Using pyinstaller: $($pyInstaller.Source)"
Write-Host "   Using spec file: $specFile"

Push-Location $repoRoot
try {
    & $pyInstaller.Source '--noconfirm' '--clean' $specFile
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path $portableDir)) {
    throw "Portable output folder was not generated: $portableDir"
}

New-DirectoryIfMissing -Path $portableReleaseDir
$releasePortableVersionDir = Join-Path $portableReleaseDir ("CtrlV-portable-{0}" -f $version)
if (Test-Path $releasePortableVersionDir) {
    Remove-Item -Path $releasePortableVersionDir -Recurse -Force
}

Copy-Item -Path $portableDir -Destination $releasePortableVersionDir -Recurse -Force

Set-Content -Path $portableVersionFile -Value $version -NoNewline
Copy-Item -Path $portableVersionFile -Destination (Join-Path $releasePortableVersionDir 'VERSION.txt') -Force

if (Test-Path $portableReadmeTemplate) {
    Copy-Item -Path $portableReadmeTemplate -Destination (Join-Path $portableDir 'README.txt') -Force
    Copy-Item -Path $portableReadmeTemplate -Destination (Join-Path $releasePortableVersionDir 'README.txt') -Force
}

Write-Host "==> Portable build complete: $portableDir"
Write-Host "==> Portable release copy: $releasePortableVersionDir"
