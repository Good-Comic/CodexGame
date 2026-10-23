param([Parameter(Mandatory=$true)][string]$Project)
$ErrorActionPreference = 'Stop'
if ($Project -notmatch '^[a-zA-Z0-9_.-]+$') { throw 'Project must be simple directory name.' }
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) { throw 'Node.js and npm/npx required.' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$folder = Join-Path (Join-Path $root 'workspace') $Project
if (-not (Test-Path (Join-Path $folder 'index.html'))) { throw "Cannot find index.html in $folder" }
Set-Location $folder
Write-Host 'Vite live preview at http://127.0.0.1:4173'
Write-Host 'Exit with Ctrl+C. Requires downloading Vite if it is not already installed.'
npx --yes vite@7 --host 127.0.0.1 --port 4173
