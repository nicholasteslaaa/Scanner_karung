import cv2
import numpy as np
from ultralytics import YOLO
import time
from datetime import datetime
import jsonfile
import os
from dotenv import load_dotenv

load_dotenv()

now = datetime.now()
model_path = os.getenv("MODEL_PATH")
db = os.getenv("DATABASE_URL")

#  Jika diperlukan
def cek_rata(c1,c2):
    pass
    
def lapisan(image_path,conf_threshold = 0.5,iou_threshold=0.4,toleransi=0.45,caminfo=0):
    # 1. Load Model & Prediksi
    model = YOLO(model_path)
    
    results = model.predict(source=image_path, conf=conf_threshold, iou=iou_threshold, save=False,augment=True)
    result = results[0]

    # 2. Ekstrak Data
    boxes = result.boxes.xyxy.cpu().numpy()

    if len(boxes) == 0:
        print("tidak ada objek terdeteksi")
        exit()

    objek = []
    tinggi = []

    for box in boxes:
        x1, y1, x2, y2 = box
        cy = (y1 + y2) / 2
        cx = (x1 + x2) / 2
        h = y2 - y1
        objek.append({'box': box, 'cx': cx, 'cy': cy, 'h': h})
        tinggi.append(h)

    # Hitung rata-rata tinggi karung untuk referensi toleransi
    avg_h = np.mean(tinggi)
    threshold = avg_h * toleransi

    # 3. ALGORITMA PENGELOMPOKAN BARIS (HORIZONTAL LAYER)
    # Urutkan dulu semua berdasarkan Y 
    objek.sort(key=lambda k: k['cy'])
    rows = []
    current_row = []
    simpan_lapisan=[]
    if objek:
        current_row.append(objek[0])

    for i in range(1, len(objek)):
        obj = objek[i]
        # Bandingkan Y objek ini dengan rata-rata Y baris saat ini
        avg_y_current_row = np.mean([o['cy'] for o in current_row])
        
        # Jika selisih Y < threshold, maka dia teman satu baris (horizontal)
        if abs(obj['cy'] - avg_y_current_row) < threshold:
            current_row.append(obj)
        else:
            # Jika jauh, tutup baris lama, mulai baris baru
            rows.append(current_row)
            current_row = [obj]

    # Masukkan baris terakhir
    if current_row:
        rows.append(current_row)
    # 4. VISUALISASI HASIL
    frame = cv2.imread(image_path)
    
    print(f"--- TERDETEKSI {len(rows)} LAPIS (BARIS) ---")

    total_obj = 0
    # Loop per baris (Lapis Horizontal)
    for r_idx, row_objs in enumerate(rows):
        # Urutkan objek dalam baris dari kiri ke kanan (X)
        row_objs.sort(key=lambda k: k['cx'])
        count = len(row_objs)
        total_obj += count
        # print(f"Lapis {r_idx+1}: {count} item")
        simpan_lapisan.append(count)
        # Gambar kotak dan label
        for c_idx, obj in enumerate(row_objs):
            x1, y1, x2, y2 = map(int, obj['box'])
            color = (0, 255, 0) if r_idx % 2 == 0 else (0, 165, 255) 
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
            # ket. (B=Baris, K=Kolom)
            label = f"B{r_idx+1}.K{c_idx+1}"
            # Background label 
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(frame, (x1, y1 - 15), (x1 + w, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1)

        # Tulis total per baris di sisi kiri gambar
        avg_y_row = int(np.mean([o['cy'] for o in row_objs]))
        text_info = f"Lapis {r_idx+1}: {count}"
        cv2.putText(frame, text_info, (10, avg_y_row), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    # print(simpan_lapisan[-1],simpan_lapisan[-2])
    # untuk testing
    data_kamera=simpan_lapisan[-1],simpan_lapisan[-2],r_idx+1
    #add database python

    # Tulis Total Keseluruhan di pojok kiri atas
    # cv2.putText(frame, f"TOTAL: {total_obj}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    #read db camera depan data dari semua kamera harus sdh lengkap
    time.sleep(2)
    # c1,c2=read(db)
    ## hitung jumlah karung
    # print(f'{c1},{c2},total terdeteksi : {total_obj}')
    # hasil = hitung(c1[0],c1[1],c2[0],c2[1],total_obj)
    # print(hasil)
    # Tampilkan
    if caminfo==1:
        row = jsonfile.savejson(rows)
        # database.insert_data1(simpan_lapisan[-1],simpan_lapisan[-2],"-",len(simpan_lapisan),sum(simpan_lapisan),row)
        # print("insert database1 done")
    else:
        row = jsonfile.savejson(rows)
        # database.insert_data2(simpan_lapisan[-1],simpan_lapisan[-2],"-",len(simpan_lapisan),sum(simpan_lapisan),row)
        # print("insert database2 done")
        
    cv2.imwrite(f'folder_deteksi/{image_path[-28:]}',frame)
    
    # cv2.imshow("preview ", frame)
    # cv2.waitKey(2000)
    # cv2.destroyAllWindows()
    return data_kamera,rows
    
# #### untuk testing  
# kamera depan variasi 5
# kamera2,row2 = lapisan("/home/epiphany/yolov11_project/captures/analisis kamera depan/13 Maret 2026 22:24:18_37.jpg")
# kamera samping
# kamera1,row1 = lapisan("/home/epiphany/yolov11_project/captures/analisis kamera samping/13 Maret 2026 23:02:08_4.jpg")   
    
# # kamera depan variasi 5
# kamera2,row2 = lapisan("/home/epiphany/yolov11_project/captures/analisis kamera depan/13 Maret 2026 22:10:50_7.jpg")
# # kamera samping
# kamera1,row1 = lapisan("/home/epiphany/yolov11_project/captures/analisis kamera samping/18 Maret 2026 01:39:43_7.jpg")

# kamera depan variasi 3
# kamera2,row2=lapisan("/home/epiphany/yolov11_project/captures/analisis kamera depan/13 Maret 2026 22:21:12_52.jpg")
# kamera samping
# kamera1,row1=lapisan("/home/epiphany/yolov11_project/captures/analisis kamera samping/13 Maret 2026 22:46:57_0.jpg")

# # kamera depan variasi 7
# kamera2,row2=lapisan("/home/epiphany/yolov11_project/captures/analisis kamera depan/18 Maret 2026 01:28:14_15.jpg")
# # kamera samping
# kamera1,row1=lapisan("/home/epiphany/yolov11_project/captures/analisis kamera samping/13 Maret 2026 22:58:13_5.jpg")

# kamera depan variasi 2
# kamera2,row2 =lapisan("/home/epiphany/yolov11_project/captures/analisis kamera depan/18 Maret 2026 01:30:07_2.jpg")
# kamera samping
# kamera1,row1 =lapisan("/home/epiphany/yolov11_project/captures/analisis kamera samping/18 Maret 2026 01:19:03_3.jpg")

# kamera depan variasi 2
# kamera2,row2 =lapisan("/home/epiphany/yolov11_project/captures/analisis kamera depan/13 Maret 2026 22:12:18_4.jpg")
# # kamera samping
# kamera1,row1 =lapisan("/home/epiphany/yolov11_project/captures/analisis kamera samping/13 Maret 2026 22:41:25_8.jpg")

# kamera depan variasi 4
# kamera2 ,row2=lapisan("/home/epiphany/yolov11_project/captures/analisis kamera depan/18 Maret 2026 21:15:50_4.jpg")
# kamera samping
# kamera1 ,row1=lapisan("/home/epiphany/yolov11_project/captures/analisis kamera samping/18 Maret 2026 21:13:59_7.jpg")

# print(kamera1,kamera2)
# print(hitung(kamera1[0],kamera1[1],kamera2[0],kamera2[1],row1,row2))
# print(row2)



    