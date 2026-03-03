import os

from huggingface_hub import login


hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")

if not hf_token:
	raise ValueError("Set HUGGINGFACE_HUB_TOKEN before running this script.")

login(hf_token)
print("✅ Login successful!")