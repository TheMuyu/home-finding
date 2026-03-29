<#
.SYNOPSIS
    Deploy HomeApp to C:\Apps\HomeApp (or a custom path).

.DESCRIPTION
    Syncs files to the target directory, sets up a Python virtual environment,
    installs all dependencies,
    installs Playwright Chromium, and writes a start.bat launcher.

    Existing .env and database files are never overwritten.

.PARAMETER Target
    Destination folder. Defaults to C:\Apps\HomeApp.

.PARAMETER IncludeDb
    When specified, copies apartment_finder.db from source to target (overwrites).
    Omit this flag to preserve existing data at the target.

.EXAMPLE
    .\deploy-local.ps1
    .\deploy-local.ps1 -Target "D:\Apps\HomeApp"
    .\deploy-local.ps1 -IncludeDb
    .\deploy-local.ps1 -Target "D:\Apps\HomeApp" -IncludeDb
#>
param(
    [string]$Target = "C:\Apps\HomeApp",
    [switch]$IncludeDb
)

$ErrorActionPreference = "Stop"
$Source = $PSScriptRoot   # always the folder this script lives in

function Step([string]$msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function OK([string]$msg) { Write-Host "    OK  $msg" -ForegroundColor Green }
function Warn([string]$msg) { Write-Host "    WARN $msg" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# 1. Create target directory
# ---------------------------------------------------------------------------
Step "Preparing target directory: $Target"
New-Item -ItemType Directory -Force -Path $Target | Out-Null
OK "Directory ready."

# ---------------------------------------------------------------------------
# 2. Sync application files (preserve database/ and .env)
# ---------------------------------------------------------------------------
Step "Syncing application files to $Target..."
# robocopy exit codes 0-7 are success; >=8 means an error occurred.
robocopy $Source $Target /E /PURGE `
    /XD ".git" ".venv" "__pycache__" "database" ".claude" ".windsurf" `
    /XF "*.pyc" "*.db" "deploy-local.ps1" `
    /NFL /NDL /NJH /NJS
if ($LASTEXITCODE -ge 8) { throw "robocopy failed (exit $LASTEXITCODE)" }
OK "Application files synced."

# Sync database/ Python module files — never overwrite *.db (user data)
Step "Syncing database module (preserving existing data)..."
New-Item -ItemType Directory -Force -Path "$Target\database" | Out-Null
robocopy "$Source\database" "$Target\database" /E /XF "*.db" /NFL /NDL /NJH /NJS
if ($LASTEXITCODE -ge 8) { throw "robocopy (database) failed (exit $LASTEXITCODE)" }
OK "Database module synced — existing .db files untouched."

# ---------------------------------------------------------------------------
# 2b. Optionally copy the database file
# ---------------------------------------------------------------------------
$dbSource = "$Source\database\apartment_finder.db"
$dbTarget = "$Target\database\apartment_finder.db"
if ($IncludeDb) {
    Step "Copying database file to target (-IncludeDb specified)..."
    if (Test-Path $dbSource) {
        Copy-Item $dbSource $dbTarget -Force
        OK "apartment_finder.db copied to $dbTarget"
    } else {
        Warn "Source DB not found at $dbSource — skipped."
    }
} else {
    if (Test-Path $dbTarget) {
        OK "Database file preserved at target (use -IncludeDb to overwrite)."
    } else {
        Warn "No database file at target yet — it will be created on first run."
    }
}

# ---------------------------------------------------------------------------
# 3. Copy .env (only if target doesn't already have one)
# ---------------------------------------------------------------------------
Step "Checking .env configuration..."
if (-not (Test-Path "$Target\.env")) {
    if (Test-Path "$Source\.env") {
        Copy-Item "$Source\.env" "$Target\.env"
        OK "Copied .env from source."
    }
    else {
        Copy-Item "$Source\.env.example" "$Target\.env"
        Warn ".env not found — copied .env.example to $Target\.env"
        Warn "Open $Target\.env and fill in your API keys before starting the app."
    }
}
else {
    OK ".env already exists at target — skipped (keys preserved)."
}

# ---------------------------------------------------------------------------
# 4. Python virtual environment
# ---------------------------------------------------------------------------
$venv = "$Target\.venv"
Step "Setting up Python virtual environment..."
if (-not (Test-Path "$venv\Scripts\python.exe")) {
    python -m venv $venv
    OK "Virtual environment created."
}
else {
    OK "Virtual environment already exists — skipping creation."
}

# ---------------------------------------------------------------------------
# 5. Install Python dependencies
# ---------------------------------------------------------------------------
Step "Installing Python dependencies..."
& "$venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
& "$venv\Scripts\pip.exe" install -r "$Target\requirements.txt" --quiet
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
OK "Dependencies installed."

# ---------------------------------------------------------------------------
# 6. Install Playwright Chromium browser
# ---------------------------------------------------------------------------
Step "Installing Playwright Chromium browser..."
& "$venv\Scripts\playwright.exe" install chromium
if ($LASTEXITCODE -ne 0) { throw "playwright install failed" }
OK "Playwright Chromium ready."

# ---------------------------------------------------------------------------
# 7. Run database migrations
# ---------------------------------------------------------------------------
Step "Running database migrations on target..."
if (Test-Path $dbTarget) {
    & "$venv\Scripts\python.exe" "$Target\db_migrate.py"
    if ($LASTEXITCODE -ne 0) { throw "db_migrate.py failed" }
    OK "Migrations applied."
} else {
    OK "No database file yet — migrations will run automatically on first app start."
}

# ---------------------------------------------------------------------------
# 8. Write convenience launchers
# ---------------------------------------------------------------------------
Step "Writing launcher scripts..."

# start.bat — double-click launcher
$bat = @"
@echo off
title HomeApp - Stockholm Apartment Finder
echo.
echo  Starting HomeApp...
echo  Press Ctrl+C to stop.
echo.
start "" "chrome.exe" "http://localhost:5000"
timeout /t 2 /nobreak >nul
"$Target\.venv\Scripts\python.exe" "$Target\app.py"
pause
"@
Set-Content -Path "$Target\start.bat" -Value $bat -Encoding ASCII
OK "Launcher: $Target\start.bat"

# start.ps1 — PowerShell launcher
$ps1 = @"
# HomeApp launcher
Write-Host "Starting HomeApp on http://localhost:5000 ..." -ForegroundColor Cyan
& "$Target\.venv\Scripts\python.exe" "$Target\app.py"
"@
Set-Content -Path "$Target\start.ps1" -Value $ps1 -Encoding UTF8
OK "Launcher: $Target\start.ps1"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  HomeApp deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Location : $Target" -ForegroundColor White
Write-Host "  Launch   : $Target\start.bat" -ForegroundColor White
Write-Host "  URL      : http://localhost:5000" -ForegroundColor White
if ($IncludeDb) {
    Write-Host "  Database : copied from source" -ForegroundColor Yellow
} else {
    Write-Host "  Database : preserved at target  (tip: use -IncludeDb to push your local DB)" -ForegroundColor DarkGray
}
Write-Host "========================================" -ForegroundColor Green
