#!/usr/bin/env pwsh
# Complete clean restart script

Write-Host "`n🔧 Starting complete cleanup and restart...`n" -ForegroundColor Cyan

# Step 1: Kill all node processes
Write-Host "1️⃣ Stopping all Node processes..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "✅ All Node processes stopped`n" -ForegroundColor Green

# Step 2: Clean Vite cache
Write-Host "2️⃣ Cleaning Vite cache..." -ForegroundColor Yellow
if (Test-Path "node_modules\.vite") {
    Remove-Item -Recurse -Force "node_modules\.vite"
    Write-Host "✅ Vite cache cleared" -ForegroundColor Green
} else {
    Write-Host "ℹ️ No Vite cache found" -ForegroundColor Gray
}

# Step 3: Clean dist
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "✅ Dist folder cleared" -ForegroundColor Green
}

Write-Host "`n3️⃣ Starting dev server...`n" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🚀 Server will start on: " -NoNewline -ForegroundColor Green
Write-Host "http://localhost:3000" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

Write-Host "📝 IMPORTANT STEPS AFTER SERVER STARTS:`n" -ForegroundColor Magenta
Write-Host "  ✅ 1. Close ALL browser tabs with localhost:3000" -ForegroundColor White
Write-Host "  ✅ 2. Open NEW Incognito/Private window (Ctrl+Shift+N)" -ForegroundColor White
Write-Host "  ✅ 3. Go to: http://localhost:3000" -ForegroundColor White
Write-Host "  ✅ 4. Press F12 and check Console for errors`n" -ForegroundColor White

Write-Host "⏳ Starting in 3 seconds...`n" -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start the dev server
npm run dev
