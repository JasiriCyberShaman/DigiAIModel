import asyncio
import websockets
import json
import os

# --- 1. HARDWARE CONFIGURATION ---
HUB_IP = "192.168.0.31"
HUB_URI = f"wss://{HUB_IP}:8765"
# Base URL for assets served via HTTPS by host_server.py
ASSET_BASE_URL = f"https://{HUB_IP}:8000"

async def _fire_signal(payload):
    """Internal pulse: Opens a quick connection, sends a command, and closes."""
    try:
        # We disable SSL verification because we are using local self-signed certs
        async with websockets.connect(HUB_URI, ssl=None) as ws:
            await ws.send(json.dumps(payload))
    except Exception as e:
        print(f"⚠️ [Signal Hub Error]: Connection to {HUB_IP} failed. Is host_server.py running? \n({e})")

# --- 2. THE MOOD DECK (Texture Swapping) ---

def set_mood(mood_name):
    """
    Sets the face texture based on the filename in your Textures folder.
    Example: set_mood("happy") looks for /Textures/happy.png
    """
    payload = {
        "type": "SET_TEXTURE",
        "url": f"{ASSET_BASE_URL}/Textures/{mood_name}.png"
    }
    asyncio.run(_fire_signal(payload))
    print(f"🎭 [Mood]: Changed to {mood_name}")

def happy(): set_mood("happy")
def sad(): set_mood("sad")
def thinking(): set_mood("thinking")
def glitch(): set_mood("glitch")
def neutral(): set_mood("neutral")

# --- 3. THE ACTUATOR DECK (Animations) ---

def set_animation(anim_name, fade_rate=0.5):
    """
    Triggers a 3D animation stored in your .glb model.
    Common names: 'Wave', 'Blink', 'Idle.001', 'Dance'
    """
    payload = {
        "type": "SET_ANIMATION",
        "animation": anim_name,
        "rate": fade_rate
    }
    asyncio.run(_fire_signal(payload))
    print(f"[Anim]: Triggered {anim_name}")

def wave(): set_animation("Wave")
def idle(): set_animation("Idle.001")

# --- 4. THE SPEECH DECK (Manual TTS Override) ---

def speak(text):
    """
    Forces the character to say a specific line without going through Jan/LLM.
    Useful for system alerts or debugging.
    """
    payload = {
        "type": "REQUEST_SPEECH",
        "text": text
    }
    asyncio.run(_fire_signal(payload))
    print(f" [Manual TTS]: Character is synthesizing: '{text}'")

# --- 5. THE GLOBAL RESET ---

def system_reset():
    """Returns Dorimon to base state: Neutral texture + Idle animation."""
    neutral()
    idle()
    print(" [System]: Dorimon reset to Home state.")

# --- TEST BLOCK ---
if __name__ == "__main__":
    # Test sequence to verify the bridge is working
    print(" Running Companion Command Test...")
    wave()
    happy()
    print(" Signal test complete.")