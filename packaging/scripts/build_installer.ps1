Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '_common.ps1')

$repoRoot = Get-RepoRoot
$version = Get-Version -RepoRoot $repoRoot
$portableDir = Join-Path $repoRoot 'dist/CtrlV-portable'
$portableExe = Join-Path $portableDir 'CtrlV.exe'
$issFile = Join-Path $repoRoot 'packaging/inno/ctrlv_installer.iss'
$releaseInstallerDir = Join-Path $repoRoot 'release/installer'
$innoOutputDir = Join-Path $repoRoot 'release/installer'
$iconPath = Join-Path $repoRoot 'assets/icons/app.ico'

Write-Host "==> Building CtrlV installer (version $version)"

if (-not (Test-Path $portableExe)) {
    throw "Portable build not found at $portableExe. Run packaging/scripts/build_portable.ps1 first."
}

if (-not (Test-Path $issFile)) {
    throw "Inno Setup script not found: $issFile"
}

$iscc = Find-Iscc
if (-not $iscc) {
    throw "ISCC.exe was not found. Install Inno Setup 6 and ensure ISCC.exe is in PATH or installed in Program Files. Download: https://jrsoftware.org/isdl.php"
}

New-DirectoryIfMissing -Path $releaseInstallerDir

$iconArg = "/DAppIconPath=$iconPath"
if (-not (Test-Path $iconPath)) {
    Write-Host "   Icon file not found ($iconPath). Installer will use default icon."
    $iconArg = '/DAppIconPath='
}

Write-Host "   Using ISCC: $iscc"
Write-Host "   Using script: $issFile"

$args = @(
    "/DRepoRoot=$repoRoot",
    "/DMyAppVersion=$version",
    "/DPortableDir=$portableDir",
    "/DInstallerOutputDir=$innoOutputDir",
    $iconArg,
    $issFile
)

& $iscc @args

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup build failed with exit code $LASTEXITCODE"
}

Write-Host "==> Installer build complete. Output folder: $releaseInstallerDir"
