import os
import re
from transformers import pipeline
import torch
import soundfile as sf

# Cleans text from llm output to be TTS-friendly

def process_and_speak(llm_text):
    """
    Cleans text for TTS and generates the wav file.
    """
    # 1. TTS-Friendly Filter: Strip out asterisks, emojis, and extra punctuation
    clean_text = re.sub(r'\*[^*]*\*', '', llm_text) # Removes *actions*
    clean_text = clean_text.replace("#", "").strip()
    
    print(f"[TTS]: Generating voice for: {clean_text}")

    # 2. Run TTS (Mocking the generation here)
    # In reality: speech = tts_pipe(clean_text, forward_params={"speaker_embeddings": speaker_embeddings})
    # sf.write("SpeechAudio/test_voice.wav", speech["audio"], speech["sampling_rate"])
    
    # 3. Save to the specific path Framer is watching
    output_path = "SpeechAudio/test_voice.wav"
    
    # Simulating file save for now
    return clean_text