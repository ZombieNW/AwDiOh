import random
from typing import TYPE_CHECKING, Tuple
from utils.lerp import LerpValue, LerpPosition

if TYPE_CHECKING:
    from utils import Config

class AnimationState:
    def __init__(self, config: 'Config'):
        self.config = config

        # Mouth
        self.current_mouth = "closed"
        self.target_mouth = "closed"

        # Mouth Shape Lerp
        if config.animation.mouth.lerp_enabled:
            self.mouth_open_amount = LerpValue(0.0, config.animation.mouth.lerp_speed)
        else:
            self.mouth_open_amount = None
        
        # Eyes - Blinking
        self.blinking = False
        self.blink_progress = 0.0
        self.blink_timer = random.uniform(
            config.animation.blink.min_interval,
            config.animation.blink.max_interval
        )

        # Eyes - Position
        if config.animation.eyes.lerp_enabled:
            self.eye_position = LerpPosition(0.0, 0.0, config.animation.eyes.lerp_speed)
        else:
            self.eye_position = None
        self._eye_target = (0.0, 0.0)

        # Eyes - Darting
        self.eye_dart_active = False
        self.eye_dart_progress = 0.0
        self.eye_dart_target = (0, 0)

        # Eyebrows w/ Lerping
        self.eyebrow_raised = False
        self.eyebrow_timer = 0.0
        if config.animation.eyebrows.lerp_enabled:
            self.eyebrow_amount = LerpValue(0.0, config.animation.eyebrows.lerp_speed)
        else:
            self.eyebrow_amount = None

        # Head Bob w/ Lerping
        if config.animation.head_bob.lerp_enabled:
            self.head_bob_offset = LerpPosition(0.0, 0.0, config.animation.head_bob.lerp_speed)
        else:
            self.head_bob_offset = None
        
        # Breathing w/ Lerping
        if config.animation.breathing.lerp_enabled:
            self.breathing_offset = LerpPosition(0.0, 0.0, config.animation.breathing.lerp_speed)
        else:
            self.breathing_offset = None
    
    # Update Mouth State
    def update_mouth(self, talking: bool, change_point: bool, energy: float, dt: float):
        if not talking:
            self.target_mouth = "closed"
        elif change_point:
            if energy < self.config.animation.mouth.small_threshold:
                self.target_mouth = "small"
            elif energy < self.config.animation.mouth.medium_threshold:
                self.target_mouth = "medium"
            else:
                self.target_mouth = "wide"
        
        # Update Mouth w/ Lerping
        if self.config.animation.mouth.lerp_enabled:
            # Lerp for Smoother Transitions
            target_amount = self._mouth_to_amount(self.target_mouth)
            self.mouth_open_amount.set_target(target_amount)
            self.mouth_open_amount.update(dt)
            
            # Determine Mouth from Lerped Value
            self.current_mouth = self._amount_to_mouth(self.mouth_open_amount.get())
        else:
            # Instant Change
            self.current_mouth = self.target_mouth
    
    # Mouth Type to Number Value
    def _mouth_to_amount(self, mouth: str) -> float:
        mapping = {"closed": 0.0, "small": 0.33, "medium": 0.66, "wide": 1.0}
        return mapping.get(mouth, 0.0)
    
    # Number Value to Mouth Type
    def _amount_to_mouth(self, amount: float) -> str:
        if amount < 0.15:
            return "closed"
        elif amount < 0.5:
            return "small"
        elif amount < 0.8:
            return "medium"
        else:
            return "wide"

    # Update Blink State
    def update_blink(self, dt: float):
        if not self.config.animation.blink.enabled:
            return
        
        self.blink_timer -= dt
        
        if self.blink_timer <= 0 and not self.blinking: # Blink if it's time
            self.blinking = True
            self.blink_progress = 0.0
        
        if self.blinking:
            self.blink_progress += dt / self.config.animation.blink.duration
            if self.blink_progress >= 1.0: # Stop blinking if it's time
                self.blinking = False
                self.blink_timer = random.uniform(
                    self.config.animation.blink.min_interval,
                    self.config.animation.blink.max_interval
                )
    
    # Update Eye Position
    def update_eye_position(self, target_x: float, target_y: float, dt: float):
        self._eye_target = (target_x, target_y)
        
        if self.eye_position and self.config.animation.eyes.lerp_enabled:
            self.eye_position.set_target(target_x, target_y)
            self.eye_position.update(dt)
    
    # Get Eye Position
    def get_eye_position(self) -> Tuple[float, float]:
        if self.eye_position and self.config.animation.eyes.lerp_enabled:
            return self.eye_position.get()
        return self._eye_target

    # Update Eye Dart
    def update_eye_dart(self, dt: float):
        if not self.config.animation.eyes.dart_enabled:
            return
        
        if not self.eye_dart_active:
            if random.random() < self.config.animation.eyes.dart_chance:
                self.eye_dart_active = True
                self.eye_dart_progress = 0.0
                self.eye_dart_target = (
                    random.randint(-self.config.animation.eyes.dart_range_x,
                                   self.config.animation.eyes.dart_range_x),
                    random.randint(-self.config.animation.eyes.dart_range_y,
                                   self.config.animation.eyes.dart_range_y)
                )
        else:
            self.eye_dart_progress += dt / self.config.animation.eyes.dart_duration
            if self.eye_dart_progress >= 1.0:
                self.eye_dart_active = False
    
    # Update Eyebrows
    def update_eyebrows(self, emphasis: bool, dt: float):
        if not self.config.animation.eyebrows.enabled:
            return
        
        if emphasis and not self.eyebrow_raised and self.config.animation.eyebrows.raise_on_emphasis:
            self.eyebrow_raised = True
            self.eyebrow_timer = self.config.animation.eyebrows.hold_duration
        
        if self.eyebrow_raised:
            self.eyebrow_timer -= dt
            if self.eyebrow_timer <= 0:
                self.eyebrow_raised = False
        
        # Update Lerp
        if self.eyebrow_amount:
            target = 1.0 if self.eyebrow_raised else 0.0
            self.eyebrow_amount.set_target(target)
            self.eyebrow_amount.update(dt)
    
    # Get eyebrow raise amount (0-1)
    def get_eyebrow_amount(self) -> float:
        if self.eyebrow_amount:
            return self.eyebrow_amount.get()
        return 1.0 if self.eyebrow_raised else 0.0

    # Update head bob offset with lerping
    def update_head_bob(self, target_x: float, target_y: float, dt: float):
        if self.head_bob_offset and self.config.animation.head_bob.lerp_enabled:
            self.head_bob_offset.set_target(target_x, target_y)
            self.head_bob_offset.update(dt)
    
    # Get head bob offset
    def get_head_bob_offset(self, calculated_offset: tuple) -> tuple:
        if self.head_bob_offset and self.config.animation.head_bob.lerp_enabled:
            return self.head_bob_offset.get()
        return calculated_offset

    # Update breathing offset with lerping
    def update_breathing(self, target_x: float, target_y: float, dt: float):
        if self.breathing_offset and self.config.animation.breathing.lerp_enabled:
            self.breathing_offset.set_target(target_x, target_y)
            self.breathing_offset.update(dt)
    
    # Get Breathing Offset
    def get_breathing_offset(self, calculated_offset: tuple) -> tuple:
        if self.breathing_offset and self.config.animation.breathing.lerp_enabled:
            return self.breathing_offset.get()
        return calculated_offset