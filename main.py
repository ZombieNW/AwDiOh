import librosa
import numpy as np
import math
import random
import os
import sys
from PIL import Image
from scipy.ndimage import gaussian_filter1d

# ====================
# Config
# ====================

# Files
AUDIO_FILE = sys.argv[1]
ASSETS_DIR = 'assets'
OUTPUT_DIR = 'frames'

# Video
FPS = 24
FRAME_SIZE = (2048, 2048)

# Audio
TALK_THRESHOLD = 0.08
MOUTH_CHANGE_ENERGY = 0.05
BLINK_MIN = 3.0
BLINK_MAX = 5.0
BLINK_DURATION = 0.15

# ====================
# Load Audio
# ====================

audio, sample_rate = librosa.load(AUDIO_FILE, sr=None) # load audio, get sample rate
hop_length = int(sample_rate / FPS) # samples per frame

# loudness
rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0] # root mean square - loudness
rms = rms / np.max(rms) # normalize

# pitch
f0 = librosa.yin(audio, fmin=80, fmax=400, sr=sample_rate) # fundamental frequency
f0 = np.nan_to_num(f0) # replace nan with 0
f0 = gaussian_filter1d(f0, sigma=3) # smooth

# rates of change
energy_delta = np.diff(rms, prepend=rms[0]) # energy change
pitch_delta = np.abs(np.diff(f0, prepend=f0[0])) # pitch change

frames = len(rms)

# ====================
# Load Images
# ====================

# Helper function to load images from asset directory
def load_img(name):
    return Image.open(os.path.join(ASSETS_DIR, name)).convert("RGBA")

base = load_img("base.png")
eyes_open = load_img("eyes_open.png")
eyes_closed = load_img("eyes_closed.png")


mouth_imgs = {
    "closed": load_img("mouth_closed.png"),
    "small": load_img("mouth_small.png"),
    "medium": load_img("mouth_medium.png"),
    "wide": load_img("mouth_wide.png"),
}

# ====================
# Eye State
# ====================

blink_timer = random.uniform(BLINK_MIN, BLINK_MAX) # random time between blinks
blink_progress = 0.0
blinking = False

# ====================
# Helpers
# ====================

# Determine what mouth to use depending on energy level
def mouth_from_energy(e):
    if e < 0.25:
        return "small"
    elif e < 0.6:
        return "medium"
    else:
        return "wide"

# Determine eye offset based on time
def eye_offset(t):
    x = math.sin(t * 0.7) * 4
    y = math.cos(t * 0.7) * 3
    return (int(x), int(y))

# ====================
# Main Loop
# ====================

os.makedirs(OUTPUT_DIR, exist_ok=True)

current_mouth = "closed"

for i in range(frames):
    time = i / FPS
    
    # Mouth State
    talking = rms[i] > TALK_THRESHOLD # determine if talking
    change_point = ( # determine if mouth should change
        energy_delta[i] > MOUTH_CHANGE_ENERGY or # energy change
        pitch_delta[i] > np.percentile(pitch_delta, 90) # pitch change
    )

    # Determine mouth to use this frame
    if not talking:
        current_mouth = "closed"
    elif change_point:
        current_mouth = mouth_from_energy(rms[i])

    # Eye State
    # Blinking
    blink_timer -= 1 / FPS # count down
    if blink_timer <= 0 and not blinking: # blink if timer is up
        blinking = True
        blink_progress = 0.0
    
    if blinking:
        blink_progress += 1 / (FPS * BLINK_DURATION) # count how long we've been blinking for
        if blink_progress >= 1.0: # stop blinking if we've been blinking long enough
            blinking = False
            blink_timer = random.uniform(BLINK_MIN, BLINK_MAX)
    
    eye_img = eyes_closed if blinking else eyes_open
    eye_x, eye_y = eye_offset(time)

    # Render Frame
    frame = base.copy()
    frame.paste(eye_img, (eye_x, eye_y), eye_img)
    frame.paste(mouth_imgs[current_mouth], (0, 0), mouth_imgs[current_mouth])

    frame.save(f"{OUTPUT_DIR}/frame_{i:04d}.png")

print(f"Done! Saved {frames} frames to {OUTPUT_DIR}")