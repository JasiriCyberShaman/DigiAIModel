import asyncio
import websockets
import json
import ssl

async def test_speech():
    uri = "wss://192.168.0.31:8765"
    
    # Create an SSL context that doesn't verify certificates
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print("🚀 [Digimon OS]: Connected! Sending Test Lipsync Packet...")
            
            # This packet mimics a real AI response with timed cues
            test_packet = {
                "type": "SPEAK",
                "audioData": "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAA==", 
                "cues": [
                    {"start": 0.0, "end": 1.0, "viseme": "viseme_sil"},
                    {"start": 1.0, "end": 2.0, "viseme": "viseme_AA"}, # "O"
                    {"start": 2.0, "end": 3.0, "viseme": "viseme_PP"}, # "P"
                    {"start": 3.0, "end": 4.0, "viseme": "viseme_E"},  # "E"
                    {"start": 4.0, "end": 5.0, "viseme": "viseme_nn"}, # "N"
                    {"start": 5.0, "end": 6.0, "viseme": "viseme_sil"}
                ]
            }
            
            await websocket.send(json.dumps(test_packet))
            print("✅ [Digimon OS]: Packet Delivered. Watch the model's mouth!")
            
    except Exception as e:
        print(f"❌ [Error]: Could not connect to the server. Is host_server.py running? \nDetail: {e}")

if __name__ == "__main__":
    asyncio.run(test_speech())