import asyncio
import websockets
import json
import ssl

async def trigger_test():
    # Use your static workstation IP
    uri = "wss://192.168.0.31:8765"
    
    # We bypass SSL verification for this local diagnostic script 
    # to avoid needing the certs in this specific client.
    ssl_context = ssl._create_unverified_context()
    
    try:
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            # This triggers the 'TRIGGER_TEST_SPEECH' block in host_server.py
            payload = {"type": "TRIGGER_TEST_SPEECH"}
            await websocket.send(json.dumps(payload))
            print("🚀 [Diagnostic]: Speech Trigger Pulse Sent to host_server.py!")
            
    except Exception as e:
        print(f"❌ [Connection Failed]: {e}. Is host_server.py running?")

if __name__ == "__main__":
    asyncio.run(trigger_test())