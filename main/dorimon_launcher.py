import httpx
import os
import subprocess
import asyncio

# --- CONFIGURATION ---
JAN_PATH = r"C:\Users\bryan\AppData\Local\Programs\Jan\Jan.exe" # Path to Jan Nitro executable. move to config later
JAN_API_URL = "http://127.0.0.1:1337/v1/chat/completions" #local Jan Nitro API endpoint. move to config later
MODEL_ID = r"mistralai\Ministral-3-3B-Instruct-2512-Q4_K_M" #move to config later
JAN_HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer digimon-local"}

# Global chat history for persistent personality
chat_history = [
    {"role": "system", "content": "You are Dorimon, a helpful, witty AI virtual pet. A digimon. Keep responses brief and friendly."}
]

async def start_jan_engine():
    """Initializes the Jan Nitro Engine if it's not already running."""
    if not os.path.exists(JAN_PATH):
        print(f"XXX [Launcher]: Jan not found at {JAN_PATH}")
        return False

    print("[Launcher]: Warming up Jan Nitro Engine...")
    subprocess.Popen([JAN_PATH, "--server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    async with httpx.AsyncClient() as client:
        for _ in range(30): # 30 second timeout
            try:
                res = await client.get("http://127.0.0.1:1337/v1/models", timeout=1.0)
                if res.status_code == 200:
                    print("!!![Launcher]: Jan API Online.")
                    return True
            except:
                await asyncio.sleep(1)
    return False

async def get_ai_response(user_input):
    """Fetches text from the local Mistral model."""
    chat_history.append({"role": "user", "content": user_input})
    
    payload = {
        "model": MODEL_ID,
        "messages": chat_history,
        "temperature": 0.7
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(JAN_API_URL, json=payload, headers=JAN_HEADERS)
            data = response.json()
            ai_message = data['choices'][0]['message']['content']
            
            chat_history.append({"role": "assistant", "content": ai_message})
            return ai_message
        except Exception as e:
            return f"Brain Error: {e}"