from pathlib import Path
from PIL import Image
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from utils import Config

class AssetManager:
    def __init__(self, config: 'Config'):
        self.config = config
        self.asset_dir = Path(config.assets.directory)
        self._load_assets()
    
    # Load Imager from Asset Directory
    def _load_img(self, name: str) -> Image.Image:
        path = self.asset_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Asset {name} not found in {self.asset_dir}")
        return Image.open(path).convert("RGBA")

    # Load all Assets
    def _load_assets(self):
        # Base Layers
        self.base = self._load_img(self.config.assets.base)
        self.eyes_open = self._load_img(self.config.assets.eyes_open)
        self.eyes_closed = self._load_img(self.config.assets.eyes_closed)

        # Mouth Shapes
        self.mouths: Dict[str, Image.Image] = {}
        for name, filename in self.config.assets.mouths.items():
            self.mouths[name] = self._load_img(filename)

        # Optional Eyebrows
        try:
            self.eyebrows_normal = self._load_img(self.config.assets.eyebrows['normal'])
            self.eyebrows_raised = self._load_img(self.config.assets.eyebrows['raised'])
            self.has_eyebrows = True
        except (FileNotFoundError, KeyError):
            self.has_eyebrows = False
    
    # Get Mouth by Type
    def get_mouth(self, mouth_type: str) -> Image.Image:
        return self.mouths.get(mouth_type, self.mouths['closed'])
    
    # Get Eyes Image
    def get_eyes(self, closed: bool) -> Image.Image:
        return self.eyes_closed if closed else self.eyes_open

    # Get Eyebrows Image
    def get_eyebrows(self, raised: bool) -> Image.Image:
        if not self.has_eyebrows:
            return None
        return self.eyebrows_raised if raised else self.eyebrows_normal