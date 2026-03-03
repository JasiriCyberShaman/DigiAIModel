from pocket_tts import TTSModel
import scipy.io.wavfile

def generate_tts_audio():
    tts_model = TTSModel.load_model() #this error means nothing. 
    # voice_state = tts_model.get_state_for_audio_prompt(
    #     "alba"  # One of the pre-made voices, see above
    #     # You can also use any voice file you have locally or from Hugging Face:
    #     # "./some_audio.wav"
    #     # or "hf://kyutai/tts-voices/expresso/ex01-ex02_default_001_channel2_198s.wav"
    # )
    voice_state = tts_model.get_state_for_audio_prompt(
        "C:\\Users\\bryan\\Documents\\fuck1drive\\GitHub\\DigiAIModel\\DigiAIModel\\main\\SpeechSource\\refvoice.wav"
        # One of the pre-made voices, see above
        # You can also use any voice file you have locally or from Hugging Face:
        
        # or "hf://kyutai/tts-voices/expresso/ex01-ex02_default_001_channel2_198s.wav"
    )
    audio = tts_model.generate_audio(voice_state, "Hello world, this is a test. Hey Bryant, what it do my weaboo!?")
    # Audio is a 1D torch tensor containing PCM data.
    scipy.io.wavfile.write("output.wav", tts_model.sample_rate, audio.numpy())

if __name__ == "__main__":
    generate_tts_audio()
    print("✅ Generated output.wav using Pocket TTS")
# Note: You may need to install the pocket_tts package and its dependencies.