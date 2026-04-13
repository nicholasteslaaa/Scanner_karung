from fastapi import FastAPI
import cv2
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import signal
import sys
import time

# model = AI_counter("yolo11n.pt")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cap = None
current_frame = None
info = None
frame_lock = threading.Lock() 

@app.on_event("startup")
def startup_event():
    global cap
    cap = cv2.VideoCapture("Person Walking 1.mp4")

    t = threading.Thread(target=thread_function, daemon=True)
    t.start()

def thread_function():
    global current_frame,info
    while cap.isOpened():
        ret, frame = cap.read()
        frame = cv2.flip(frame,1)
        
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
            # break
        
        # result = model.detect(frame)

        with frame_lock:
            # current_frame = result["frame"]
            # info = result
            
            current_frame = frame
            info = {"info":0}
            
            
            # try:
            #     # Point to the other port
            #     response = requests.get("http://localhost:8000/get_info") # or 8001
            #     print(f"Response: {response.json()}")
            # except Exception as e:
            #     print(f"Error connecting: {e}")
            
        # time.sleep(0.5) 

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


@app.get("/cam_feed")
async def cam_feed():
    return StreamingResponse(generateFrame(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/get_info")
async def get_info():
    global info
    return info


def signal_handler():
    cap.release()
    sys.exit(0)

# Register the custom handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTSTP, signal_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    