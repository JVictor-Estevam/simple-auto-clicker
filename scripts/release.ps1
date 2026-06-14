# Build and publish a GitHub release with the Windows executable.
# Usage: .\scripts\release.ps1 -Version 1.0.0

param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Tag = "v$Version"
$Exe = Join-Path $Root "dist\Simple AutoClicker.exe"

Set-Location $Root

Write-Host "Building icon assets..."
python (Join-Path $Root "scripts\build_icon.py")

Write-Host "Building executable..."
pyinstaller (Join-Path $Root "build.spec") --noconfirm

if (-not (Test-Path $Exe)) {
    throw "Executable not found: $Exe"
}

if (Get-Command gh -ErrorAction SilentlyContinue) {
    $null = gh auth status 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Run 'gh auth login' first."
        exit 1
    }
} else {
    throw "GitHub CLI (gh) is not installed. Install from https://cli.github.com/"
}

$ExistingTag = git tag -l $Tag
if ($ExistingTag) {
    Write-Host "Tag $Tag already exists locally."
} else {
    git tag $Tag
    git push origin $Tag
}

$Notes = @"
## Simple AutoClicker $Tag

### Windows
Download **Simple AutoClicker.exe** below and run it. No Python required.

### Source
Use the **Source code** archives attached to this release, or clone the repository at tag ``$Tag``.

### Highlights
- Timed mouse clicks or keyboard input
- Fixed coordinates or cursor-following mode
- Settings persistence
- Global stop hotkey (F7 / F8)
"@

$prevErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"
gh release view $Tag 2>&1 | Out-Null
$releaseExists = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $prevErrorAction

if ($releaseExists) {
    gh release upload $Tag $Exe --clobber
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Release $Tag updated with executable."
} else {
    gh release create $Tag $Exe --title $Tag --notes $Notes
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Release $Tag created."
}

Write-Host "https://github.com/JVictor-Estevam/simple-auto-clicker/releases/tag/$Tag"
