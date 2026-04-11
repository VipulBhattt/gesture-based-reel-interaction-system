import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService

from config import EDGE_DRIVER_PATH, INSTAGRAM_REELS_URL, PAGE_LOAD_WAIT
from main import start_gesture_control


def setup_driver():
    """
    Initialise the Edge WebDriver.

    Priority:
      1. Explicit path from config.py / EDGE_DRIVER_PATH env var
      2. Auto-download via webdriver-manager (recommended — no manual driver needed)
    """
    options = webdriver.EdgeOptions()
    options.add_argument("--start-maximized")
    # Suppress 'Chrome is being controlled by automated software' banner
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        if EDGE_DRIVER_PATH:
            print(f"Using explicit driver path: {EDGE_DRIVER_PATH}")
            service = EdgeService(executable_path=EDGE_DRIVER_PATH)
        else:
            print("Auto-downloading Edge WebDriver via webdriver-manager...")
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            service = EdgeService(EdgeChromiumDriverManager().install())

        driver = webdriver.Edge(service=service, options=options)
        print("Edge driver initialised successfully.\n")
        return driver

    except Exception as e:
        print(f"Failed to setup Edge driver: {e}")
        return None


def open_instagram_reels(driver):
    """
    Navigate to Instagram Reels and start the gesture control loop.
    The user has PAGE_LOAD_WAIT seconds to log in manually if required.
    """
    try:
        print(f"Opening {INSTAGRAM_REELS_URL} ...")
        driver.get(INSTAGRAM_REELS_URL)

        print(f"Waiting {PAGE_LOAD_WAIT}s for page load / manual login...")
        print("Log in to Instagram in the browser window if prompted.")
        time.sleep(PAGE_LOAD_WAIT)

        # Verify we actually landed on a reels page
        if "instagram.com" not in driver.current_url:
            print("Warning: unexpected URL after navigation:", driver.current_url)

        print("Instagram Reels opened.\n")
        start_gesture_control(driver)

    except Exception as e:
        print(f"Error opening Instagram Reels: {e}")


def main():
    driver = None
    try:
        driver = setup_driver()
        if driver:
            open_instagram_reels(driver)
        else:
            print("Driver setup failed. Exiting.")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                print("Browser closed.")
            except Exception:
                pass


if __name__ == "__main__":
    main()