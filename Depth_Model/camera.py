import cv2
import time
import os

# Configuration
IMAGE_PATH = "data/camera.jpg"  # Will be overwritten every 3 second
INTERVAL = 3  # Seconds between captures

# Open webcam (0 = default webcam)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Cannot open webcam.")
    exit()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Save the current frame
        cv2.imwrite(IMAGE_PATH, frame)
        print(f"Saved frame to {IMAGE_PATH}")

        # Wait before capturing the next frame
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    cap.release()
    cv2.destroyAllWindows()
