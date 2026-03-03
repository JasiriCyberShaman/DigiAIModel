import asyncio
import json
import ssl
import websockets
from archive.emotional_sync import sync_manager

async def manual_test():
    URI = "wss://192.168.0.31:8765" # Your Framer Bridge
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with websockets.connect(URI, ssl=ssl_context) as ws:
        print("🛠️ Dorimon Visual Debugger Active.")
        print("Commands: /joy, /happy, /angry, /sad, /surprised, /cringe, /peaceful, /neutral")
        
        while True:
            cmd = await asyncio.to_thread(input, "Enter Mood: ")
            mood = cmd.replace("/", "").strip().lower()

            if mood in sync_manager.textures:
                # 1. Update Texture
                await ws.send(json.dumps({
                    "type": "SET_TEXTURE", 
                    "url": sync_manager.textures[mood]
                }))
                
                # 2. Trigger Animation
                anim = "Idle.001"
                if mood == "joy": anim = "JoyFlip"
                elif mood == "angry": anim = "Roar"
                await ws.send(json.dumps({"type": "SET_ANIMATION", "animation": anim}))
                
                print(f"✅ Triggered: {mood} (Texture: {mood}, Animation: {anim})")
            else:
                print("❌ Invalid mood. Try /angry or /joy.")

if __name__ == "__main__":
    asyncio.run(manual_test())