import subprocess
import json
import os
import asyncio

# --- CONFIGURATION ---
RHUBARB_PATH = r"C:\Users\bryan\Documents\fuck1drive\Rhubarb-Lip-Sync-1.14.0-Windows\rhubarb.exe" 

async def get_visemes_from_wav(wav_path):
    """Runs the Rhubarb model on the wav file and returns timed visemes."""
    if not os.path.exists(wav_path):
        print(f"❌ Error: {wav_path} not found.")
        return []

    # Command to run Rhubarb and get JSON output via stdout
    cmd = [
        RHUBARB_PATH,
        "-f", "json",
        wav_path
    ]
    
    try:
        # Run Rhubarb in the background
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"❌ Rhubarb Error: {stderr.decode()}")
            return []

        # Parse the JSON results from the stdout pipe
        data = json.loads(stdout.decode())
        return data['mouthCues'] # This is a list of {start, end, value}
        
    except Exception as e:
        print(f"❌ Failed to run Rhubarb: {e}")
        return []

# Rhubarb uses A-X shapes. We map them to your Framer A, E, I, O, U shapes.
RHUBARB_MAP = {
    "A": "BASE", # Closed mouth
    "B": "I",    # Slightly open
    "C": "E",    # Open
    "D": "A",    # Wide open
    "E": "O",    # Rounded
    "F": "U",    # Pursed
    "G": "I",    # Slit/Neutral
    "H": "A",    # Wide open (exaggerated)
    "X": "BASE"  # Silence/Neutral
}