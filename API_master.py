from fastapi import FastAPI,Form
import cv2
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import bcrypt
import socket
from dotenv import dotenv_values, set_key
from webcam_manager import webcam_stream
import threading
import signal
import sys
import time
from AI_system import AI_counter

model = AI_counter("yolo11n.pt")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# It's better to define thecamera here, but ensure it's accessible
# camera = webcam_stream()

cap = None
current_frame = None
info = None
frame_lock = threading.Lock() 



@app.on_event("startup")
def startup_event():
    global cap
    cap = cv2.VideoCapture("Person Walking.mp4")

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
        
        result = model.detect(frame)
        # frame = result["frame"]
        print(f"Info: {info}")
        
        with frame_lock:
            current_frame = result["frame"]
            info = result["info"]

def get_db():
    con = sqlite3.connect("db.sqlite3")
    con.row_factory = sqlite3.Row
    return con

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

ENV_PATH = "webcam-stream\.env"
API_URL = f"http://{get_local_ip()}:8000"
set_key(ENV_PATH, "VITE_CAM1", f"http://{get_local_ip()}:8000")


def table_exists(cur, table_name):
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cur.fetchone() is not None


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

@app.post("/login")
def login(username:str = Form(...), password:str = Form(...)):
    con = get_db()
    cur = con.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_table (
        username TEXT PRIMARY KEY,
        password BLOB NOT NULL
    )
    """)
    
    query = cur.execute(f"SELECT * FROM user_table WHERE username = '{username}'")
    result = query.fetchone()

    if (result is None):
        return {"Status":"Account Not Found!"}
    
    if (bcrypt.checkpw(password.encode(),result[1])):
        return {"Status":"Success"}
    else:
        return {"Status":"Failed"}
    
def register(username:str , password):
    con = get_db()
    cur = con.cursor()
    
    query = cur.execute(f"SELECT * FROM user_table WHERE username = ?",(username,))
    result = query.fetchone()
    
    if (not (result is None)):
        return {"Status":"Username Already Exist!"}
    cur.execute(f"INSERT INTO user_table(username,password) VALUES (?,?)",[username,bcrypt.hashpw(password.encode(),bcrypt.gensalt())])    
    con.commit()
    return {"Status":"Success"}


def signal_handler(frame,sig):
    cap.release()
    sys.exit(0)

# Register the custom handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTSTP, signal_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    