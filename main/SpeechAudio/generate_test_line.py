# pip install gTTS
from gtts import gTTS

text = "Hello Bryant. The mechatronics system is online. Wawa lip sync testing is now in progress."
tts = gTTS(text)
tts.save("test_voice.wav")
print("✅ Created test_voice.wav")