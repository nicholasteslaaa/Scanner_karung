from fastapi import FastAPI, Form, Response
import cv2
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
# from AI_system import AI_counter
import ai_system
from queue import Queue

detection_queue = Queue()

# model = AI_counter("yolo11n.pt")
model = ai_system.raspi_depan()
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
fetch_trigger = False
frame_lock = threading.Lock()
info_lock = threading.Lock()

@app.on_event("startup")
def startup_event():
    global cap
    cap = cv2.VideoCapture("ujiniksap/depan/v7_1.mp4")

    t = threading.Thread(target=thread_function, daemon=True)
    t.start()

counter = 0
def thread_function():
    global fetch_trigger, current_frame, info, counter
    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            counter += 1
            print(f"putaran: {counter}")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            model.clear_attr()
            continue

        result = model.scan_depan(frame)

        with frame_lock:
            current_frame = result["frame"]
            if (result["bbox"] != -1):
                with info_lock:
                    info = {"info":str(result["bbox"]),"filename":"belum ada"}
                    print(info)
@app.get("/get_info")
async def get_info():
    global info
    with info_lock:
        if info is not None:
            data = info.copy()
            info = None
            return {"info":data["info"],"filename": data["filename"]}
    return {"None":None}

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




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)