# AwDiOh!

## _Generate basic facial animation from voiceover_

![Language](https://badgen.net/badge/language/Python/yellow) ![License](https://badgen.net/badge/language/MIT/red)

# What?
This generates a .mp4 of basic facial animation data from a .wav input. I made this tool to help automate some of my animation processes for my videos.

# How?
Install packages `pip install -r requirements.txt`

## Basic Usage
`python main.py <wav> [optional arguments]`

### Arguments

| Argument | Description |
| --- | --- |
| `<wav>` | Input audio file (WAV) |
| `-c <yaml>`, `--config <yaml>` | Path to config file |
| `-o <video>`, `--output <video>` | Output video file |
| `--fps <num>` | Frames per second |
| `-a`, `--assets` | Assets directory |
| `--no-parallel` | Disable Multithreading | 
| `--workers <num>` | Max Multithreading Workers |
| `--keep-frames` | Keep temp output frames |
| `--frames-dir` | Dir to store temp frames |
| `-v`, `--verbose` | Verbose Logging |
| `--no-progress` | Disable progressbar |
| `--no-head-bob` | Disable head bobbing |
| `--no-breathing` | Disable breathing animation |
| `--no-eye-dart` | Disable eye dart movements |
| `--no-blink` | Disable blinking |
| `--no-lerp` | Disable all interpolation (instant transitions) |