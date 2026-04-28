import cv2
import numpy as np
import time
from ultralytics import YOLO
from collections import defaultdict
import os
import module_menghitung_lapisan
import shutil
from datetime import datetime
from preprocessing import sharpen_image
from dotenv import load_dotenv

load_dotenv()

class helper:
    def check(self,arah):
        if arah == {1, 2, 3}:
            return False
        if arah == {3, 2, 1}:
            return True
        else:
            return None


    def hapus_tempfile(self,folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    # print(f"hapus file: {filename}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    # print(f"hapus directory: {filename}")
            except Exception as e:
                print(f'Failed to delete {file_path}. {e}')




class raspi_depan:
    def __init__(self):
        self.object_states = defaultdict(str)
        self.previous_centroids = {}
        self.total_count_L_to_R = 0
        self.total_count_R_to_L = 0
        self.temp = []
        self.state = False
        self.modus = []
        self.num = 0

        self.CONF_THRES = 0.5
        self.IOU_THRES = 0.45

        self.folder_path = 'temp_file/'
        WEIGHTS_PATH = os.getenv("MODEL_PATH")
        self.model = YOLO(WEIGHTS_PATH)

        self.helper = helper()

    def clear_attr(self):
        self.object_states = defaultdict(str)
        self.previous_centroids = {}
        self.total_count_L_to_R = 0
        self.total_count_R_to_L = 0
        self.temp = []
        self.state = False
        self.modus = []
        self.num = 0


    def scan_depan(self,frame):
        # global modus, num, object_states, previous_centroids, total_count_L_to_R, total_count_R_to_L, temp, pola, state, model, CONF_THRES, IOU_THRES, folder_path
        # CLASS_NAMES = ['karung']

        #  Garis Vertikal
        LINE_POSITION_NONE = 0.25
        LINE_POSITION_RATIO_A = 0.50
        LINE_POSITION_RATIO_B = 0.80

        # Konfigurasi Area Tengah
        CENTER_AREA_NONE = 0.25
        CENTER_AREA_START_RATIO = 0.50
        CENTER_AREA_END_RATIO = 0.80


        frame_height, frame_width = frame.shape[:2]

        # Perhitungan Garis
        column_x_a = int(frame_height * LINE_POSITION_RATIO_A)
        column_x_b = int(frame_height * LINE_POSITION_RATIO_B)
        column_x_x = int(frame_height * LINE_POSITION_NONE)

        CENTER_AREA_NONE = int(frame_height * CENTER_AREA_NONE)
        CENTER_AREA_START_Y = int(frame_height * CENTER_AREA_START_RATIO)
        CENTER_AREA_END_Y = int(frame_height * CENTER_AREA_END_RATIO)

        frame[0:CENTER_AREA_NONE, :] = [0, 0, 255]
        original_frame = frame.copy()

        # Inferensi
        # persist=True penting jika ingin menggunakan tracker bawaan (id)
        results = self.model.track(frame, persist=True, conf=self.CONF_THRES, iou=self.IOU_THRES, verbose=False)
        # Gambar Garis Panduan
        cv2.line(frame, (0, column_x_x), (frame_width, column_x_x), (200, 200, 210), 1)

        cv2.line(frame, (0, column_x_a), (frame_width, column_x_a), (0, 255, 0), 1)
        cv2.line(frame, (0, column_x_b,), (frame_width, column_x_b), (0, 0, 255), 1)
        # cv2.line(frame, (50,100), (600,100 ), (255, 0, 0), 1)#bgr red
        # cv2.line(frame, (50,200), (600,200 ), (0, 0, 255), 1)#bgr red
        # cv2.line(frame, (50,350), (600, 350), (0, 255, 0), 1)#green
        frame_centroids = []
        current_ids = []
        row2 = -1
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.int().cpu().numpy()
            confs = results[0].boxes.conf.cpu().numpy()
            clss = results[0].boxes.cls.int().cpu().numpy()

            for box, obj_id, conf, cls in zip(boxes, ids, confs, clss):
                x1, y1, x2, y2 = map(int, box)
                center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2

                frame_centroids.append((center_x, center_y))
                current_ids.append(obj_id)

                # --- LOGIKA CROSSING (State Machine) ---
                state_old = self.object_states[obj_id]
                center_x_old = self.previous_centroids.get(obj_id)

                if column_x_a < center_x < column_x_b:
                    self.object_states[obj_id] = 'BETWEEN'

                if center_x_old is not None:
                    if state_old == 'START_L' and center_x > column_x_b:
                        self.total_count_L_to_R += 1
                        self.object_states[obj_id] = 'COUNTED'
                        print("kanaaan")
                    elif state_old == 'START_R' and center_x < column_x_a:
                        self.total_count_R_to_L += 1
                        self.object_states[obj_id] = 'COUNTED'
                        print("kiiiiirriiii")

                if center_x < column_x_a and state_old not in ['START_L', 'COUNTED']:
                    self.object_states[obj_id] = 'START_L'

                elif center_x > column_x_b and state_old not in ['START_R', 'COUNTED']:
                    self.object_states[obj_id] = 'START_R'

                self.previous_centroids[obj_id] = center_x

                # Visualisasi Box
                label = f'ID:{obj_id} {self.object_states[obj_id]} {conf:.2f}'
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # --- GLOBAL CENTROID ---
        # print(frame_centroids)
        if frame_centroids:
            all_x = [c[0] for c in frame_centroids]
            all_y = [c[1] for c in frame_centroids]
            global_center_x, global_center_y = int(np.mean(all_x)), int(np.mean(all_y))

            if CENTER_AREA_START_Y <= global_center_y <= CENTER_AREA_END_Y:
                status_text = "STATUS:  TENGAH"
                color = (0, 0, 255)
                cv2.putText(frame, f'Sisi: {len(frame_centroids)}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)
                cv2.putText(frame, f'Est. Total: {len(frame_centroids) * 2}', (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            color, 1)
                kondisi = 0
                self.temp.append(0)
                # print(f"capture!{len(frame_centroids)}")
                self.modus.append(len(frame_centroids))
                now = datetime.now()

                filename = 'temp_file/' + str(now.strftime("%d %B %Y %H:%M:%S_")) + str(self.num) + '.jpg'

                # filename='temp_file/temp_image_'+str(num)+'.jpg'

                cv2.imwrite(filename, original_frame)
                self.num += 1

            elif global_center_y <= CENTER_AREA_NONE:
                status_text = "Area None"
                color = (0, 0, 255)

            elif global_center_y > CENTER_AREA_END_Y:
                status_text = "STATUS: zona C"
                color = (255, 0, 0)
                self.temp.append(3)
            elif CENTER_AREA_NONE < global_center_y < CENTER_AREA_START_Y:
                status_text = "STATUS: zona A"
                color = (0, 255, 0)
                self.clear_attr()
                self.temp.append(1)
            cv2.circle(frame, (global_center_x, global_center_y), 10, color, -1)
            cv2.putText(frame, status_text, (50, frame_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 1)
            # tmp = check(pola)
        else:
            cv2.putText(frame, 'none', (50, frame_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
            # print(f'TOTAL : {temp}')
            res = []
            self.num = 0

            for item in self.temp:
                if item not in res:
                    res.append(item)
            self.temp = []
            # print(f'result : {res}')
            if res == [1, 0, 3]:
                time.sleep(3)
                self.modus = []
                self.num = 0
                for filename in os.listdir(self.folder_path):
                    file_path = os.path.join(self.folder_path, filename)
                    if (file_path[-6:] == '_3.jpg') and self.state:
                        result = sharpen_image(file_path)
                        cv2.imwrite(file_path, result)

                        _, row2 = module_menghitung_lapisan.lapisan(file_path, caminfo=2)
                        shutil.move(file_path, 'folder_foto/')
                        self.state = False
                        print(row2,"<<")
                        # self.clear_attr()

                self.helper.hapus_tempfile(self.folder_path)
                self.state = True  # ← re-set state=True after clear_attr resets it to False
                time.sleep(3)

            elif res == [3, 0, 1]:
                self.helper.hapus_tempfile(self.folder_path)
                self.clear_attr()  # ← same here
                self.state = True  # ← re-set after clear
                time.sleep(3)
        self.state = True
        # Pembersihan
        for oid in list(self.previous_centroids.keys()):
            if oid not in current_ids:
                self.previous_centroids.pop(oid, None)
                self.object_states.pop(oid, None)

        return {"frame":frame,"bbox":row2}


class raspi_samping:
    def __init__(self):
        self.object_states = defaultdict(str)
        self.previous_centroids = {}
        self.total_count_L_to_R = 0
        self.total_count_R_to_L = 0
        self.temp = []
        self.modus = []
        self.num = 0
        self.state = False

        self.CONF_THRES = 0.5
        self.IOU_THRES = 0.45

        self.folder_path = 'temp_file/'
        WEIGHTS_PATH = os.getenv("MODEL_PATH")
        self.model = YOLO(WEIGHTS_PATH)

        self.helper = helper()

    def clear_attr(self):
        self.object_states = defaultdict(str)
        self.previous_centroids = {}
        self.total_count_L_to_R = 0
        self.total_count_R_to_L = 0
        self.temp = []
        self.modus = []
        self.num = 0
        self.state = False

    def scan_samping(self,frame):
        # global modus, num, object_states, previous_centroids, total_count_L_to_R, total_count_R_to_L, temp, pola, state, model, CONF_THRES, IOU_THRES, folder_path

        frame_height, frame_width = frame.shape[:2]

        LINE_POSITION_RATIO_R = 0.90
        LINE_POSITION_RATIO_L = 0.20
        LINE_Y_START = 70
        LINE_COLOR = (190, 20, 15)
        LINE_THICKNESS = 2

        # Konfigurasi Area Tengah
        CENTER_AREA_START_RATIO = 0.40
        CENTER_AREA_END_RATIO = 0.60

        column_x_r = int(frame_width * LINE_POSITION_RATIO_R)
        column_x_l = int(frame_width * LINE_POSITION_RATIO_L)
        CENTER_AREA_START_X = int(frame_width * CENTER_AREA_START_RATIO)
        CENTER_AREA_END_X = int(frame_width * CENTER_AREA_END_RATIO)



        original = frame.copy()

        # kalau gagal persist = False
        results = self.model.track(frame, persist=True, conf=self.CONF_THRES, iou=self.IOU_THRES, verbose=False)

        cv2.line(frame, (column_x_l, LINE_Y_START), (column_x_l, frame_height), LINE_COLOR, LINE_THICKNESS)
        cv2.line(frame, (column_x_r, LINE_Y_START), (column_x_r, frame_height), LINE_COLOR, LINE_THICKNESS)
        cv2.line(frame, (CENTER_AREA_START_X, LINE_Y_START), (CENTER_AREA_START_X, frame_height), (0, 255, 0), 1)
        cv2.line(frame, (CENTER_AREA_END_X, LINE_Y_START), (CENTER_AREA_END_X, frame_height), (0, 255, 0), 1)

        frame_centroids = []
        current_ids = []

        row1 = -1

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.int().cpu().numpy()
            confs = results[0].boxes.conf.cpu().numpy()
            clss = results[0].boxes.cls.int().cpu().numpy()

            for box, obj_id, conf, cls in zip(boxes, ids, confs, clss):
                x1, y1, x2, y2 = map(int, box)
                center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2

                frame_centroids.append((center_x, center_y))
                current_ids.append(obj_id)

                ### --- LOGIKA CROSSING untuk arah---###
                state_old = self.object_states[obj_id]
                center_x_old = self.previous_centroids.get(obj_id)

                if column_x_l < center_x < column_x_r:
                    self.object_states[obj_id] = 'BETWEEN'

                if center_x_old is not None:
                    if state_old == 'START_L' and center_x > column_x_r:
                        self.total_count_L_to_R += 1
                        self.object_states[obj_id] = 'COUNTED'
                        print("kanaaan")
                    elif state_old == 'START_R' and center_x < column_x_l:
                        self.total_count_R_to_L += 1
                        self.object_states[obj_id] = 'COUNTED'
                        print("kiiiiirriiii")

                if center_x < column_x_l and state_old not in ['START_L', 'COUNTED']:
                    self.object_states[obj_id] = 'START_L'

                elif center_x > column_x_r and state_old not in ['START_R', 'COUNTED']:
                    self.object_states[obj_id] = 'START_R'

                self.previous_centroids[obj_id] = center_x

                ##### Visualisasi Box
                label = f'ID:{obj_id} {self.object_states[obj_id]} {conf:.2f}'
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        ############ --- GLOBAL CENTROID ---
        if frame_centroids:
            all_x = [c[0] for c in frame_centroids]
            all_y = [c[1] for c in frame_centroids]
            global_center_x, global_center_y = int(np.mean(all_x)), int(np.mean(all_y))

            if CENTER_AREA_START_X <= global_center_x <= CENTER_AREA_END_X:
                status_text = "STATUS:  TENGAH"
                color = (0, 0, 255)
                cv2.putText(frame, f'Sisi: {len(frame_centroids)}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)
                cv2.putText(frame, f'Total: {len(frame_centroids) * 2}', (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)
                # kondisi = 0
                self.temp.append(0)
                # print(f"capture!{len(frame_centroids)}")
                self.modus.append(len(frame_centroids))
                now = datetime.now()

                filename = 'temp_file/' + str(now.strftime("%d %B %Y %H:%M:%S_")) + str(self.num) + '.jpg'

                cv2.imwrite(filename, original)
                self.num += 1

            elif global_center_x > CENTER_AREA_END_X:
                status_text = "STATUS: kanan"
                color = (255, 0, 0)
                # kondisi = 3
                self.temp.append(3)
            elif global_center_x < CENTER_AREA_START_X:
                status_text = "STATUS: kiri"
                color = (0, 255, 0)
                # kondisi = 1
                self.temp.append(1)
            cv2.circle(frame, (global_center_x, global_center_y), 10, color, -1)
            cv2.putText(frame, status_text, (50, frame_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 1)
        else:
            cv2.putText(frame, 'none', (50, frame_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
            res = []
            self.num = 0

            for item in self.temp:
                if item not in res:
                    res.append(item)
            self.temp = []

            if res == [3, 0, 1]:
                time.sleep(1)

                self.modus = []
                self.num = 0
                for filename in os.listdir(self.folder_path):
                    file_path = os.path.join(self.folder_path, filename)
                    if (file_path[-6:] == '_3.jpg') and self.state:
                        _, row1 = module_menghitung_lapisan.lapisan(file_path, caminfo=1)
                        shutil.move(file_path, 'folder_foto/')
                        # self.state = False
                        self.clear_attr()
                        """
                        request: lapis_raspi2,row2 = lapisan()
                        lapis_raspi1,row1 = lapisan()


                        hasil = hitung(C1L1,C1L2,C2L1,C2L2,row1,row2):
                        atau pakai
                        hitung(row1,row2)

                        add database -> hasil
                        """
                        # nunggu json
                        # hitung karung
                        # add database
                self.helper.hapus_tempfile(self.folder_path)

            elif res == [1, 0, 3]:
                # print("tidak hitung")
                self.helper.hapus_tempfile(self.folder_path)

                time.sleep(1)
        self.state = True
        # Pembersihan State
        for oid in list(self.previous_centroids.keys()):
            if oid not in current_ids:
                self.previous_centroids.pop(oid, None)
                self.object_states.pop(oid, None)

        return {"frame": frame,"bbox": row1}


if __name__ == "__main__":
    VIDEO_PATH1 = 'ujiniksap/samping/v7_1.mp4'
    cap_1 = cv2.VideoCapture(VIDEO_PATH1)
    raspi_1 = raspi_samping()

    VIDEO_PATH2 = 'ujiniksap/depan/v7_1.mp4'
    cap_2 = cv2.VideoCapture(VIDEO_PATH2)
    raspi_2 = raspi_depan()

    putaran = 0
    last_row1 = -1
    last_row2 = -1

    # while True:
    #     ret_1, frame_1 = cap_1.read()
    #     ret_2, frame_2 = cap_2.read()
    #
    #     if not ret_1:
    #         cap_1.set(cv2.CAP_PROP_POS_FRAMES, 0)
    #         raspi_1.clear_attr()
    #         continue
    #
    #     if not ret_2:
    #         cap_2.set(cv2.CAP_PROP_POS_FRAMES, 0)
    #         raspi_2.clear_attr()
    #         continue
    #
    #     result_1 = raspi_1.scan_samping(frame_1)
    #     frame_1 = result_1["frame"]
    #
    #     result_2 = raspi_2.scan_depan(frame_2)
    #     frame_2 = result_2["frame"]
    #
    #     row1, row2 = result_1["bbox"], result_2["bbox"]
    #
    #     # Update last known results when new data arrives
    #     updated = False
    #     if row1 != -1:
    #         last_row1 = row1
    #         updated = True
    #     if row2 != -1:
    #         last_row2 = row2
    #         updated = True
    #
    #     if updated:
    #         many_1 = len(last_row1) if not isinstance(last_row1, int) else last_row1
    #         many_2 = len(last_row2) if not isinstance(last_row2, int) else last_row2
    #         putaran += 1
    #         print(f"kamera samping: {many_1}, kamera depan: {many_2}")
    #         print(f"putaran: {putaran}")
    #     else:
    #         print(f"\r{row1}|{row2}", end="", flush=True)
    #
    #     cv2.imshow("detection", np.hstack((frame_1, frame_2)))
    #
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break
    #
    # cap_1.release()
    # cap_2.release()
    # cv2.destroyAllWindows()

    while True:
        ret_2, frame_2 = cap_2.read()
        if not ret_2:
            cap_2.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        result_2 = raspi_2.scan_depan(frame_2)
        frame_2 = result_2["frame"]

        row2 = result_2["bbox"]

        # Update last known results when new data arrives

        if row2 != -1:
            putaran += 1
            print(f"kamera depan: {len(row2)}")
            print(f"putaran: {putaran}")
        else:
            print(f"\r{row2}", end="", flush=True)

        # cv2.imshow("detection", np.hstack((frame_1, frame_2)))
        cv2.imshow("kamera depan",frame_2)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap_2.release()
    cv2.destroyAllWindows()
