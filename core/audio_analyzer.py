import librosa
import numpy as np
from scipy.ndimage import gaussian_filter1d
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils import Config

class AudioAnalyzer:
    def __init__(self, audio_file: str, config: 'Config'):
        self.audio_file = audio_file
        self.config = config
        self.fps = config.output.fps

        # Load Audio
        self.audio, self.sample_rate = librosa.load(audio_file, sr=None)
        self.hop_length = int(self.sample_rate / self.fps)

        # Analyze Audio
        self._analyze()
    
    def _analyze(self):
        # Loudness/Energy (Root Mean Square)
        self.rms = librosa.feature.rms(y=self.audio, hop_length=self.hop_length)[0]
        self.rms = self.rms / np.max(self.rms) if np.max(self.rms) > 0 else self.rms

        # Pitch (fundamental frequency)
        self.f0 = librosa.yin(
            self.audio,
            fmin=self.config.audio.pitch_min,
            fmax=self.config.audio.pitch_max,
            sr=self.sample_rate,
            hop_length=self.hop_length
        )
        self.f0 = np.nan_to_num(self.f0) # NaN to 0
        self.f0 = gaussian_filter1d(self.f0, sigma=self.config.audio.pitch_smoothing) # Smoothing

        # Rates of Chance
        self.energy_delta = np.diff(self.rms, prepend=self.rms[0])
        self.pitch_delta = np.abs(np.diff(self.f0, prepend=self.f0[0]))

        # Detect Speech Segments
        self.speech_segments = self._detect_speech_segments()

        # Detect Emphasis Points
        self.emphasis_points = self._detect_emphasis()

        # Frame Count
        self.frames = len(self.rms)
        self.duration = self.frames / self.fps
    
    # Detect Speech Segments
    def _detect_speech_segments(self) -> np.ndarray:
        return self.rms > (np.mean(self.rms) * 0.5)

    # Detect Emphasis Points
    def _detect_emphasis(self) -> np.ndarray:
        pitch_threshold = np.percentile(
            self.pitch_delta, 
            self.config.audio.emphasis_pitch_threshold
        )
        energy_threshold = np.percentile(
            self.energy_delta,
            self.config.audio.emphasis_energy_threshold
        )
        
        emphasis = (
            (self.pitch_delta > pitch_threshold) |
            (self.energy_delta > energy_threshold)
        )
        return emphasis

    # Check for Talking at Frame
    def is_talking(self, frame_idx: int) -> bool:
        return self.rms[frame_idx] > self.config.audio.talk_threshold

    # Check for Mouth Change at Frame
    def is_change_point(self, frame_idx: int) -> bool:
        pitch_threshold = np.percentile(self.pitch_delta, 90)
        return (
            self.energy_delta[frame_idx] > self.config.audio.mouth_change_energy or
            self.pitch_delta[frame_idx] > pitch_threshold
        )

    # Get Normalized Energy at Frame
    def get_energy(self, frame_idx: int) -> float:
        return self.rms[frame_idx]

    # Check Emphasis at Frame
    def has_emphasis(self, frame_idx: int) -> bool:
        return self.emphasis_points[frame_idx]