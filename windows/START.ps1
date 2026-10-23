$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker not found. Install Docker Desktop first.' }
foreach ($d in @('workspace', 'state')) { New-Item -ItemType Directory -Force -Path (Join-Path $root $d) | Out-Null }
docker compose up -d
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose failed. Review Docker Desktop and image availability.' }
Write-Host 'OpenHands Canvas: http://127.0.0.1:8000/canvas'
Write-Host 'Only local loopback is exposed. Configure your model/provider in the UI.'
Start-Process 'http://127.0.0.1:8000/canvas'
