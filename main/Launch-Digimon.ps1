# Digimon Project: Linear Boot Sequence
Clear-Host
Write-Host "🐾 [Digimon OS]: Initiating Hard Boot..." -ForegroundColor Cyan

# 1. Set the Static IP for your Bryant-Workstation
$env:DIGIMON_IP = "192.168.0.31"
Write-Host "📡 [Digimon OS]: Target IP locked to 192.168.0.31" -ForegroundColor Green

# 2. Force Location to your project folder
Set-Location "C:\Users\bryan\Documents\fuck1drive\GitHub\DigiAIModel\DigiAIModel\main"

# 3. Start the HTTPS Texture Server (Minimized)
Write-Host "🌐 Starting Local HTTPS Host Server..." -ForegroundColor Yellow
Start-Process python -ArgumentList "host_server.py" -WindowStyle Minimized

# 4. Start Jan Nitro Engine (Hidden)
Write-Host "🚀 Starting Jan Nitro Engine..." -ForegroundColor Yellow
Start-Process "C:\Users\bryan\AppData\Local\Programs\Jan\Jan.exe" -ArgumentList "--server" -WindowStyle Hidden

# 5. Wait exactly 30 seconds for the RTX 4060 to load the model
Write-Host "⏳ Warming up LLM (30s timer)..." -NoNewline
for ($i=1; $i -le 30; $i++) {
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 1
}

# 6. Launch the Python Link
Write-Host "`n🎙️ Activating Digimon Link..." -ForegroundColor Green
python dorimon_launcher.py

# Keep window open if python exits
Write-Host "`n👋 Press any key to close." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")