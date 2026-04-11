import cv2
import mediapipe as mp
import time
from collections import deque
from selenium.webdriver.common.by import By

from config import (
    POSE_HOLD_TIME, SWIPE_THRESHOLD, SCROLL_COOLDOWN,
    TOGGLE_COOLDOWN, STARTUP_GRACE_PERIOD,
    POSE_FRAME_THRESHOLD, SWIPE_STABILITY_THRESHOLD
)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)


# ──────────────────────────────────────────────
# Gesture detection helpers
# ──────────────────────────────────────────────

def fingers_up(hand_landmarks, hand_label):
    """Return list of 5 booleans (thumb → pinky) indicating extended fingers."""
    lm = hand_landmarks.landmark
    fingers = []

    if hand_label == "Right":
        fingers.append(1 if lm[4].x < lm[3].x else 0)
    else:
        fingers.append(1 if lm[4].x > lm[3].x else 0)

    tip_ids = [8, 12, 16, 20]
    pip_ids = [6, 10, 14, 18]
    for tip, pip in zip(tip_ids, pip_ids):
        fingers.append(1 if lm[tip].y < lm[pip].y else 0)

    return fingers


def detect_pose(fingers):
    """
    Map finger state to a named pose.

    [thumb, index, middle, ring, pinky]
    [1,1,1,1,1] → open hand       → PAUSE/PLAY
    [0,0,0,0,0] → closed fist     → MUTE/UNMUTE
    [1,0,0,0,0] → thumbs up       → LIKE
    [0,1,1,1,1] → thumbs down     → DISLIKE (all fingers up except thumb)
    """
    if fingers == [1, 1, 1, 1, 1]:
        return "PAUSE/PLAY"
    elif fingers == [0, 0, 0, 0, 0]:
        return "MUTE/UNMUTE"
    elif fingers == [1, 0, 0, 0, 0]:
        return "LIKE"
    elif fingers == [0, 1, 1, 1, 1]:
        return "DISLIKE"
    return "NONE"


def detect_swipe(index_history):
    """Detect vertical swipe from index-finger position history."""
    if len(index_history) < index_history.maxlen:
        return "NONE"

    start_y = sum(p[1] for p in list(index_history)[:3]) / 3
    end_y   = sum(p[1] for p in list(index_history)[-3:]) / 3
    dy      = end_y - start_y

    if dy < -SWIPE_THRESHOLD:
        return "SCROLL UP"
    elif dy > SWIPE_THRESHOLD:
        return "SCROLL DOWN"
    return "NONE"


# ──────────────────────────────────────────────
# Browser actions
# ──────────────────────────────────────────────

_VISIBLE_VIDEO_JS = """
    const videos = Array.from(document.querySelectorAll('video'));
    return videos.find(v => {
        const r = v.getBoundingClientRect();
        return r.top >= 0 && r.bottom <= window.innerHeight + 50;
    }) || videos[0] || null;
"""


def _scroll_reels(driver, direction):
    try:
        height = driver.execute_script("return window.innerHeight;")
        scroll_amount = -height if direction == "UP" else height
        driver.execute_script(
            "window.scrollBy({top: arguments[0], behavior: 'smooth'});",
            scroll_amount
        )
        arrow = "↑" if direction == "UP" else "↓"
        print(f"{arrow} Scrolled {direction}")
        time.sleep(0.8)
    except Exception as e:
        print(f"Scroll {direction} failed: {e}")


def _toggle_pause_play(driver):
    try:
        result = driver.execute_script(f"""
            const v = (function() {{ {_VISIBLE_VIDEO_JS} }})();
            if (!v) return 'no-video';
            if (v.paused) {{ v.play(); return 'playing'; }}
            else          {{ v.pause(); return 'paused'; }}
        """)
        labels = {
            'playing':  '▶ Playing',
            'paused':   '⏸ Paused',
            'no-video': '✗ No video found'
        }
        print(f"⏯ {labels.get(result, result)}")
    except Exception as e:
        print(f"⏯ PAUSE/PLAY failed: {e}")


def _toggle_mute(driver):
    try:
        result = driver.execute_script(f"""
            const v = (function() {{ {_VISIBLE_VIDEO_JS} }})();
            if (!v) return 'no-video';
            v.muted = !v.muted;
            return v.muted ? 'muted' : 'unmuted';
        """)
        labels = {
            'muted':    '🔇 Muted',
            'unmuted':  '🔊 Unmuted',
            'no-video': '✗ No video found'
        }
        print(f"🔇 {labels.get(result, result)}")
    except Exception as e:
        print(f"🔇 MUTE failed: {e}")


def _click_heart_button(driver, aria_label):
    """
    Generic function to click the like/unlike button.

    Both Like and Unlike confirmed to use div[role="button"] as
    the clickable parent (verified via DevTools).
    Picks the button closest to viewport centre = current reel.

    aria_label: 'Like' or 'Unlike'
    """
    try:
        result = driver.execute_script("""
            const label = arguments[0];
            const svgs  = Array.from(document.querySelectorAll(
                "svg[aria-label='" + label + "']"
            ));
            if (!svgs.length) return 'no-svg';

            const midY = window.innerHeight / 2;
            let best = null, bestDist = Infinity;

            for (const svg of svgs) {
                const btn = svg.closest('div[role="button"]');
                if (!btn) continue;

                const r = btn.getBoundingClientRect();
                if (r.bottom < 0 || r.top > window.innerHeight) continue;

                const dist = Math.abs((r.top + r.bottom) / 2 - midY);
                if (dist < bestDist) {
                    bestDist = dist;
                    best = btn;
                }
            }

            if (!best) return 'no-button';

            best.scrollIntoView({block: 'center'});

            ['mouseover', 'mouseenter', 'mousedown', 'mouseup', 'click'].forEach(type => {
                best.dispatchEvent(new MouseEvent(type, {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
            });

            return 'ok';
        """, aria_label)

        return result

    except Exception as e:
        print(f"Heart button click exception: {e}")
        return 'exception'


def _like_reel(driver):
    """Like the current reel (thumbs up gesture)."""
    result = _click_heart_button(driver, 'Like')
    if result == 'ok':
        print("❤ LIKED")
    elif result == 'no-svg':
        # Reel might already be liked — check for Unlike SVG
        check = driver.execute_script(
            "return document.querySelectorAll(\"svg[aria-label='Unlike']\").length;"
        )
        if check > 0:
            print("❤ Already liked (heart is already red)")
        else:
            print("❤ LIKE failed: Like button not found in DOM")
    else:
        print(f"❤ LIKE failed: {result}")


def _dislike_reel(driver):
    """
    Remove like from the current reel (thumbs down gesture).
    Only works if the reel is already liked (Unlike SVG present).
    """
    result = _click_heart_button(driver, 'Unlike')
    if result == 'ok':
        print("💔 UNLIKED")
    elif result == 'no-svg':
        # Reel is not liked yet
        check = driver.execute_script(
            "return document.querySelectorAll(\"svg[aria-label='Like']\").length;"
        )
        if check > 0:
            print("💔 Not liked yet — nothing to unlike")
        else:
            print("💔 DISLIKE failed: Neither Like nor Unlike button found")
    else:
        print(f"💔 DISLIKE failed: {result}")


def perform_action(driver, action):
    """Route a gesture action to the correct browser interaction."""
    try:
        driver.switch_to.window(driver.current_window_handle)
        driver.execute_script("window.focus();")
        time.sleep(0.1)

        if action == "SCROLL UP":
            _scroll_reels(driver, "UP")
        elif action == "SCROLL DOWN":
            _scroll_reels(driver, "DOWN")
        elif action == "PAUSE/PLAY":
            _toggle_pause_play(driver)
        elif action == "MUTE/UNMUTE":
            _toggle_mute(driver)
        elif action == "LIKE":
            _like_reel(driver)
        elif action == "DISLIKE":
            _dislike_reel(driver)

        time.sleep(0.2)

    except Exception as e:
        print(f"perform_action error for '{action}': {e}")


# ──────────────────────────────────────────────
# Main gesture control loop
# ──────────────────────────────────────────────

def start_gesture_control(driver):
    """
    Capture webcam frames, detect hand gestures via MediaPipe,
    and send corresponding actions to the Instagram Reels page.
    Press 'q' in the camera window to exit.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    try:
        driver.switch_to.window(driver.current_window_handle)
        driver.execute_script("window.focus();")
        time.sleep(0.5)
        print("Browser window focused.")
    except Exception as e:
        print(f"Could not focus browser: {e}")

    index_history     = deque(maxlen=10)
    current_pose      = None
    current_swipe     = None
    pose_frame_count  = 0
    swipe_frame_count = 0
    pose_start_time   = 0
    last_scroll_time  = 0
    last_toggle_time  = 0
    startup_time      = time.time()

    print("\n=== GESTURE CONTROL STARTED ===")
    print("  Swipe Up / Down  →  Scroll reels")
    print("  Open Hand        →  Pause / Play")
    print("  Closed Fist      →  Mute / Unmute")
    print("  Thumbs Up        →  Like ❤")
    print("  Thumbs Down      →  Unlike 💔 (only if already liked)")
    print("Press 'q' in the camera window to quit.\n")

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame   = cv2.flip(frame, 1)
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        gesture_text = "No hand detected"
        current_time  = time.time()

        if current_time - startup_time < STARTUP_GRACE_PERIOD:
            gesture_text = "Stabilizing..."

        elif results.multi_hand_landmarks and results.multi_handedness:
            hand_landmarks = results.multi_hand_landmarks[0]
            hand_label     = results.multi_handedness[0].classification[0].label

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            fingers    = fingers_up(hand_landmarks, hand_label)
            pose_name  = detect_pose(fingers)

            index_tip = hand_landmarks.landmark[8]
            index_history.append((index_tip.x, index_tip.y))
            swipe_name = detect_swipe(index_history)

            # ── Swipe (higher priority than pose) ─────────────────
            if swipe_name != "NONE":
                if current_swipe != swipe_name:
                    current_swipe     = swipe_name
                    swipe_frame_count = 1
                else:
                    swipe_frame_count += 1

                if (swipe_frame_count >= SWIPE_STABILITY_THRESHOLD
                        and current_time - last_scroll_time >= SCROLL_COOLDOWN):
                    gesture_text      = swipe_name
                    perform_action(driver, swipe_name)
                    last_scroll_time  = current_time
                    current_pose      = None
                    pose_start_time   = 0
                    pose_frame_count  = 0
                    current_swipe     = None
                    swipe_frame_count = 0
                    index_history.clear()
                else:
                    gesture_text = f"Detecting {swipe_name}..."

            # ── Pose ───────────────────────────────────────────────
            elif pose_name != "NONE":
                if current_pose != pose_name:
                    current_pose      = pose_name
                    pose_start_time   = current_time
                    pose_frame_count  = 1
                    gesture_text      = f"Detecting {pose_name}..."
                else:
                    pose_frame_count += 1
                    elapsed = current_time - pose_start_time

                    if (pose_frame_count >= POSE_FRAME_THRESHOLD
                            and elapsed >= POSE_HOLD_TIME
                            and current_time - last_toggle_time >= TOGGLE_COOLDOWN):
                        gesture_text      = pose_name
                        perform_action(driver, pose_name)
                        last_toggle_time  = current_time
                        current_pose      = None
                        pose_frame_count  = 0
                        pose_start_time   = 0
                    else:
                        gesture_text = f"Detecting {pose_name}..."

            # ── No gesture ─────────────────────────────────────────
            else:
                current_pose      = None
                pose_frame_count  = 0
                pose_start_time   = 0
                current_swipe     = None
                swipe_frame_count = 0
                gesture_text      = "No gesture"

            cv2.putText(frame, f"Hand: {hand_label}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, f"Fingers: {fingers}", (10, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

        else:
            current_pose    = None
            pose_start_time = 0
            index_history.clear()

        cv2.putText(frame, f"Gesture: {gesture_text}", (10, 115),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        cv2.imshow("Gesture Control  —  press 'q' to exit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n=== GESTURE CONTROL STOPPED ===")