import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

@dataclass
class OutputConfig:
    video_file: str = "output.mp4"
    fps: int = 24
    frame_size: Tuple[int, int] = (2048, 2048)
    video_codec: str = "libx264"
    video_preset: str = "medium"
    video_bitrate: str = "5M"
    audio_bitrate: str = "192k"

@dataclass
class AssetConfig:
    directory: str = "assets"
    base: str = "base.png"
    eyes_open: str = "eyes_open.png"
    eyes_closed: str = "eyes_closed.png"
    mouths: Dict[str, str] = field(default_factory=lambda: {
        "closed": "mouth_closed.png",
        "small": "mouth_small.png",
        "medium": "mouth_medium.png",
        "wide": "mouth_wide.png",
    })
    eyebrows: Dict[str, str] = field(default_factory=lambda: {
        "normal": "eyebrows_normal.png",
        "raised": "eyebrows_raised.png",
    })

@dataclass
class AudioConfig:
    talk_threshold: float = 0.08
    mouth_change_energy: float = 0.05
    pitch_min: int = 80
    pitch_max: int = 400
    pitch_smoothing: int = 5
    emphasis_pitch_threshold: int = 85
    emphasis_energy_threshold: int = 85

@dataclass
class MouthAnimationConfig:
    small_threshold: float = 0.25
    medium_threshold: float = 0.6
    lerp_enabled: bool = True
    lerp_speed: float = 0.3

@dataclass
class BlinkConfig:
    enabled: bool = True
    min_interval: float = 3.0
    max_interval: float = 6.0
    duration: float = 0.15

@dataclass
class HeadBobConfig:
    enabled: bool = True
    amount: float = 8.0
    speed: float = 0.5
    only_when_talking: bool = True
    lerp_enabled: bool = True
    lerp_speed: float = 0.2

@dataclass
class BreathingConfig:
    enabled: bool = True
    amount: float = 3.0
    speed: float = 0.3
    talking_scale: float = 0.3
    lerp_enabled: bool = True
    lerp_speed: float = 0.15

@dataclass
class EyesConfig:
    drift_enabled: bool = True
    drift_speed: float = 0.7
    drift_amount_x: float = 4.0
    drift_amount_y: float = 3.0
    dart_enabled: bool = True
    dart_chance: float = 0.02
    dart_duration: float = 0.2
    dart_range_x: int = 15
    dart_range_y: int = 10
    lerp_enabled: bool = True
    lerp_speed: float = 0.25

@dataclass
class EyebrowsConfig:
    enabled: bool = True
    raise_on_emphasis: bool = True
    hold_duration: float = 0.3
    lerp_enabled: bool = True
    lerp_speed: float = 0.4

@dataclass
class AnimationConfig:
    mouth: MouthAnimationConfig = field(default_factory=MouthAnimationConfig)
    blink: BlinkConfig = field(default_factory=BlinkConfig)
    head_bob: HeadBobConfig = field(default_factory=HeadBobConfig)
    breathing: BreathingConfig = field(default_factory=BreathingConfig)
    eyes: EyesConfig = field(default_factory=EyesConfig)
    eyebrows: EyebrowsConfig = field(default_factory=EyebrowsConfig)

@dataclass
class PerformanceConfig:
    parallel: bool = True
    num_workers: Optional[int] = None
    cleanup_frames: bool = True
    frames_directory: str = "frames"

@dataclass
class DebugConfig:
    keep_frames: bool = False
    show_progress: bool = True
    verbose: bool = False

# Main Config Object
@dataclass
class Config:
    audio_file: str
    output: OutputConfig = field(default_factory=OutputConfig)
    assets: AssetConfig = field(default_factory=AssetConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    animation: AnimationConfig = field(default_factory=AnimationConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)

# Load config from yaml
def load_config(config_path: str, audio_file: str, **overrides) -> Config:
    config_path = Path(config_path)
    
    # Load YAML
    if config_path.exists():
        with open(config_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
    else:
        yaml_data = {}
    
    # Build nested config objects
    output_cfg = OutputConfig(**yaml_data.get('output', {}))
    assets_cfg = AssetConfig(**yaml_data.get('assets', {}))
    audio_cfg = AudioConfig(**yaml_data.get('audio', {}))
    
    # Animation sub-configs
    anim_data = yaml_data.get('animation', {})
    mouth_cfg = MouthAnimationConfig(**anim_data.get('mouth', {}))
    blink_cfg = BlinkConfig(**anim_data.get('blink', {}))
    head_bob_cfg = HeadBobConfig(**anim_data.get('head_bob', {}))
    breathing_cfg = BreathingConfig(**anim_data.get('breathing', {}))
    eyes_cfg = EyesConfig(**anim_data.get('eyes', {}))
    eyebrows_cfg = EyebrowsConfig(**anim_data.get('eyebrows', {}))
    
    animation_cfg = AnimationConfig(
        mouth=mouth_cfg,
        blink=blink_cfg,
        head_bob=head_bob_cfg,
        breathing=breathing_cfg,
        eyes=eyes_cfg,
        eyebrows=eyebrows_cfg
    )
    
    performance_cfg = PerformanceConfig(**yaml_data.get('performance', {}))
    debug_cfg = DebugConfig(**yaml_data.get('debug', {}))
    
    # Create main config
    config = Config(
        audio_file=audio_file,
        output=output_cfg,
        assets=assets_cfg,
        audio=audio_cfg,
        animation=animation_cfg,
        performance=performance_cfg,
        debug=debug_cfg
    )
    
    # Apply Overrides
    _apply_overrides(config, overrides)
    
    return config

# Apply CLI Overrides
def _apply_overrides(config: Config, overrides: Dict):
    for key, value in overrides.items():
        if value is None:
            continue
        
        # Handle Nested Settings (like output.fps)
        if '.' in key:
            parts = key.split('.')
            obj = config
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
        else:
            # Find Attribute in Config
            if hasattr(config, key):
                setattr(config, key, value)