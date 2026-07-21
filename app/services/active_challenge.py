import random
from typing import List

CHALLENGE_POOL = [
    "blink", "smile", "turn_left", "turn_right", 
    "look_up", "look_down", "open_mouth", "raise_eyebrows"
]

def generate_challenges(count: int = 3) -> List[str]:
    """Generates a random sequence of challenges."""
    # random.sample ensures unique challenges without repetition
    return random.sample(CHALLENGE_POOL, min(count, len(CHALLENGE_POOL)))

# TODO: Add gesture validation functions
