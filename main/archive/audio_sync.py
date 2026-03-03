import pyaudio
import numpy as np
import json
import asyncio
import websockets

class AudioLipsyncManager:
    def __init__(self):
        # Audio Stream Parameters
        self.CHUNK = 512       # Small buffer for low latency
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.p = pyaudio.PyAudio()
        
        # Sensitivity Calibration
        self.min_rms = 300     # Noise floor
        self.max_rms = 5000    # Volume threshold for 100% mouth opening
        
        # The Gate: controlled by text_to_lipsync.py
        self.is_active = False 

    # --- INDENTED INSIDE THE CLASS ---
    def find_vb_cable_index(self):
        """Automatically finds the 'CABLE Output' index."""
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            name = str(dev.get('name', ''))
            if "CABLE Output" in name:
                return i
        return None

    def get_viseme_weights(self, data):
        """Analyzes FFT data to estimate vowel shapes (A, E, I, O, U)."""
        audio_data = np.frombuffer(data, dtype=np.int16)
        rms = np.sqrt(np.mean(audio_data.astype(float)**2))
        
        if rms < self.min_rms:
            return None 

        vol_scaler = min((rms - self.min_rms) / (self.max_rms - self.min_rms), 1.0)
        fft_data = np.abs(np.fft.rfft(audio_data))
        freqs = np.fft.rfftfreq(len(audio_data), 1.0/self.RATE)

        # FFT Frequency Mapping
        o_energy = np.sum(fft_data[(freqs > 100) & (freqs < 600)])
        a_energy = np.sum(fft_data[(freqs > 600) & (freqs < 1600)])
        i_energy = np.sum(fft_data[(freqs > 1600) & (freqs < 4000)])

        total = o_energy + a_energy + i_energy + 1e-6
        
        w_o = (o_energy / total) * vol_scaler
        w_a = (a_energy / total) * vol_scaler
        w_i = (i_energy / total) * vol_scaler

        return {
            "A": w_a * 1.5,
            "E": w_a * 0.5,
            "I": w_i,
            "O": w_o * 1.2,
            "U": w_o,
            "BASE": 1.0 - vol_scaler
        }

    async def start_listening(self, websocket):
        """Captures audio from the VB-Cable and sends weights to Framer."""
        # Now this will correctly find the method within the class
        dev_index = self.find_vb_cable_index()
        
        try:
            stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=dev_index,
                frames_per_buffer=self.CHUNK
            )
        except Exception as e:
            print(f"❌ Could not open audio stream: {e}")
            return

        print("🎙️ Audio Sync: VRChat-style listener is live.")
        
        try:
            while True:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                
                if self.is_active:
                    visemes = self.get_viseme_weights(data)
                    if visemes:
                        payload = {
                            "type": "SET_VISEMES",
                            "visemes": visemes,
                            "rate": 0.05
                        }
                        await websocket.send(json.dumps(payload))
                else:
                    await websocket.send(json.dumps({
                        "type": "SET_VISEMES",
                        "visemes": {"A":0,"E":0,"I":0,"O":0,"U":0,"BASE":1},
                        "rate": 0.2
                    }))
                
                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"❌ Audio Sync Error: {e}")
        finally:
            stream.stop_stream()
            stream.close()

# Export instance
audio_sync = AudioLipsyncManager()