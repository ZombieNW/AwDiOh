import math
from PIL import Image
from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from utils import Config
    from core.asset_manager import AssetManager
    from core.animation_state import AnimationState

class FrameRenderer:
    def __init__(self, assets: 'AssetManager', config: 'Config'):
        self.assets = assets
        self.config = config
    
    # Render a single frame
    def render_frame(
        self,
        state: 'AnimationState',
        time: float,
        talking: bool,
        dt: float
    ) -> Image.Image:
        frame = self.assets.base.copy()
        
        # Head Bob
        head_offset_calc = self._calculate_head_bob(time, talking)
        state.update_head_bob(head_offset_calc[0], head_offset_calc[1], dt)
        head_offset = state.get_head_bob_offset(head_offset_calc)
        
        # Breathing
        breathing_offset_calc = self._calculate_breathing(time, talking)
        state.update_breathing(breathing_offset_calc[0], breathing_offset_calc[1], dt)
        breathing_offset = state.get_breathing_offset(breathing_offset_calc)
        
        # Combine Offsets
        base_x = int(head_offset[0] + breathing_offset[0])
        base_y = int(head_offset[1] + breathing_offset[1])
        
        # Eye Position
        eye_calc = self._calculate_eye_position(time, state)
        state.update_eye_position(eye_calc[0], eye_calc[1], dt)
        eye_pos = state.get_eye_position()
        
        eye_x = int(eye_pos[0]) + base_x
        eye_y = int(eye_pos[1]) + base_y
        
        # Paste Eyes
        eye_img = self.assets.get_eyes(state.blinking)
        frame.paste(eye_img, (eye_x, eye_y), eye_img)
        
        # Paste Eyebrows
        eyebrow_img = self.assets.get_eyebrows(state.eyebrow_raised)
        if eyebrow_img is not None:
            frame.paste(eyebrow_img, (base_x, base_y), eyebrow_img)
        
        # Paste Mouth
        mouth_img = self.assets.get_mouth(state.current_mouth)
        frame.paste(mouth_img, (base_x, base_y), mouth_img)
        
        return frame
    
    # Head Bob Offset
    def _calculate_head_bob(self, time: float, talking: bool) -> Tuple[float, float]:
        if not self.config.animation.head_bob.enabled:
            return (0.0, 0.0)
        
        if self.config.animation.head_bob.only_when_talking and not talking:
            return (0.0, 0.0)
        
        # Oscillate vertically when talking
        y = math.sin(time * math.pi * 2 * self.config.animation.head_bob.speed)
        y *= self.config.animation.head_bob.amount
        
        return (0.0, y)
    
    # Breathing Offset
    def _calculate_breathing(self, time: float, talking: bool) -> Tuple[float, float]:
        if not self.config.animation.breathing.enabled:
            return (0.0, 0.0)
        
        # Gentle breathing - reduced when talking
        scale = self.config.animation.breathing.talking_scale if talking else 1.0
        y = math.sin(time * math.pi * 2 * self.config.animation.breathing.speed)
        y *= self.config.animation.breathing.amount * scale
        
        return (0.0, y)
    
    # Final Eye Position
    def _calculate_eye_position(self, time: float, state: 'AnimationState') -> Tuple[float, float]:
        # Base drift
        if self.config.animation.eyes.drift_enabled:
            base_x = math.sin(time * self.config.animation.eyes.drift_speed) * \
                     self.config.animation.eyes.drift_amount_x
            base_y = math.cos(time * self.config.animation.eyes.drift_speed) * \
                     self.config.animation.eyes.drift_amount_y
        else:
            base_x = 0.0
            base_y = 0.0
        
        # Add eye dart
        if state.eye_dart_active:
            progress = state.eye_dart_progress
            # Ease in-out
            ease = progress * (2 - progress)
            base_x += state.eye_dart_target[0] * ease
            base_y += state.eye_dart_target[1] * ease
        
        return (base_x, base_y)