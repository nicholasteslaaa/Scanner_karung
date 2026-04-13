# API_master.py

from fastapi import FastAPI,Form,Response
import cv2
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import bcrypt
import threading
import signal
import sys
import time
from AI_system import AI_counter
import requests
import pandas as pd
from io import BytesIO

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
fetch_trigger = False
frame_lock = threading.Lock()

RASPI1_IP = "192.168.100.218:8000"
RASPI2_IP = "192.168.100.223:8000"

@app.on_event("startup")
def startup_event():
    global cap
    cap = cv2.VideoCapture("Person Walking.mp4")

    t = threading.Thread(target=thread_function, daemon=True)
    t_fetch_info = threading.Thread(target=fetch_info, daemon=True)
    t.start()
    t_fetch_info.start()

def fetch_info():
    global fetch_trigger, info
    max_attempts = 5

    while True:  # Fix 2: always keep thread alive
        if not fetch_trigger:  # Fix 3: wait when there's nothing to do
            time.sleep(0.1)
            continue

        current_info = info  # Fix 4: snapshot to avoid race condition with None check
        if current_info is None:
            fetch_trigger = False
            continue

        res = {"None":None}
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"http://{RASPI2_IP}/get_info", timeout=3)
                response.raise_for_status()
                res = response.json()
                print(res)
                break  # success — skip the else block

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed:", e)
                time.sleep(1)
        else:
            # Only runs if all attempts exhausted (no break)
            print("All fetch attempts failed. Using res = None.")
            res = {"None":None}

        # DB insert always happens here, after the loop
        con = get_db()
        cur = con.cursor()

        variasi = 2
        jumlah_karung = 10
        cam1 = current_info["info"]
        cam2 = -1
        path1 = current_info["filename"]
        path2 = ""

        if "info" in res:
            cam2 = res["info"]
        if "filename" in res:
            path2 = res["filename"]

        cur.execute("""
                    INSERT INTO inventori (variasi, jumlah_karung, cam1, cam2, path1, path2)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        variasi,
                        jumlah_karung,
                        cam1,
                        cam2,
                        path1,
                        path2
                    ))
        con.commit()
        con.close()
        info = {"None":None}
        fetch_trigger = False

def thread_function():
    global fetch_trigger,current_frame,info
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
                fetch_trigger = True

def get_db():
    con = sqlite3.connect("db.sqlite3")
    con.row_factory = sqlite3.Row
    return con

def table_exists(cur, table_name):
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cur.fetchone() is not None

@app.post("/get_table")
def get_table(offset: int = 0):
    con = get_db()
    cur = con.cursor()
    gap = 5
    start = offset*gap
    end = start+gap
    try:
        cur.execute("SELECT * FROM inventori")
        # cur.execute("SELECT * FROM eval")
        rows = cur.fetchall()
        return [dict(row) for row in rows[start:end]]
    except Exception as e:
        return {"error": str(e)}

@app.get("/get_count") # Changed from .post to .get
def get_count():
    con = get_db()
    cur = con.cursor()
    try:
        # Use SQL COUNT instead of fetching all rows into memory
        cur.execute("SELECT COUNT(*) as total FROM inventori")
        # cur.execute("SELECT COUNT(*) as total FROM eval")
        result = cur.fetchone()
        return {"count": result["total"]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        con.close()


@app.get("/summary_info")
def get_summary():
    con = get_db()
    # Using a Row-based cursor makes it much easier to convert to a dict
    # If using sqlite3, you'd set con.row_factory = sqlite3.Row
    cur = con.cursor()
    try:
        # We give the columns aliases (total_karung, total_data)
        # so they have names in our resulting dictionary
        query = "SELECT SUM(jumlah_karung) AS total_karung, COUNT(*) AS total_rows FROM inventori;"
        # query = "SELECT SUM(jumlah_karung) AS total_karung, COUNT(*) AS total_rows FROM eval;"
        cur.execute(query)

        row = cur.fetchone()

        # If using standard tuples, map them manually:
        return {
            "total_karung": row[0] or 0,  # Handles case where table is empty
            "total_rows": row[1]
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        con.close()

@app.get("/download_excel")
def download_excel():
    con = get_db()
    try:
        # 1. Read DB with Pandas
        query = "SELECT * FROM inventori(datetime,variasi,jumlah_karung,cam1,cam2)"
        df = pd.read_sql_query(query, con)

        # 2. Convert to XLSX in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventory')

        # 3. Seek to start of stream
        output.seek(0)

        # 4. Return as a downloadable file response
        headers = {
            'Content-Disposition': 'attachment; filename=f"inventory_report.xlsx"'
        }
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        return {"error": str(e)}
    finally:
        con.close()

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

def signal_handler(signum,frame):
    cap.release()
    sys.exit(0)

# Register the custom handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTSTP, signal_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
