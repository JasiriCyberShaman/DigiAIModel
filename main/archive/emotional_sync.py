import json
import asyncio
import random
import time
import websockets
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# 1. Initialize Global Resources
analyzer = SentimentIntensityAnalyzer()
connected_clients = set()  # <--- FIXED: Track active browser connections

class EmotionalSyncManager:
    def __init__(self, host_ip="192.168.0.31"):
        self.is_speaking = False  
        self.host_ip = host_ip
        self.base_url = f"https://{self.host_ip}:8000/Dorimon"
        self.current_mood = "neutral" 
        self.last_interaction_time = time.time()
        self.override_until = 0 
        
        self.textures = {            
            "angry": f"{self.base_url}/Angry466.jpg",
            "blink": f"{self.base_url}/Closed466.jpg",
            "cringe": f"{self.base_url}/Cringe466.jpg",
            "happy": f"{self.base_url}/Happy466.jpg",
            "joy": f"{self.base_url}/Joy466.jpg",
            "neutral": f"{self.base_url}/Neutral466.jpg",
            "peaceful": f"{self.base_url}/Peaceful466.jpg",
            "sad": f"{self.base_url}/Sad466.jpg",
            "surprised": f"{self.base_url}/Wide466.jpg"
        }

    @property
    def override_active(self):
        return time.time() < self.override_until

    def trigger_override(self, mood, duration=10):
        self.current_mood = mood
        self.override_until = time.time() + duration
        self.last_interaction_time = time.time()

    def set_mood(self, mood):
        if not self.override_active:
            self.current_mood = mood
            self.last_interaction_time = time.time()

    def get_sentiment_mood(self, text):
        if self.override_active: 
        #     return self.current_mood 

         scores = analyzer.polarity_scores(text)
         compound = scores['compound']
        # text_lower = text.lower()

        if compound >= 0.75: new_mood = "joy"
        # elif any(w in text_lower for w in ["wow", "really", "shock"]): new_mood = "surprised"
        # elif 0.25 <= compound < 0.75: new_mood = "happy"
        # elif compound <= -0.65: new_mood = "angry"
        # elif any(w in text_lower for w in ["cringe", "glitch"]): new_mood = "cringe"
        # elif compound <= -0.2: new_mood = "sad"
        # else: new_mood = "neutral"

        self.set_mood(new_mood)
        return new_mood

# 2. Instantiate the Manager
# FIXED: This must be created before the functions try to use it
sync_manager = EmotionalSyncManager(host_ip="192.168.0.31")

async def blink_loop(websocket, sync_manager):
    while True:
        await asyncio.sleep(random.uniform(2.5, 5.5))
        if not sync_manager.is_speaking:
            # BLINK START
            await websocket.send(json.dumps({"type": "SET_TEXTURE", "url": sync_manager.textures["blink"]}))
            await asyncio.sleep(0.12)
            
            # BLINK END - Check what we are sending!
            print(f"DEBUG: Blink ending. Current mood is: {sync_manager.current_mood}")
            await websocket.send(json.dumps({
                "type": "SET_TEXTURE", 
                "url": sync_manager.textures[sync_manager.current_mood]
            }))


        # ... rest of code

async def mood_decay_loop(websocket, sync_manager):
    while True:
        await asyncio.sleep(5)
        if sync_manager.override_active:
            continue
            
        elapsed = time.time() - sync_manager.last_interaction_time
        if elapsed > 30 and sync_manager.current_mood not in ["neutral", "peaceful"]:
            target = "neutral" if sync_manager.current_mood in ["joy", "happy", "surprised"] else "neutral"
            sync_manager.set_mood(target)
            if not sync_manager.is_speaking:
                await websocket.send(json.dumps({
                    "type": "SET_TEXTURE", 
                    "url": sync_manager.textures[target]
                }))

async def handle_message(websocket, message, sync_manager):
    data = json.loads(message)
    msg_type = data.get("type")
    print(f"DEBUG: Received message type: {msg_type} with data: {data}") # ADD THIS

    if msg_type == "UPDATE_STATE":
        new_mood = data.get("mood")
        sync_manager.trigger_override(new_mood, duration=10)
        print(f"--- [Digimon OS] Manual Override: {new_mood} (Locked for 10s) ---")
        
        await websocket.send(json.dumps({
            "type": "SET_TEXTURE",
            "url": sync_manager.textures.get(new_mood, sync_manager.textures["neutral"])
        }))

    elif msg_type == "CHAT_MESSAGE":
        text = data.get("text", "")
        sync_manager.get_sentiment_mood(text)

async def server_loop(websocket):
    connected_clients.add(websocket)
    print(f"--- [Digimon OS] Client Connected: {websocket.remote_address} ---")
    try:
        async for message in websocket:
            await handle_message(websocket, message, sync_manager)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        print("--- [Digimon OS] Client Disconnected ---")

async def start_background_tasks(sync_manager):
    """
    Since we only have one active 3D model,
    we only need to run the loops for the first connected client.
    """
    while True:
        if connected_clients:
            # Pass the first available connection to the loops
            target_socket = list(connected_clients)[0]
            await asyncio.gather(
                blink_loop(target_socket, sync_manager),
                mood_decay_loop(target_socket, sync_manager)
            )
        else:
            await asyncio.sleep(1) # Wait for a client to connect

async def main():
    print("--- [Digimon OS] Secure Bridge: wss://192.168.0.31:8765 ---")
    async with websockets.serve(server_loop, "0.0.0.0", 8765):
        await start_background_tasks(sync_manager)

if __name__ == "__main__":
    asyncio.run(main())