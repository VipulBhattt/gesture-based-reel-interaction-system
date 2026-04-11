"""
debug_dom.py  —  Run this BEFORE gesture control to verify that
Instagram's DOM structure matches what main.py expects.

Usage:
    python debug_dom.py

The script opens Instagram Reels, waits for you to log in,
then prints counts for every selector the main app relies on.
If any count is 0 you'll know exactly which action will fail.
"""

import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By

from config import EDGE_DRIVER_PATH, INSTAGRAM_REELS_URL, PAGE_LOAD_WAIT

SELECTORS = {
    "Articles (scroll targets)":        "article",
    "Videos":                           "video",
    "Like button (SVG aria-label)":     "svg[aria-label='Like']",
    "Like button (button aria-label)":  "button[aria-label='Like']",
    "Unlike button (already liked)":    "svg[aria-label='Unlike']",
}

JS_CHECKS = {
    "Visible video exists": """
        const videos = Array.from(document.querySelectorAll('video'));
        return videos.some(v => {
            const r = v.getBoundingClientRect();
            return r.top >= 0 && r.bottom <= window.innerHeight + 50;
        });
    """,
    "First visible video paused": """
        const videos = Array.from(document.querySelectorAll('video'));
        const v = videos.find(v => {
            const r = v.getBoundingClientRect();
            return r.top >= 0 && r.bottom <= window.innerHeight + 50;
        });
        return v ? v.paused : 'no visible video';
    """,
    "First visible video muted": """
        const videos = Array.from(document.querySelectorAll('video'));
        const v = videos.find(v => {
            const r = v.getBoundingClientRect();
            return r.top >= 0 && r.bottom <= window.innerHeight + 50;
        });
        return v ? v.muted : 'no visible video';
    """,
}


def run_debug():
    options = webdriver.EdgeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    if EDGE_DRIVER_PATH:
        service = EdgeService(executable_path=EDGE_DRIVER_PATH)
    else:
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        service = EdgeService(EdgeChromiumDriverManager().install())

    driver = webdriver.Edge(service=service, options=options)

    try:
        print(f"Opening {INSTAGRAM_REELS_URL}")
        driver.get(INSTAGRAM_REELS_URL)
        print(f"Waiting {PAGE_LOAD_WAIT}s — log in if prompted...")
        time.sleep(PAGE_LOAD_WAIT)

        print("\n" + "=" * 50)
        print("  DOM SELECTOR COUNTS")
        print("=" * 50)
        for label, css in SELECTORS.items():
            elements = driver.find_elements(By.CSS_SELECTOR, css)
            status = "✓" if elements else "✗ PROBLEM"
            print(f"  {status}  {label}: {len(elements)}")

        print("\n" + "=" * 50)
        print("  JS STATE CHECKS")
        print("=" * 50)
        for label, js in JS_CHECKS.items():
            result = driver.execute_script(js)
            print(f"  {label}: {result}")

        print("\n" + "=" * 50)
        print("Results above tell you exactly which gestures will work.")
        print("Any ✗ PROBLEM row = that gesture action will fail.")
        print("=" * 50)
        input("\nPress Enter to close the browser...")

    finally:
        driver.quit()


if __name__ == "__main__":
    run_debug()