param([Parameter(Mandatory=$true)][string]$Project)
$ErrorActionPreference = 'Stop'
if ($Project -notmatch '^[a-zA-Z0-9_.-]+$') { throw 'Invalid project directory name.' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$folder = Join-Path (Join-Path $root 'workspace') $Project
if (-not (Test-Path (Join-Path $folder '.git'))) { throw 'Not a git repository.' }
Set-Location $folder
git fetch --prune
if ($LASTEXITCODE -ne 0) { throw 'git fetch failed. Check repository access.' }
git status -sb
Write-Host 'No automatic reset, pull, rebase, merge, push or force-push performed.'
