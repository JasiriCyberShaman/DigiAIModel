import asyncio
import json
import ssl
import websockets
import wave
import contextlib
import time
from archive.emotional_sync import sync_manager, mood_decay_loop, blink_loop
import archive.text_to_lipsync as tts 

# --- GLOBAL QUEUE ---
# Acts as the buffer between Jan's inference and the visual output
speech_queue = asyncio.Queue()

def get_wav_duration(file_path):
    """Calculates the exact duration of a WAV file in seconds."""
    try:
        with contextlib.closing(wave.open(file_path, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            return frames / float(rate)
    except Exception as e:
        print(f"⚠️ Warning: Could not read WAV duration: {e}")
        return 2.5 # Fallback safety duration

async def process_text_to_action(websocket, text):
    """
    Handles a single sentence: Mood -> TTS -> Precise Wait -> Framer.
    """
    if not text.strip(): return
    
    # 1. Gating: Signal that speaking has started
    sync_manager.is_speaking = True
    
    # 2. Generate Voice & Visuals
    # Saves audio to tts.TEMP_AUDIO_FILE on your local drive
    await tts.execute_tts(text)
    
    # 3. Analyze Audio Timing
    duration = get_wav_duration(tts.TEMP_AUDIO_FILE)
    
    # 4. Prepare Payload for WawaSync.tsx
    audio_b64 = tts.get_audio_base64(tts.TEMP_AUDIO_FILE)
    mood = sync_manager.get_sentiment_mood(text)

    if not audio_b64:
        print("❌ Error: Audio encoding failed.")
        sync_manager.is_speaking = False
        return

    payload = {
        "type": "SPEAK",
        "textureUrl": sync_manager.textures.get(mood, sync_manager.textures["neutral"]),
        "audioData": f"data:audio/wav;base64,{audio_b64}"
    }

    # 5. Stream to Framer via Static IP 192.168.0.31
    print(f"📤 [Digimon OS]: Streaming {duration:.2f}s Audio Buffer...")
    await websocket.send(json.dumps(payload))

    # 6. Precise Handshake
    # Wait for the audio to finish + small buffer for buffer processing
    await asyncio.sleep(duration + 0.2) 
    
    # 7. Release Gate: Allow blinking and mood decay again
    sync_manager.is_speaking = False
    sync_manager.last_interaction_time = time.time() # Reset the decay timer

async def joint_sync_worker(uri, input_queue):
    """Main WebSocket worker that coordinates visual and audio tasks."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with websockets.connect(uri, ssl=ssl_context) as ws:
            print("✅ [Dorimon Joint Sync]: Bridge Online.")
            
            # Start background autonomous loops
            asyncio.create_task(mood_decay_loop(ws, sync_manager))
            asyncio.create_task(blink_loop(ws, sync_manager)) # RESTORED

            # Listener for Framer manual signals
            async def incoming_listener():
                async for message in ws:
                    data = json.loads(message)
                    if data.get("type") == "UPDATE_STATE":
                        mood = data.get("mood")
                        if mood in sync_manager.textures:
                            sync_manager.current_mood = mood
                            sync_manager.last_interaction_time = time.time()
                            print(f"🕹️ [Framer Override]: Sync Manager locked to '{mood}'")

            asyncio.create_task(incoming_listener())

            while True:
                text = await input_queue.get()
                await process_text_to_action(ws, text)
                input_queue.task_done()
                
    except Exception as e:
        print(f"❌ Connection error in Joint Sync: {e}")