import pyttsx3
import os
import re
import base64

# --- CONFIGURATION ---
TEMP_AUDIO_FILE = "dorimon_buffer.wav"

async def execute_tts(text: str, speaking_rate: int = 170):
    """Generates the WAV file silently."""
    # Clean text: remove *actions* and non-ASCII (emojis)
    speech_text = re.sub(r'\*.*?\*', '', text) 
    speech_text = speech_text.encode('ascii', 'ignore').decode('ascii')

    try:
        # Initializing for every call ensures the SAPI5 engine 
        # doesn't hang across multiple sentences
        engine = pyttsx3.init()
        engine.setProperty('rate', speaking_rate)
        engine.save_to_file(speech_text, TEMP_AUDIO_FILE)
        engine.runAndWait()
        # Explicitly delete the engine instance to release the file handle
        del engine 
    except Exception as e:
        print(f"❌ TTS Generation Failed: {e}")

def get_audio_base64(file_path):
    """Encodes the WAV file to Base64 for WebSocket transmission."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ Base64 Encoding Error: {e}")
    return None

def cleanup_audio():
    """Removes the temporary buffer file on shutdown."""
    if os.path.exists(TEMP_AUDIO_FILE):
        try:
            os.remove(TEMP_AUDIO_FILE)
            print(f"🧹 Cleaned up {TEMP_AUDIO_FILE}")
        except PermissionError:
            print(f"⚠️ Could not clean {TEMP_AUDIO_FILE} (File currently in use)")
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")