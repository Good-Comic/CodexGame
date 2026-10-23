param([Parameter(Mandatory=$true)][string]$Repo)
$ErrorActionPreference = 'Stop'
if ($Repo -notmatch '^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$') { throw 'Expected OWNER/REPO.' }
foreach ($cmd in @('git','gh')) { if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "$cmd not installed." } }
gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Run: gh auth login (on host).' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$dir = Join-Path $root 'workspace'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$targetName = ($Repo -split '/')[1]
$target = Join-Path $dir $targetName
if (Test-Path $target) { throw "Project exists: $target. Refusing overwrite." }
gh repo clone $Repo $target
if ($LASTEXITCODE -ne 0) { throw 'GitHub clone failed.' }
Write-Host "Cloned to: $target"
Write-Host "In Agent Canvas choose project folder: /projects/$targetName"
Write-Host 'Never commit API keys. AI should work in a feature branch.'
