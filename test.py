from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import threading
import uvicorn
import time
import cv2
import os
import re


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

current_frame = None
folder_path = "test_pict/samping"
frame_list = sorted(os.listdir(folder_path))
counter =  0

current_frame2 = None
folder_path2 = "test_pict/depan"
frame_list2 = sorted(os.listdir(folder_path2))
counter2 =  0


thread_lock = threading.Lock()

def natural_key(string_):
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

@app.on_event("startup")
def startup_event():
    global current_frame,current_frame2
    frame_list.sort(key=natural_key)
    filepath = os.path.join(folder_path,frame_list[counter])
    current_frame = cv2.imread(filepath)
    
    frame_list2.sort(key=natural_key)
    filepath2 = os.path.join(folder_path2,frame_list2[counter2])
    current_frame2 = cv2.imread(filepath2)
    
    t = threading.Thread(target=thread_function, daemon=True)
    t.start()

def generateFrame():
    global current_frame
    while True:
        if current_frame is not None:
            ret, buffer = cv2.imencode(".jpg", current_frame)
            frame_bytes = buffer.tobytes()

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame_bytes +
                b'\r\n'
            )

        time.sleep(0.03)

def generateFrame2():
    global current_frame2
    while True:
        if current_frame2 is not None:
            ret, buffer = cv2.imencode(".jpg", current_frame2)
            frame_bytes = buffer.tobytes()

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame_bytes +
                b'\r\n'
            )

        time.sleep(0.03)
        
def generateFrame():
    global current_frame
    while True:
        if current_frame is not None:
            ret, buffer = cv2.imencode(".jpg", current_frame)
            frame_bytes = buffer.tobytes()

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame_bytes +
                b'\r\n'
            )

        time.sleep(0.03)

def generateFrame2():
    global current_frame2
    while True:
        if current_frame2 is not None:
            ret, buffer = cv2.imencode(".jpg", current_frame2)
            frame_bytes = buffer.tobytes()

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame_bytes +
                b'\r\n'
            )

        time.sleep(0.03)


@app.get("/cam_feed")
async def cam_feed():
    return StreamingResponse(generateFrame(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/cam_feed2")
async def cam_feed2():
    return StreamingResponse(generateFrame2(), media_type="multipart/x-mixed-replace; boundary=frame")


def thread_function():
    global current_frame, current_frame2, counter, counter2
    while True:    
        with thread_lock:
            filepath = os.path.join(folder_path,frame_list[counter])
            current_frame = cv2.imread(filepath)
            
            filepath2 = os.path.join(folder_path2,frame_list2[counter2])
            current_frame2 = cv2.imread(filepath2)
            
            combined = cv2.hconcat([current_frame, current_frame2])
            cv2.imshow("cam",combined)
            
            
            key = cv2.waitKey(10) & 0XFF
            
            if (key == ord("q")):
                os._exit(1)
                
            
            if (key == ord(",")):
                counter -= 1
                counter %= len(frame_list)*-1
                    
            if (key == ord(".")):
                counter += 1
                counter %= len(frame_list)
            
            if (key == ord(";")):
                counter2 -= 1
                counter %= len(frame_list)*-1
                    
            if (key == ord("'")):
                counter2 += 1
                counter2 %= len(frame_list2)
            
            print(counter)
        
    cv2.destroyAllWindows()
    
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)