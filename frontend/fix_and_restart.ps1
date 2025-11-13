# Script to fix and restart the frontend
Write-Host "🔧 Starting fix process..." -ForegroundColor Cyan

# Step 1: Kill any existing node processes
Write-Host "`n1️⃣ Stopping existing processes..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Step 2: Clear Vite cache
Write-Host "`n2️⃣ Clearing Vite cache..." -ForegroundColor Yellow
if (Test-Path "node_modules\.vite") {
    Remove-Item -Recurse -Force "node_modules\.vite"
    Write-Host "✅ Vite cache cleared" -ForegroundColor Green
}

# Step 3: Start dev server
Write-Host "`n3️⃣ Starting dev server..." -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🚀 Frontend will start on http://localhost:3000" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host "`n📝 Important: After the server starts:" -ForegroundColor Yellow
Write-Host "   1. Open browser in Incognito/Private mode" -ForegroundColor White
Write-Host "   2. Or press Ctrl+Shift+R for hard refresh" -ForegroundColor White
Write-Host "   3. Or clear browser cache completely" -ForegroundColor White
Write-Host "`n🔍 Open Console (F12) to see debug logs`n" -ForegroundColor Magenta

npm run dev
