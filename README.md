# Gesture Based Reel Scroller

A Python-based application that allows you to control Instagram Reels using hand gestures captured via webcam. This project is currently under development and may have bugs or incomplete features.

## Features

- **Gesture Recognition**: Detects hand gestures using MediaPipe and OpenCV.
- **Browser Automation**: Uses Selenium to interact with Instagram Reels in a web browser.
- **Supported Gestures**:
  - Swipe Up/Down: Scroll through reels.
  - Open Hand: Pause/Play video.
  - Closed Fist: Mute/Unmute video.
  - Thumbs Up: Like the current reel.
  - Thumbs Down: Unlike the current reel (if already liked).
- **Real-time Feedback**: Displays gesture status in a camera window.

## Requirements

- Python 3.7+
- Webcam
- Microsoft Edge browser (for Selenium WebDriver)
- Internet connection for Instagram access

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/VipulBhattt/gesture-based-reel-inetraction-system.git
   cd gesture-based-reel-scroller
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. (Optional) Run the debug script to verify Instagram DOM compatibility:
   ```
   python debug_dom.py
   ```

## Usage

1. Ensure your webcam is connected and accessible.

2. Run the main application:
   ```
   python open_instagram.py
   ```

3. The browser will open Instagram Reels. Log in if prompted.

4. A camera window will appear. Perform gestures in front of the camera to control the reels.

5. Press 'q' in the camera window to exit.

## Configuration

Edit `config.py` to customize settings such as gesture thresholds, timing, and WebDriver path.

## Development

This project is under active development. Contributions are welcome! Please:

- Report bugs via GitHub Issues.
- Submit pull requests for improvements.
- Test on different systems and browsers.

### Project Structure

- `main.py`: Core gesture detection and browser action logic.
- `open_instagram.py`: WebDriver setup and Instagram navigation.
- `config.py`: Configuration settings.
- `debug_dom.py`: DOM verification script.
- `requirements.txt`: Python dependencies.


## Disclaimer

This project is for educational purposes. Use responsibly and in accordance with Instagram's terms of service. The developers are not responsible for any misuse.