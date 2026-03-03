from pocket_tts import TTSModel
import scipy.io.wavfile
import os
import re

def generate_tts_audio(llm_output, tts_model):
    
    # voice_state = tts_model.get_state_for_audio_prompt(
    #     "alba"  # One of the pre-made voices, see above
    #     # You can also use any voice file you have locally or from Hugging Face:
    #     # "./some_audio.wav"
    #     # or "hf://kyutai/tts-voices/expresso/ex01-ex02_default_001_channel2_198s.wav"
    # )

    # 1. TTS-Friendly Filter: Strip out asterisks, emojis, and extra punctuation
    clean_text = re.sub(r'\*[^*]*\*', '', llm_output) # Removes *actions*
    clean_text = clean_text.replace("#", "").strip()

    output_dir = r"C:\Users\bryan\Documents\fuck1drive\GitHub\DigiAIModel\DigiAIModel\main\SpeechAudio"
    output_filename = "output.wav"
    full_output_path = os.path.join(output_dir, output_filename)

    # Ensure the directory actually exists before writing
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created missing directory: {output_dir}")
    
    print(f"Initializing Pocket-TTS Model...")
    #tts_model = TTSModel.load_model() #this error means nothing. MAKE SURE TO LOAD ONCE AND PASS IN.
    
    #reference voice file to clone. This one uses an edited version of my own voice.
    ref_voice = r"C:\Users\bryan\Documents\fuck1drive\GitHub\DigiAIModel\DigiAIModel\main\SpeechSource\refvoice.wav"

    voice_state = tts_model.get_state_for_audio_prompt(
        ref_voice #uses reference voice file to clone. Requires HuggingFace login and acceptance of terms and conditions.
        #no voice stealing here! ;)
    )
    # 1. RUN TTS GENERATION
    print(f"🔊 Generating Audio: '{clean_text}'")
    audio = tts_model.generate_audio(voice_state, clean_text)
   
    # Audio is a 1D torch tensor containing PCM data.
    # 2. WRITE TO THE DEFINED LOCATION
    scipy.io.wavfile.write(full_output_path, tts_model.sample_rate, audio.numpy())

# --- 2. THE GENERATION FUNCTION ---
def generate_voice(text, TTS_ENGINE, VOICE_STATE, OUTPUT_PATH):
    """Generates audio using the pre-loaded global model and state. Requires text input, TTS engine, voice state, and output path."""
    print(f"🔊 [TTS]: Generating voice for -> {text}")
    try:
        audio = TTS_ENGINE.generate_audio(VOICE_STATE, text)
        scipy.io.wavfile.write(OUTPUT_PATH, TTS_ENGINE.sample_rate, audio.numpy())
        return True
    except Exception as e:
        print(f"❌ [TTS Error]: {e}")
        return False
    
if __name__ == "__main__":
    generate_tts_audio("Hello world, this is a test. Hey Bryant, what it do my weaboo!?", TTSModel.load_model())
    print("!!! Generated output.wav using Pocket TTS")
# Note: You may need to install the pocket_tts package and its dependencies.

