import os
import cv2
import numpy as np
from ultralytics import YOLO
from paddleocr import PaddleOCR
from PIL import Image, ImageEnhance
from pathlib import Path
import logging
import csv
from collections import defaultdict
import difflib

# === CONFIGURATION ===
YOLO_MODEL_PATH = os.environ.get("YOLO_MODEL_PATH", "best.pt")
VIDEO_DIR = os.environ.get("INPUT_DIR", "input")
IMAGE_DIR = os.environ.get("INPUT_DIR", "input")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")
DEVICE = os.environ.get('DEVICE', 'cpu')

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)
CSV_PATH = os.path.join(OUTPUT_DIR, "vehicle_log.csv")

# Suppress PaddleOCR DEBUG logs
logging.getLogger('ppocr').setLevel(logging.WARNING)

# === Initialize Models ===
print("[INFO] Loading YOLOv8 model...")
yolo = YOLO(YOLO_MODEL_PATH).to(DEVICE)
print("[INFO] Loading PaddleOCR...")
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)

# === Vehicle Tracking Class ===
class VehicleTracker:
    def __init__(self):
        self.vehicles = []  # List of [best_plate, all_readings, first_timestamp]
        
    def clean_plate(self, text):
        """Clean plate text for comparison"""
        if text == "UNREADABLE":
            return text
        return ''.join(c.upper() for c in text if c.isalnum())
    
    def plates_similar(self, plate1, plate2, threshold=0.75):
        """Check if two plates are similar"""
        if plate1 == "UNREADABLE" and plate2 == "UNREADABLE":
            return True
        if plate1 == "UNREADABLE" or plate2 == "UNREADABLE":
            return False
            
        clean1 = self.clean_plate(plate1)
        clean2 = self.clean_plate(plate2)
        
        if clean1 == clean2:
            return True
            
        # Check similarity ratio
        similarity = difflib.SequenceMatcher(None, clean1, clean2).ratio()
        return similarity >= threshold
    
    def get_best_plate(self, readings):
        """Get best plate from multiple readings"""
        # Filter out UNREADABLE
        readable = [r for r in readings if r != "UNREADABLE"]
        if readable:
            # Return longest readable plate (usually more complete)
            return max(readable, key=len)
        return "UNREADABLE"
    
    def add_detection(self, plate_text, timestamp):
        """Add a new plate detection"""
        # Find if this matches any existing vehicle
        for i, (best_plate, readings, first_time) in enumerate(self.vehicles):
            if self.plates_similar(plate_text, best_plate) or any(self.plates_similar(plate_text, r) for r in readings):
                # Update existing vehicle
                readings.append(plate_text)
                new_best = self.get_best_plate(readings)
                self.vehicles[i] = [new_best, readings, first_time]
                return False  # Not a new vehicle
        
        # New vehicle
        self.vehicles.append([plate_text, [plate_text], timestamp])
        return True  # New vehicle
    
    def get_unique_vehicles(self):
        """Get list of unique vehicles with their best plate reading"""
        return [(best_plate, first_time) for best_plate, readings, first_time in self.vehicles]

# === Enhancement Functions ===
def enhance_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    contrast = np.std(gray)

    condition = "Clear"

    if brightness < 80:
        condition = "Lowlight"
        image = enhance_lowlight(image)
    elif contrast < 30:
        condition = "Foggy"
        image = enhance_fog(image)
    elif brightness > 200 and contrast < 40:
        condition = "Rainy"
        image = enhance_rain(image)

    return image, condition

def enhance_fog(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def enhance_rain(img):
    filtered = cv2.bilateralFilter(img, 9, 75, 75)
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(filtered, -1, kernel)
    return cv2.addWeighted(filtered, 0.7, sharpened, 0.3, 0)

def enhance_lowlight(img):
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    pil_img = ImageEnhance.Brightness(pil_img).enhance(1.5)
    pil_img = ImageEnhance.Contrast(pil_img).enhance(1.3)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

# === OCR Function ===
def recognize_plate(plate_img):
    result = ocr.ocr(plate_img, cls=True)
    if result and result[0]:
        return result[0][0][1][0]
    return "UNREADABLE"

# === Plate Detection ===
def detect_plates(frame):
    detections = []
    results = yolo(frame, verbose=False)
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            plate_crop = frame[y1:y2, x1:x2]
            text = recognize_plate(plate_crop)
            detections.append((x1, y1, x2, y2, text))
    return detections

# === Annotate Frame ===
def annotate_frame(frame, detections, extra_text=None):
    for (x1, y1, x2, y2, text) in detections:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, text, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    if extra_text:
        cv2.putText(frame, extra_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
    return frame

# === Timestamp Formatter ===
def format_timestamp(frame_num, fps):
    seconds = frame_num / fps
    ms = int((seconds - int(seconds)) * 1000)
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"

# === CSV Summary Tracker ===
summary_data = defaultdict(int)

# === Process Videos ===
def process_videos():
    with open(CSV_PATH, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Video Timestamp", "Plates Detected", "Vehicle Count", "Condition"])

        for filename in os.listdir(VIDEO_DIR):
            if not filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                continue
            path = os.path.join(VIDEO_DIR, filename)
            cap = cv2.VideoCapture(path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            w, h = int(cap.get(3)), int(cap.get(4))
            out_path = os.path.join(OUTPUT_DIR, f"annotated_{filename}")
            out = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

            frame_num = 0
            tracker = VehicleTracker()

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                video_ts = format_timestamp(frame_num, fps)
                frame, condition = enhance_image(frame)
                detections = detect_plates(frame)
                annotated = annotate_frame(frame, detections, extra_text=condition)
                out.write(annotated)

                # Process detections
                for (_, _, _, _, text) in detections:
                    tracker.add_detection(text, video_ts)

                frame_num += 1

            # Write unique vehicles to CSV
            unique_vehicles = tracker.get_unique_vehicles()
            for plate, first_time in unique_vehicles:
                csv_writer.writerow([first_time, plate, 1, condition])
                summary_data[plate] = 1

            cap.release()
            out.release()
            print(f"[DONE] Saved: {out_path} - Found {len(unique_vehicles)} unique vehicles")

# === Process Images ===
def process_images():
    with open(CSV_PATH, mode='a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        for filename in os.listdir(IMAGE_DIR):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            path = os.path.join(IMAGE_DIR, filename)
            img = cv2.imread(path)
            img, condition = enhance_image(img)
            detections = detect_plates(img)
            annotated = annotate_frame(img, detections, extra_text=condition)
            out_path = os.path.join(OUTPUT_DIR, f"annotated_{filename}")
            cv2.imwrite(out_path, annotated)

            # Use tracker for images too
            tracker = VehicleTracker()
            for (_, _, _, _, text) in detections:
                tracker.add_detection(text, f"Image: {filename}")

            unique_vehicles = tracker.get_unique_vehicles()
            if unique_vehicles:
                plates = [plate for plate, _ in unique_vehicles]
                plate_str = ", ".join(sorted(plates))
                csv_writer.writerow([f"Image: {filename}", plate_str, len(plates), condition])
                
                for plate, _ in unique_vehicles:
                    summary_data[plate] = 1

            print(f"[DONE] Saved: {out_path} - Found {len(unique_vehicles)} unique vehicles")

def process_stream(stream_url, save_name="stream_output.mp4"):
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print(f"[ERROR] Could not open stream: {stream_url}")
        return None, []

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_path = os.path.join(OUTPUT_DIR, f"annotated_{save_name}")
    out = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    print(f"[INFO] Processing CCTV stream...")
    frame_num = 0
    tracker = VehicleTracker()

    while cap.isOpened() and frame_num < 100:
        ret, frame = cap.read()
        if not ret:
            break

        video_ts = format_timestamp(frame_num, fps)
        frame, condition = enhance_image(frame)
        detections = detect_plates(frame)
        annotated = annotate_frame(frame, detections, extra_text=condition)
        out.write(annotated)

        # Process detections
        for (_, _, _, _, text) in detections:
            tracker.add_detection(text, video_ts)

        frame_num += 1

    unique_vehicles = tracker.get_unique_vehicles()
    final_plates = [plate for plate, _ in unique_vehicles]

    cap.release()
    out.release()
    print(f"[DONE] Stream saved to: {out_path} - Found {len(unique_vehicles)} unique vehicles")
    return f"annotated_{save_name}", sorted(final_plates)


# === MAIN ===
if __name__ == "__main__":
    print("[START] Processing videos and images...")
    process_videos()
    process_images()

    print("\n[SUMMARY]")
    print("Total Unique Vehicles Detected (including UNREADABLE):", len(summary_data))
    print("License Plate Frequencies:")
    for plate, count in summary_data.items():
        print(f"{plate}: {count} times")

    print("\n[COMPLETE] All data logged to:", CSV_PATH)