import pygame
import pygame._sdl2.audio as sdl2_audio

pygame.mixer.init()

# The correct way to get names in modern Pygame _sdl2
# False = Playback devices, True = Capture devices
names = sdl2_audio.get_audio_device_names(False)

print("--- Playback Devices Found ---")
for i, name in enumerate(names):
    print(f"Index {i}: {name}")

pygame.mixer.quit()