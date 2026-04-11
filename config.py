
# config.py  —  centralised settings for gesture reel controller
# Edit values here; no need to touch main.py or open_instagram.py


import os

# ── WebDriver ────────────────────────────────────────────────
# Leave as None to auto-download via webdriver-manager (recommended).
# Set to an explicit path only if you must use a local driver binary.
EDGE_DRIVER_PATH = r"E:\Study\Gesture Based Reel Scroller\edgedriver_win64\msedgedriver.exe"

# ── Gesture timing ───────────────────────────────────────────
# Seconds a pose must be held before it fires
POSE_HOLD_TIME = 0.5

# Minimum normalised-coordinate delta to count as a swipe (0–1 scale)
SWIPE_THRESHOLD = 0.18

# Minimum seconds between consecutive scroll actions
SCROLL_COOLDOWN = 0.8

# Minimum seconds between consecutive toggle actions (pause, mute, like)
TOGGLE_COOLDOWN = 1.0

# Seconds after launch before gestures are accepted (camera stabilisation)
STARTUP_GRACE_PERIOD = 3.0

# ── Frame thresholds ─────────────────────────────────────────
# Number of consecutive frames a pose must appear before it is accepted
POSE_FRAME_THRESHOLD = 3

# Number of consecutive frames a swipe direction must appear before firing
SWIPE_STABILITY_THRESHOLD = 2

# ── Instagram ─────────────────────────────────────────────────
INSTAGRAM_REELS_URL = "https://www.instagram.com/reels/"

# Increased to 25s — automated browser loads slower than normal
# and Instagram may show a login wall on first launch
PAGE_LOAD_WAIT = 25