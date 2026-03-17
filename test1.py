import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import time

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    t = threading.Thread(target=thread_function, daemon=True)
    t.start()

def thread_function():
    while True:
        try:
            # Point to the other port
            response = requests.get("http://localhost:8000/get_info") # or 8001
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error connecting: {e}")
        
        # Add a delay so it doesn't overwhelm the system
        time.sleep(5)
            
@app.get("/get_info")
async def get_info():
    # Return a dictionary instead of a string
    return {"status": "success", "data": "info info"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    