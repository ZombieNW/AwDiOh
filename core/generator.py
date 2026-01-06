import subprocess
import shutil
from pathlib import Path
from typing import Dict
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

from utils import Config
from core.audio_analyzer import AudioAnalyzer
from core.asset_manager import AssetManager
from core.animation_state import AnimationState
from renderers.frame_renderer import FrameRenderer

class AnimationGenerator:
    def __init__(self, config: Config):
        self.config = config
        self.analyzer = AudioAnalyzer(config.audio_file, config)
        self.assets = AssetManager(config)
        self.renderer = FrameRenderer(self.assets, config)
    
    def generate(self):
        output_path = Path(self.config.performance.frames_directory)
        output_path.mkdir(exist_ok=True)

        if self.config.debug.verbose:
            print(f"Audio: {self.config.audio_file}")
            print(f"Duration: {self.analyzer.duration:.2f}s")
            print(f"Frames: {self.analyzer.frames} at {self.config.output.fps} FPS")
        
        # Generate Frames
        if self.config.performance.parallel and self.analyzer.frames > 100:
            self._generate_parallel()
        else:
            self._generate_sequential()
        
        if self.config.debug.verbose:
            print(f"Frames saved to {self.config.performance.frames_directory}")

        # Compile Video
        self._compile_video()

        # Cleanup
        if self.config.performance.cleanup_frames and not self.config.debug.keep_frames:
            if self.config.debug.verbose:
                print("Cleaning Temp Frames...")
            shutil.rmtree(self.config.performance.frames_directory)
            if self.config.debug.verbose:
                print("Cleanup Complete")
    
    def _generate_sequential(self):
        state = AnimationState(self.config)
        dt = 1.0 / self.config.output.fps

        iterator = range(self.analyzer.frames)
        if self.config.debug.show_progress:
            iterator = tqdm(iterator, desc="Generating frames")
        
        for i in iterator:
            self._generate_frame(i, state, dt)
    
    def _generate_parallel(self):
        num_workers = self.config.performance.num_workers or max(1, cpu_count() - 1)

        if self.config.debug.verbose:
            print(f"Parallel Processing w/ {num_workers} Workers...")
        
        # Pre-compute all state transitions
        frame_data = self._precompute_states()

        # Render in parallel
        with Pool(num_workers) as pool:
            iterator = pool.imap(self._render_frame_data, frame_data)

            if self.config.debug.show_progress:
                iterator = tqdm(iterator, total=len(frame_data), desc="Rendering frames")
            
            list(iterator)

    # Pre-compute all animation state transitions
    def _precompute_states(self) -> list:
        state = AnimationState(self.config)
        dt = 1.0 / self.config.output.fps
        frame_data = []

        for i in range(self.analyzer.frames):
            time = i / self.config.output.fps

            # Get audio features
            talking = self.analyzer.is_talking(i)
            change_point = self.analyzer.is_change_point(i)
            energy = self.analyzer.get_energy(i)
            emphasis = self.analyzer.has_emphasis(i)

            # Update state
            state.update_mouth(talking, change_point, energy, dt)
            state.update_blink(dt)
            state.update_eye_dart(dt)
            state.update_eyebrows(emphasis, dt)

            # Store frame data
            frame_data.append({
                'frame_idx': i,
                'time': time,
                'dt': dt,
                'talking': talking,
                'mouth': state.current_mouth,
                'blinking': state.blinking,
                'eyebrow_raised': state.eyebrow_raised,
                'eye_dart_active': state.eye_dart_active,
                'eye_dart_progress': state.eye_dart_progress,
                'eye_dart_target': state.eye_dart_target,
            })
        
        return frame_data
    
    # Render frame from pre-computed animation frame data
    def _render_frame_data(self, data: Dict):
        # Reconstruct Minimal State
        state = AnimationState(self.config)
        state.current_mouth = data['mouth']
        state.blinking = data['blinking']
        state.eyebrow_raised = data['eyebrow_raised']
        state.eye_dart_active = data['eye_dart_active']
        state.eye_dart_progress = data['eye_dart_progress']
        state.eye_dart_target = data['eye_dart_target']

        # Render frame
        frame = self.renderer.render_frame(
            state,
            data['time'],
            data['talking'],
            data['dt']
        )

        # Save frame
        output_path = Path(self.config.performance.frames_directory) / f"frame_{data['frame_idx']:04d}.png"
        frame.save(output_path)
    
    # Generate a single frame
    def _generate_frame(self, frame_idx: int, state: AnimationState, dt: float):
        time = frame_idx / self.config.output.fps

        # Get audio features
        talking = self.analyzer.is_talking(frame_idx)
        change_point = self.analyzer.is_change_point(frame_idx)
        energy = self.analyzer.get_energy(frame_idx)
        emphasis = self.analyzer.has_emphasis(frame_idx)

        # Update animation state
        state.update_mouth(talking, change_point, energy, dt)
        state.update_blink(dt)
        state.update_eye_dart(dt)
        state.update_eyebrows(emphasis, dt)

        # Render frame
        frame = self.renderer.render_frame(state, time, talking, dt)
        
        # Save frame
        output_path = Path(self.config.performance.frames_directory) / \
                     f"frame_{frame_idx:04d}.png"
        frame.save(output_path)
    
    # Compile Video
    def _compile_video(self):
        if self.config.debug.verbose:
            print("Compiling Video...")
        
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'],
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: FFmpeg not found. Please install FFmpeg.")
            print(f"Frames saved to: {self.config.performance.frames_directory}")
            return
        
        # Build ffmpeg command
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-framerate', str(self.config.output.fps),
            '-i', f'{self.config.performance.frames_directory}/frame_%04d.png',
            '-i', self.config.audio_file,
            '-c:v', self.config.output.video_codec,
            '-preset', self.config.output.video_preset,
            '-b:v', self.config.output.video_bitrate,
            '-c:a', 'aac',
            '-b:a', self.config.output.audio_bitrate,
            '-pix_fmt', 'yuv420p',
            '-shortest',  # Match shortest stream
            self.config.output.video_file
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
            print(f"✓ Video saved to: {self.config.output.video_file}")
        except subprocess.CalledProcessError as e:
            print("ERROR: FFmpeg failed")
            if self.config.debug.verbose:
                print(e.stderr.decode())
            print(f"Frames saved to: {self.config.performance.frames_directory}")