import base64
import json
import time

# Updated wawa_processor.py snippet
class WawaLipsyncProcessor:
    def __init__(self):
        # STANDARDIZE TO UPPERCASE to match your engine's VOWEL_MAP and visemeTargets
        self.wawa_set = [
            "viseme_sil", "viseme_PP", "viseme_FF", "viseme_TH",
            "viseme_DD", "viseme_kk", "viseme_CH", "viseme_SS",
            "viseme_nn", "viseme_RR", "viseme_AA", "viseme_E",
            "viseme_I", "viseme_O", "viseme_U", "viseme_AA"
        ]
    
    def create_speak_packet(self, audio_path, text_content):
        """
        Converts a local audio file and its timing into the 
        standardized SPEAK packet for the SocketBridge.
        """
        try:
            with open(audio_path, "rb") as f:
                audio_encoded = base64.b64encode(f.read()).decode("utf-8")
            
            cues = self._generate_mock_cues(len(text_content))

            packet = {
                "type": "SPEAK",
                "audioData": f"data:audio/wav;base64,{audio_encoded}",
                "cues": cues,
                "textureUrl": "https://192.168.0.31:8000/Dorimon/Happy466.jpg" # Optional mood swap
            }
            return packet
        except Exception as e:
            print(f"❌ [Wawa Error]: Failed to package audio: {e}")
            return None
    
    def _generate_mock_cues(self, text_length):
        """Generates timed viseme intervals based on average speech rates."""
        cues = []
        duration_per_char = 0.08 #time on each viseme
        current_time = 0.0

        for i in range(text_length):
            # Randomly pick a viseme that isn't silence for the test
            viseme = self.wawa_set[i % (len(self.wawa_set) - 1) + 1]
            end_time = current_time + duration_per_char
            cues.append({
                "start": round(current_time, 3),
                "end": round(end_time, 3),
                "viseme": viseme
            })
            current_time = end_time

        # Always end with silence
        cues.append({"start": round(current_time, 3), "end": round(current_time + 0.2, 3), "viseme": "viseme_sil"})
        return cues

# Instantiate for use in your main server
wawa_processor = WawaLipsyncProcessor()