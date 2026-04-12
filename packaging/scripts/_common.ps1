Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path
}

function Get-AppMetadata {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $versionFile = Join-Path $RepoRoot 'app/version.py'
    if (-not (Test-Path $versionFile)) {
        throw "Version file not found: $versionFile"
    }

    $content = Get-Content -Path $versionFile -Raw

    $versionMatch = [regex]::Match($content, 'VERSION\s*=\s*"([0-9A-Za-z\.\-_]+)"')
    if (-not $versionMatch.Success) {
        throw "Unable to parse VERSION from $versionFile"
    }

    $appNameMatch = [regex]::Match($content, 'APP_NAME\s*=\s*"([^"]+)"')
    if (-not $appNameMatch.Success) {
        throw "Unable to parse APP_NAME from $versionFile"
    }

    $publisherMatch = [regex]::Match($content, 'PUBLISHER\s*=\s*"([^"]+)"')
    if (-not $publisherMatch.Success) {
        throw "Unable to parse PUBLISHER from $versionFile"
    }

    return [ordered]@{
        AppName   = $appNameMatch.Groups[1].Value
        Publisher = $publisherMatch.Groups[1].Value
        Version   = $versionMatch.Groups[1].Value
    }
}

function Find-Iscc {
    $candidatePaths = @(
        (Get-Command iscc.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
        "$Env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
        "$Env:ProgramFiles\Inno Setup 6\ISCC.exe"
    ) | Where-Object { $_ -and $_.Trim() -ne '' }

    foreach ($candidate in $candidatePaths) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    return $null
}

function New-DirectoryIfMissing {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Assert-CommandSucceeded {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandName
    )

    if ($LASTEXITCODE -ne 0) {
        throw "$CommandName failed with exit code $LASTEXITCODE"
    }
}
