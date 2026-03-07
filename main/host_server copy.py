import http.server
import socketserver
import threading
import asyncio
from sympy import re
import re
import websockets
import ssl
import os
import json
import scipy.io.wavfile
from pocket_tts import TTSModel
from dorimon_launcher import start_jan_engine, get_ai_response

# Custom Local Modules
# Ensure these files are in the same directory or Python path
from SpeechOutput.kyutai_voice_process import generate_voice

# --- 1. GLOBAL ENGINE INITIALIZATION ---
# We load these once at boot to minimize latency during conversation
print("⚙️ [Boot]: Initializing Pocket-TTS Model...")

# Fixed Paths for the Cyber Shaman Profile
# Relying on absolute paths prevents FileNotFoundError when running from different terminals
BASE_DIR = r"C:\Users\bryan\Documents\fuck1drive\GitHub\DigiAIModel\DigiAIModel\main"
REF_VOICE_PATH = os.path.join(BASE_DIR, "SpeechSource", "refvoice.wav")
OUTPUT_PATH = os.path.join(BASE_DIR, "SpeechOutput", "output.wav")

TTS_ENGINE = TTSModel.load_model()
VOICE_STATE = TTS_ENGINE.get_state_for_audio_prompt(REF_VOICE_PATH)

# --- 2. CONFIGURATION ---
HTTPS_PORT = 8000
WS_PORT = 8765
LOCAL_IP = "192.168.0.31"
CERT_FILE = "192.168.0.31+2.pem"
KEY_FILE = "192.168.0.31+2-key.pem"

# --- 3. SECURE ASSET SERVER (HTTPS) ---
# Serves .glb models, .js libraries, and .wav audio files to Framer
import mimetypes # Add this import at the top

class SecureCORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 1. FIX THE MIME TYPE
        # This tells the browser: "If it's a .js file, treat it as code"
        if self.path.endswith(".js"):
            self.send_header('Content-Type', 'application/javascript')
        elif self.path.endswith(".glb"):
            self.send_header('Content-Type', 'model/gltf-binary')
        elif self.path.endswith(".wav"):
            self.send_header('Content-Type', 'audio/wav')
        
        # 2. CORS HEADERS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.end_headers()

def start_https_server():
    socketserver.TCPServer.allow_reuse_address = True
    server_address = ("0.0.0.0", HTTPS_PORT)
    httpd = socketserver.TCPServer(server_address, SecureCORSRequestHandler)
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f"🔒 [Assets]: https://{LOCAL_IP}:{HTTPS_PORT}")
    httpd.serve_forever()

# --- 4. SECURE SIGNAL HUB (WSS) ---
# Handles real-time communication between Python scripts and Framer
CLIENTS = set()

async def ws_handler(websocket):
    CLIENTS.add(websocket)
    print(f"[Connection]: Device linked. Total: {len(CLIENTS)}")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            
            # A. TTS GENERATION REQUEST. USED TO GENERATE DORIMON'S VOICE, testing
            # Triggered by Framer UI or LLM logic.
            if msg_type == "REQUEST_SPEECH":
                user_text = data.get("text", "...")
                print(f"[TTS]: Synthesizing -> {user_text}")
                
                success = generate_voice(user_text, TTS_ENGINE, VOICE_STATE, OUTPUT_PATH)
                
                if success:
                    # Signal Framer that the 'output.wav' is ready. 
                    # Timestamp (?t=) prevents browser caching of the old voice file.
                    response = {
                        "type": "SPEECH_READY",
                        "fileName": "output.wav",
                        "url": f"https://{LOCAL_IP}:{HTTPS_PORT}/SpeechOutput/output.wav?t={int(time.time())}"
                    }
                    await websocket.send(json.dumps(response))
            
            # B. USER CHAT INPUT for LLM RESPONSE. USE THIS ONE PRIMARILY.
            if msg_type == "USER_CHAT":
                user_text = data.get("text")
                print(f"[User]: {user_text}")

                # 1. Get AI text from the Brain
                ai_text = await get_ai_response(user_text)

                #cleans the AI text for TTS
                clean_text = re.sub(r'\*[^*]*\*', '', ai_text) # Removes *actions*
                clean_text = clean_text.replace("#", "").strip()

                ai_text = clean_text
                print(f"[Dorimon]: {ai_text}")

                # 2. Convert text to voice (using your existing pocket-tts logic)
                success = generate_voice(ai_text, TTS_ENGINE, VOICE_STATE, OUTPUT_PATH)

                if success:
                    # 3. Tell Framer to play the new audio
                    broadcast_msg = json.dumps({
                        "type": "SPEECH_READY",
                        "fileName": "output.wav",
                        "text": ai_text,
                        "url": f"https://192.168.0.31:8000/SpeechOutput/output.wav?t={int(time.time())}"
                    })
                    await asyncio.gather(*[client.send(broadcast_msg) for client in CLIENTS])

            # CENTRAL BROADCASTER
            # Forwards any other messages (Moods, Anims, Textures) to all other clients.
            # This allows external scripts (companion_cmd.py) to control the 3D model.
            else:
                target_clients = [c for c in CLIENTS if c != websocket]
                if target_clients:
                    await asyncio.gather(*[c.send(message) for c in target_clients])

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"⚠️ [Hub Error]: {e}")
    finally:
        CLIENTS.add(websocket) # Safety catch
        if websocket in CLIENTS: CLIENTS.remove(websocket)
        print(f"🔌 [Disconnect]: Device left. Total: {len(CLIENTS)}")

# --- 5. MAIN BOOT SEQUENCE ---
# At the top of host_server.py

from github_sync import get_current_ngrok_url, update_github_config

# ... inside your main() or if __name__ == "__main__": ...
async def main():
    # 1. Boot ngrok manually or via script first
    # 2. Sync the URL to GitHub
    new_url = get_current_ngrok_url()
    if new_url:
        update_github_config(new_url)
    
    # 3. Start your servers
    # ... rest of your code ...
    if not os.path.exists(CERT_FILE):
        print(f"!!! Critical Error: SSL Certificates ({CERT_FILE}) not found!")
        return

    # Start HTTPS Server in a separate thread
    threading.Thread(target=start_https_server, daemon=True).start()
    
    # Configure and Start WSS Server
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    
    async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT, ssl=ssl_context):
        print(f"[Bridge]: wss://{LOCAL_IP}:{WS_PORT}")
        await asyncio.Future() # Run forever

    jan_ready = await start_jan_engine()
    if not jan_ready:
        print(" [Warning]: Jan failed to start. Dorimon will be mute.")
    
if __name__ == "__main__":
    import time # Needed for timestamp
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Shutdown]: Powering down Digimon OS...")