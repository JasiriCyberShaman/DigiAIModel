import http.server
import socketserver
import threading
import asyncio
import re
import websockets
import ssl
import os
import json
import time
from pocket_tts import TTSModel
from dorimon_launcher import start_jan_engine, get_ai_response
from SpeechOutput.kyutai_voice_process import generate_voice

# --- 1. CONFIGURATION ---
# Replace this with your actual ngrok URL once you start it
# Example: "https://cyber-shaman.ngrok-free.app"
NGROK_URL =  "https://9da5-2600-8805-9390-2600-8515-ee8b-ea10-987c.ngrok-free.app"

PORT = 8000
BASE_DIR = r"C:\Users\bryan\Documents\fuck1drive\GitHub\DigiAIModel\DigiAIModel\main"
OUTPUT_PATH = os.path.join(BASE_DIR, "SpeechOutput", "output.wav")
REF_VOICE_PATH = os.path.join(BASE_DIR, "SpeechSource", "refvoice.wav")

# SSL files (Ngrok handles SSL for the public, but your local server 
# still needs these to talk to the tunnel securely if you use 'ngrok http')
CERT_FILE = "192.168.0.31+2.pem"
KEY_FILE = "192.168.0.31+2-key.pem"

# --- 2. INITIALIZATION ---
TTS_ENGINE = TTSModel.load_model()
VOICE_STATE = TTS_ENGINE.get_state_for_audio_prompt(REF_VOICE_PATH)
CLIENTS = set()

# --- 3. SECURE ASSET SERVER (HTTPS) ---
class SecureCORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.endswith(".js"): self.send_header('Content-Type', 'application/javascript')
        elif self.path.endswith(".glb"): self.send_header('Content-Type', 'model/gltf-binary')
        elif self.path.endswith(".wav"): self.send_header('Content-Type', 'audio/wav')
        
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        super().end_headers()

def start_https_server():
    server_address = ("0.0.0.0", PORT)
    httpd = socketserver.TCPServer(server_address, SecureCORSRequestHandler)
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f"🔒 [Assets/HTTPS]: Listening on port {PORT}")
    httpd.serve_forever()

# --- 4. SECURE SIGNAL HUB (WSS) ---
async def ws_handler(websocket):
    CLIENTS.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "USER_CHAT":
                user_text = data.get("text")
                ai_text = await get_ai_response(user_text)
                
                # Clean text for TTS
                clean_text = re.sub(r'\*[^*]*\*', '', ai_text).replace("#", "").strip()
                
                if generate_voice(clean_text, TTS_ENGINE, VOICE_STATE, OUTPUT_PATH):
                    broadcast_msg = json.dumps({
                        "type": "SPEECH_READY",
                        "text": ai_text, # Original text with actions for animations
                        "url": f"{NGROK_URL}/SpeechOutput/output.wav?t={int(time.time())}"
                    })
                    await asyncio.gather(*[client.send(broadcast_msg) for client in CLIENTS])
    except Exception as e:
        print(f"⚠️ [Hub Error]: {e}")
    finally:
        CLIENTS.remove(websocket)

# --- 5. MAIN BOOT SEQUENCE ---
async def main():
    # Start Asset Server in background thread
    threading.Thread(target=start_https_server, daemon=True).start()
    
    # Start WebSocket Server on a different port internally (e.g., 8765)
    # But Ngrok will only point to the HTTP port (8000). 
    # WAIT: To use one ngrok tunnel for both, we need to use an 
    # Integration library or point ngrok to the websocket port.
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    
    async with websockets.serve(ws_handler, "0.0.0.0", 8765, ssl=ssl_context):
        print(f"🚀 [Cyber Shaman Online]")
        print(f"1. Run: ngrok http 8000 (For Assets)")
        print(f"2. Run: ngrok tcp 8765 (For Websockets)")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())