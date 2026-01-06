import math
from typing import Tuple

# Lerp 2 Floats
def lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t

# Lerp 2 Tuples of Floats
def lerp_tuple(start: Tuple[float, float], end: Tuple[float, float], t: float) -> Tuple[float, float]:
    return (
        lerp(start[0], end[0], t),
        lerp(start[1], end[1], t)
    )

# Smoothstep Lerp 2 Floats
def smooth_lerp(start: float, end: float, t: float) -> float:
    # Smoothstep Formula: 3t² - 2t³
    t = max(0.0, min(1.0, t))  # Clamp to [0, 1]
    smooth_t = t * t * (3.0 - 2.0 * t)
    return lerp(start, end, smooth_t)

# Ease-in-Out Lerp 2 Floats
def ease_in_out(start: float, end: float, t: float) -> float:
    t = max(0.0, min(1.0, t))  # Clamp to [0, 1]
    ease_t = t * (2 - t)
    return lerp(start, end, ease_t)

# Calculate Lerp Factor based on dt and speed
def calculate_lerp_factor(dt: float, speed: float) -> float:
    return 1.0 - math.exp(-speed * dt * 60.0)

class LerpValue:
    def __init__(self, initial_value: float = 0.0, lerp_speed: float = 0.3):
        self.current = initial_value
        self.target = initial_value
        self.lerp_speed = lerp_speed
    
    def set_target(self, target: float):
        self.target = target
    
    def update(self, dt: float) -> float:
        if abs(self.current - self.target) < 0.001: # If its close enough
            self.current = self.target
        else: # Lerp that thang
            t = calculate_lerp_factor(dt, self.lerp_speed)
            self.current = lerp(self.current, self.target, t)
        
        return self.current

    def get(self) -> float:
        return self.current

    def set_immediate(self, value: float):
        self.current = value
        self.target = value

# Lerp 2D Position
class LerpPosition:
    def __init__(self, initial_x: float = 0.0, initial_y: float = 0.0, lerp_speed: float = 0.3):
        self.current_x = initial_x
        self.current_y = initial_y
        self.target_x = initial_x
        self.target_y = initial_y
        self.lerp_speed = lerp_speed
    
    def set_target(self, x: float, y: float):
        self.target_x = x
        self.target_y = y
    
    def update(self, dt: float) -> Tuple[float, float]:
        if abs(self.current_x - self.target_x) < 0.001 and abs(self.current_y - self.target_y) < 0.001: # If its close enough
            self.current_x = self.target_x
            self.current_y = self.target_y
        else: # Lerp that thang
            t = calculate_lerp_factor(dt, self.lerp_speed)
            self.current_x = lerp(self.current_x, self.target_x, t)
            self.current_y = lerp(self.current_y, self.target_y, t)
        
        return self.current_x, self.current_y

    def get(self) -> Tuple[float, float]:
        return self.current_x, self.current_y

    def set_immediate(self, x: float, y: float):
        self.current_x = x
        self.current_y = y
        self.target_x = x
        self.target_y = y