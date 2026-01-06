import sys
import argparse
from pathlib import Path

from utils import load_config
from core import AnimationGenerator

def main():
    parser = argparse.ArgumentParser(
        description="Facial Animation from Audio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python main.py audio.wav
  
  # Custom config and output
  python main.py audio.wav -c my_config.yaml -o output.mp4
  
  # Override specific settings
  python main.py audio.wav --fps 30 --no-parallel
  
  # Keep frames for inspection
  python main.py audio.wav --keep-frames
        """
    )

    # Required arguments
    parser.add_argument(
        'audio_file',
        help='Input audio file (WAV, MP3, etc.)'
    )
    
    # Configuration
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Configuration file (default: config.yaml)'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output',
        help='Output video file (overrides config)'
    )
    parser.add_argument(
        '--fps',
        type=int,
        help='Frames per second (overrides config)'
    )
    
    # Asset options
    parser.add_argument(
        '-a', '--assets',
        help='Assets directory (overrides config)'
    )
    
    # Performance options
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='Disable parallel processing'
    )
    parser.add_argument(
        '--workers',
        type=int,
        help='Number of worker processes'
    )
    
    # Debug options
    parser.add_argument(
        '--keep-frames',
        action='store_true',
        help='Keep temporary frame files'
    )
    parser.add_argument(
        '--frames-dir',
        help='Temporary frames directory'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bars'
    )
    
    # Animation toggles
    parser.add_argument(
        '--no-head-bob',
        action='store_true',
        help='Disable head bobbing'
    )
    parser.add_argument(
        '--no-breathing',
        action='store_true',
        help='Disable breathing animation'
    )
    parser.add_argument(
        '--no-eye-dart',
        action='store_true',
        help='Disable eye dart movements'
    )
    parser.add_argument(
        '--no-blink',
        action='store_true',
        help='Disable blinking'
    )
    parser.add_argument(
        '--no-lerp',
        action='store_true',
        help='Disable all lerping (instant transitions)'
    )
    
    args = parser.parse_args()

    # Check if audio file exists
    if not Path(args.audio_file).exists():
        print(f"ERROR: Audio file not found: {args.audio_file}")
        sys.exit(1)
    
    # Build overrides dictionary
    overrides = {}
    
    if args.output:
        overrides['output.video_file'] = args.output
    if args.fps:
        overrides['output.fps'] = args.fps
    if args.assets:
        overrides['assets.directory'] = args.assets
    if args.no_parallel:
        overrides['performance.parallel'] = False
    if args.workers:
        overrides['performance.num_workers'] = args.workers
    if args.keep_frames:
        overrides['debug.keep_frames'] = True
        overrides['performance.cleanup_frames'] = False
    if args.frames_dir:
        overrides['performance.frames_directory'] = args.frames_dir
    if args.verbose:
        overrides['debug.verbose'] = True
    if args.no_progress:
        overrides['debug.show_progress'] = False
    
    # Animation toggles
    if args.no_head_bob:
        overrides['animation.head_bob.enabled'] = False
    if args.no_breathing:
        overrides['animation.breathing.enabled'] = False
    if args.no_eye_dart:
        overrides['animation.eyes.dart_enabled'] = False
    if args.no_blink:
        overrides['animation.blink.enabled'] = False
    if args.no_lerp:
        overrides['animation.mouth.lerp_enabled'] = False
        overrides['animation.head_bob.lerp_enabled'] = False
        overrides['animation.breathing.lerp_enabled'] = False
        overrides['animation.eyes.lerp_enabled'] = False
        overrides['animation.eyebrows.lerp_enabled'] = False
    
    # Load configuration
    try:
        config = load_config(args.config, args.audio_file, **overrides)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    # Generate animation
    try:
        print(f"Generating animation from: {args.audio_file}")
        print(f"Configuration: {args.config}")
        
        generator = AnimationGenerator(config)
        generator.generate()
        
        print("\n✓ Animation complete!")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()