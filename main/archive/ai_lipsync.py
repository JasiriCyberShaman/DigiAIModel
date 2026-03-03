import json
import asyncio

class AILipSyncController:
    def __init__(self, lerp_factor=0.6): 
        self.current_weights = {
            "target_A": 0.0, "target_E": 0.0, "target_I": 0.0, 
            "target_O": 0.0, "target_U": 0.0, "target_BASE": 1.0
        }
        self.lerp_factor = lerp_factor

    def get_smoothed_weights(self, target_phone_weights):
        for key in self.current_weights:
            target = float(target_phone_weights.get(key, 0.0))
            self.current_weights[key] += (target - self.current_weights[key]) * self.lerp_factor
            
            if abs(self.current_weights[key] - target) < 0.015:
                self.current_weights[key] = target
                
        return self.current_weights

PHONEME_MAP = {
    "A": ["a", "ae", "ah", "ax", "ay"],
    "E": ["e", "ey", "eh", "el"],
    "I": ["i", "iy", "ih"],
    "O": ["o", "ow", "oy", "ao"],
    "U": ["u", "uw", "uh", "w"],
    "BASE": ["p", "b", "m", "f", "v", "sil", "sp"]
}

def get_viseme_weights(current_phone):
    BASE_GAIN = 1.3
    BOOST_GAIN = 1.6 
    
    weights = {
        "target_A": 0.0, "target_E": 0.0, "target_I": 0.0, 
        "target_O": 0.0, "target_U": 0.0, "target_BASE": 0.0
    }
    
    is_vowel = False
    clean_phone = current_phone.lower()
    
    for target, phones in PHONEME_MAP.items():
        if clean_phone in phones:
            if target != "BASE":
                gain = BOOST_GAIN if target in ["O", "U"] else BASE_GAIN
                weights[f"target_{target}"] = 1.0 * gain
                is_vowel = True
            break
            
    if not is_vowel:
        weights["target_BASE"] = 1.0
        
    return weights

# 🛠️ UPDATED: Now accepts an active 'websocket' instead of 'uri'
async def broadcast_visemes(websocket, phone_stream, duration_per_phone=0.14):
    """
    Broadcasts visemes using the existing connection provided by joint_sync.
    """
    controller = AILipSyncController(lerp_factor=0.6)
    
    # We no longer need SSL context or websockets.connect here
    # because the 'websocket' passed in is already connected.
    
    for phone in phone_stream:
        frames_to_hold = int(duration_per_phone / 0.016)
        
        for _ in range(frames_to_hold):
            raw_goal = get_viseme_weights(phone)
            smoothed_data = controller.get_smoothed_weights(raw_goal)
            
            payload = {
                "type": "SET_VISEMES",
                "visemes": {
                    "A": smoothed_data["target_A"],
                    "E": smoothed_data["target_E"],
                    "I": smoothed_data["target_I"],
                    "O": smoothed_data["target_O"],
                    "U": smoothed_data["target_U"],
                    "BASE": smoothed_data["target_BASE"]
                },
                "rate": 0.08 
            }
            
            await websocket.send(json.dumps(payload))
            await asyncio.sleep(0.016)