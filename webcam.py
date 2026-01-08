import warnings
warnings.filterwarnings("ignore")

import cv2
import torch
import function.utils_rotate as utils_rotate
import function.helper as helper
import time
import os

# Load YOLOv5 model
yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector_nano_61.pt', source='local')
yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr_nano_62.pt', source='local')
yolo_license_plate.conf = 0.6

vid = cv2.VideoCapture(0)  # webcam
last_saved_time = 0
save_interval = 2  # giây

while True:
    ret, frame = vid.read()
    if not ret:
        break

    cv2.imshow("Live Cam", frame)

    plates = yolo_LP_detect(frame, size=640)
    list_plates = plates.pandas().xyxy[0].values.tolist()

    for plate in list_plates:
        x1, y1, x2, y2 = int(plate[0]), int(plate[1]), int(plate[2]), int(plate[3])
        crop_img = frame[y1:y2, x1:x2]

        lp = ""
        for cc in range(2):
            for ct in range(2):
                lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
                if lp != "unknown":
                    now = time.time()
                    if now - last_saved_time >= save_interval:
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        filename = f"{lp}_{timestamp}.jpg".replace(" ", "_")
                        cv2.imwrite(filename, crop_img)
                        print(f"Biển số: {lp}, lưu file: {filename}")
                        last_saved_time = now
                    break
            if lp != "unknown":
                break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

vid.release()
cv2.destroyAllWindows()
