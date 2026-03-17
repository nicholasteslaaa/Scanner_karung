import cv2, os, numpy as np

class webcam_stream:
    def __init__(self):
        self.cap = None
        self.ret, self.frame = None, None
        self.shape = None
        self.dtype = None
        
    
    def setup(self):
        self.cap = cv2.VideoCapture(0)
        self.ret, self.frame = self.cap.read()
        self.shape = self.frame.shape  # e.g., (480, 640, 3)
        self.dtype = self.frame.dtype
        
    
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame.tofile("frame_data.bin")

    def get_frame(self):
        width = 640
        height = 480
        channels = 3
        expected_size = width * height * channels
        
        if os.path.exists("frame_data.bin"):
            try:
                # Read the raw data
                raw_data = np.fromfile("frame_data.bin", dtype=np.uint8)
                
                # CRITICAL CHECK: Only process if the file is full
                if raw_data.size == expected_size:
                    frame = raw_data.reshape((height, width, channels))
                
                    return frame
                    
            except Exception as e:
                return
            

if __name__ == "__main__":
    camera = webcam_stream()
    camera.setup()
    
    print("stream camera started")
    while True:
        camera.update_frame()