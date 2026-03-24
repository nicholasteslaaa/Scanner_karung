from fastapi import FastAPI,Form
import cv2
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import bcrypt
import socket
from dotenv import set_key
import threading
import signal
import sys
import time
from AI_system import AI_counter
import requests

model = AI_counter("yolo11n.pt")

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
    cap = cv2.VideoCapture("Person Walking.mp4")

    t = threading.Thread(target=thread_function, daemon=True)
    t.start()
    
def fetch_info():
    max_attempts = 5

    for attempt in range(max_attempts):
        try:
            response = requests.get(
                "http://localhost:8001/get_info",
                timeout=3
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1} failed:", e)
            time.sleep(1)

    return None

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
        
        with frame_lock:
            current_frame = result["frame"]
            if (result["trigger"]):
                info = result
                
                res = fetch_info()   # Try once (internally 5 attempts)

                if res is None:
                    print("Server 8001 unavailable. Continuing without cam2 info.")
                    
                con = get_db()
                cur = con.cursor()
                
                cur.execute("""
                    INSERT INTO inventori (jumlah_karung, cam1, cam2, path1, path2)
                    VALUES (?, ?, ?, ?, ?)
                """, (10,info["info"],"" if res is None else res["info"],info["filename"],info["filename"]))
                
                con.commit()
                con.close()
            else:
                info = None

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

@app.post("/get_table")
def get_table():
    con = get_db()
    cur = con.cursor()

    try:
        cur.execute("SELECT * FROM inventori")
        rows = cur.fetchall()
        result = [dict(row) for row in rows]
        return result

    except Exception as e:
        return {"error": str(e)}

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

@app.get("/download")
def download_file(filename: str):
    file_path = os.path.join(FILE_DIRECTORY, filename)

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=filename  # <- important, forces download
    )

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

@app.get("/get_info")
async def get_info():
    global info
    return info

def signal_handler(signum,frame):
    cap.release()
    sys.exit(0)

# Register the custom handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTSTP, signal_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    