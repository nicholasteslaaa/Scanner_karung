import threading
import cv2
from ultralytics import YOLO

model = YOLO("yolo11n.pt")

cap = cv2.VideoCapture(0)
current_frame = None
# A Lock ensures thread safety when reading/writing the global frame
frame_lock = threading.Lock() 

def thread_function():
    global current_frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Process and store the frame safely
        with frame_lock:
            current_frame = cv2.flip(frame, 1)

if __name__ == "__main__":
    # Start the capture thread
    t = threading.Thread(target=thread_function, daemon=True)
    t.start()

    # GUI MUST remain in the main thread
    while True:
        with frame_lock:
            if current_frame is not None:
                cv2.imshow("Webcam Feed", model(current_frame)[0].plot())

        # waitKey(1) handles window events; it won't work correctly in a child thread
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
