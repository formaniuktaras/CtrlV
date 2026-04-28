Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '_common.ps1')

$repoRoot = Get-RepoRoot
$meta = Get-AppMetadata -RepoRoot $repoRoot
$appName = $meta.AppName
$publisher = $meta.Publisher
$version = $meta.Version

$portableDir = Join-Path $repoRoot 'dist/CtrlV-portable'
$portableExe = Join-Path $portableDir "$appName.exe"
$issFile = Join-Path $repoRoot 'packaging/inno/ctrlv_installer.iss'
$releaseInstallerDir = Join-Path $repoRoot 'release/installer'
$iconPath = Join-Path $repoRoot 'assets/icons/app.ico'

Write-Host ("==> Building installer package: {0} v{1}" -f $appName, $version)

if (-not (Test-Path $portableExe)) {
    throw "Portable executable not found at $portableExe. Run packaging/scripts/build_portable.ps1 first."
}

if (-not (Test-Path $issFile)) {
    throw "Inno Setup script not found: $issFile"
}

$iscc = Find-Iscc
if (-not $iscc) {
    throw 'Inno Setup (ISCC.exe) was not found. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php and ensure ISCC.exe is available in PATH or Program Files.'
}

New-DirectoryIfMissing -Path $releaseInstallerDir

$iconArg = "/DAppIconPath=$iconPath"
if (-not (Test-Path $iconPath)) {
    Write-Warning "Icon file not found ($iconPath). Using default installer icon."
    $iconArg = '/DAppIconPath='
}

Write-Host "   ISCC       : $iscc"
Write-Host "   Script file: $issFile"

$args = @(
    "/DMyAppName=$appName",
    "/DMyAppPublisher=$publisher",
    "/DMyAppVersion=$version",
    "/DMyAppExeName=$appName.exe",
    "/DPortableDir=$portableDir",
    "/DInstallerOutputDir=$releaseInstallerDir",
    $iconArg,
    $issFile
)

& $iscc @args
Assert-CommandSucceeded -CommandName 'Inno Setup (ISCC)'

$expectedInstaller = Join-Path $releaseInstallerDir ("{0}-Setup-{1}.exe" -f $appName, $version)
if (-not (Test-Path $expectedInstaller)) {
    throw "Installer build completed but expected artifact is missing: $expectedInstaller"
}

Write-Host ("==> Installer artifact: {0}" -f $expectedInstaller)
Write-Host '==> Installer package build completed successfully.'
