@echo off
TITLE Digimon OS: Secure Boot
COLOR 0B

echo 🐾 [Digimon OS]: Initiating Hard Boot...

:: 1. Set the Static IP for your Bryant-Workstation
set DIGIMON_IP=192.168.0.31
echo  [Digimon OS]: Target IP locked to 192.168.0.31

:: 2. Move to the project directory
cd /d "C:\Users\bryan\Documents\fuck1drive\GitHub\DigiAIModel\DigiAIModel\main"

:: 3. Start the HTTPS Texture Server (Minimized)
echo  Starting Local HTTPS Host Server...
start /min python host_server.py

:: 4. Start Jan Nitro Engine (Hidden)
echo  Starting Jan Nitro Engine...
start "" /b "C:\Users\bryan\AppData\Local\Programs\Jan\Jan.exe" --server

:: 5. Wait exactly 30 seconds for the RTX 4060 to load the model
echo  Warming up LLM (30s timer)...
timeout /t 30 /nobreak > nul

:: 6. Launch the Python Link (This starts your terminal chat)
echo  Activating Digimon Link...
start "" python dorimon_launcher.py

:: 7. NEW: Auto-open the Framer UI
:: Replace YOUR_FRAMER_URL with your actual preview link
::echo  Opening Framer UI...
::start "" "YOUR_FRAMER_URL"

echo  System is live.
pause