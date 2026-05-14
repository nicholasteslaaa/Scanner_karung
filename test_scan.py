import cv2
import ai_system

cap = cv2.VideoCapture("http://localhost:8000/cam_feed")
model = ai_system.raspi_samping()

while True:
    ret, frame = cap.read()
    
    if not ret:
        break
    
    result = model.scan_samping(frame)
    frame = result["frame"]
    
    cv2.imshow("scan",frame)
    
    key = cv2.waitKey(1) & 0XFF
    
    if (key == ord("q")):
        break

cap.release()
cv2.destroyAllWindows()