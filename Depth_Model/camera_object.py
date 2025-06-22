from ultralytics import YOLO
import cv2

# Load your trained YOLOv8 model
model = YOLO('yolo11n.pt')

# Open default camera (index 0)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run YOLO inference on the frame (returns list of results)
    results = model(frame)

    # results[0].plot() returns an image with boxes drawn
    annotated_frame = results[0].plot()

    # Show the frame
    cv2.imshow("YOLOv8 Live Detection", annotated_frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
