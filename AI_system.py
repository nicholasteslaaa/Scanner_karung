
import cv2
from ultralytics import YOLO
from datetime import datetime

class AI_counter:
    def __init__(self,model_path:str="yolo11n.pt"):
        self.model = YOLO(model_path)

        # Konfigurasi Garis Vertikal
        self.LINE_POSITION_RATIO_R = 0.90
        self.LINE_POSITION_RATIO_L = 0.20
        self.LINE_Y_START = 70
        self.LINE_COLOR = (190, 20, 15)
        self.LINE_THICKNESS = 2
        self.CENTER_AREA_START_RATIO = 0.40
        self.CENTER_AREA_END_RATIO = 0.60

        self.trigger = False

    def is_point_inside_box(self,point,boxes):
        min_x, min_y, max_x, max_y = boxes
        cx,cy = point
        
        return cx > min_x and cx < max_x and cy > min_y and cy <max_y

    def is_behind_the_line(self,line_x,cx):
        return cx > line_x

    def detect(self,frame):
        # frame = cv2.flip(frame.copy(),1)
        frame = frame.copy()
        
        h,w = frame.shape[:2]
        
        result = self.model(frame,verbose=False)
        
        cx,cy = int(w),int(w)
        
        column_x_r = int(w * self.LINE_POSITION_RATIO_R)
        column_x_l = int(w * self.LINE_POSITION_RATIO_L)
        CENTER_AREA_START_X = int(w * self.CENTER_AREA_START_RATIO)
        CENTER_AREA_END_X = int(w * self.CENTER_AREA_END_RATIO)
        cxl= (CENTER_AREA_START_X+CENTER_AREA_END_X)//2
        
        
        isPastMiddle = False
        isPastEnd = False
        isPastStart = False
        
        detected_person = 0
        
        flag_out = False
        # filename = f"./savedFrame/{datetime.now()}.jpeg"
        filename = f"{datetime.now()}.png"
        path = f"/var/www/html/img/{filename}" 
        
        for box in result[0].boxes:
            class_detect = int(box.cls)
        
            if(class_detect == 0):
                detected_person += 1
            
            min_x, min_y, max_x, max_y = tuple(int(i) for i in box.xyxy[0])
            cx,cy = (max_x+min_x)//2, (max_y+min_y)//2
            
            isPastMiddle = self.is_behind_the_line(cx,cxl)
            isPastEnd = self.is_behind_the_line(cx,column_x_l)
            isPastStart = self.is_behind_the_line(column_x_r,cx)
            
            if isPastMiddle and not isPastEnd and not self.trigger:
                cv2.imwrite(path,frame)
                flag_out = True
                self.trigger = True
                
            cv2.circle(frame,(cx,cy),1,(0,255,255),5,1)
            cv2.rectangle(frame,(min_x,min_y),(max_x,max_y),(0,255,255),2,1)
        
        color_l = (0,255,0) if isPastEnd else (0,0,255)
            
        color_r = (0,255,0)
        if isPastStart:
            self.trigger = False
            color_r = (0,0,255)
        
        cv2.line(frame, (column_x_l, self.LINE_Y_START), (column_x_l, h), color_l, self.LINE_THICKNESS)
            
        cv2.line(frame, (column_x_r, self.LINE_Y_START), (column_x_r, h), color_r, self.LINE_THICKNESS)
        
        color_cl = (0,0,255) if self.is_behind_the_line(CENTER_AREA_START_X,cx) else (0,255,0)
        cv2.line(frame, (CENTER_AREA_START_X, self.LINE_Y_START), (CENTER_AREA_START_X, h), color_cl, 1)
        color_cr = (0,0,255) if self.is_behind_the_line(CENTER_AREA_END_X,cx) else (0,255,0)
        cv2.line(frame, (CENTER_AREA_END_X, self.LINE_Y_START), (CENTER_AREA_END_X, h), color_cr, 1)
        
        cv2.circle(frame,(cxl,h//2),1,(0,0,255),1,1)
        
        return {"frame":frame,"info":detected_person,"trigger":flag_out,"filename":filename}
        
if __name__ == "__main__":
    AI = AI_counter()
    cap = cv2.VideoCapture("Person Walking.mp4")
    while True:
        ret, frame = cap.read()
        
        if (not ret):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        frame = AI.detect(frame)
        cv2.imshow("system",frame)
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    cap.release()
    cv2.destroyAllWindows()
        