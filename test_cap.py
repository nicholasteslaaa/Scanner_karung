import cv2
import os
import ai_system


tipe = ("samping","depan")
tipe_idx = 0
cap = cv2.VideoCapture(f"ujiniksap/{tipe[tipe_idx]}/v7sisa1.mp4")

counter = 0
while True:
    ret, frame = cap.read()
    
    if not ret:
        break
    
    cv2.imshow("cam",frame)
    
    key = cv2.waitKey(100) & 0XFF
    
    if (key == ord("q")):
        break
    
    if (key == ord("s")):
        cv2.imwrite(f"test_pict/{tipe[tipe_idx]}/{counter}.jpg",frame)
        counter += 1
        print("saved")
  
    print(frame)
    

# cap.release()

cv2.destroyAllWindows()