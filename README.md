# Night-Time Traffic Monitoring and Vehicle Differentiation System

## Team: Team Tritech

### Team Members
- Shreya Gupta — shreyagupta1181@gmail.com
- Riya Kharbanda — riyakharbanda09@gmail.com
- Tanish — tanishahuja2005@gmail.com

---

## Problem Statement

Accurate vehicle monitoring at night is a challenge due to low visibility, glare from headlights, and poor footage quality. Our project solves this using a computer vision pipeline that detects vehicles, reads number plates, and distinguishes between bikes and cars in real-time, even under foggy or low-light conditions.

---

## Tech Stack

- YOLOv8 and PaddleOCR for vehicle and number plate detection
- CLAHE and rotation-based logic for smart OCR retry
- Flask backend for processing
- React frontend with vanilla CSS and dark/light mode
- CSV logging for detection records
- Supports images, videos, and live CCTV streams

---

## Key Features

- Works with low-light, fog, and rain-affected footage
- Accepts uploads and live CCTV feeds
- Automatically enhances input quality before detection
- Tracks each upload using a unique job ID
- Provides previews with plate overlays
- Logs all detections with timestamp, condition, vehicle count, and plate number

---

## File Structure
├── app.py # Flask backend server  
├── main.py # YOLO + OCR processing script  
├── best.pt # YOLOv8 trained weights  
├── requirements.txt # Python dependencies  
├── frontend/ # React frontend app  
├── uploads/ # Uploaded input files  
├── output/ # Annotated results and CSV log  
│ └── vehicle_log.csv # Detection log  
├── temp_input/ # Temporary files per jo

---

## API Endpoints

- POST /api/upload → file upload and job creation
- GET /api/status/<job_id> → job status and output
- GET /api/output/<filename> → fetch annotated file
- GET /api/csv-json → detection log in JSON format
- GET /api/download-csv/<job_id> → download CSV

---

## Setup Instructions

### Backend
```bash
pip install -r requirements.txt
python app.py
```
### Frontend
```bash
cd frontend
npm install
npm start
### Frontend
```
### Model Weights

Make sure the `best.pt` model file (YOLOv8) is placed in the root directory before running `main.py` or `app.py`.

---

## Output Format

Each processed file generates:
- An annotated version (image/video with boxes and labels)
- A log entry in `output/vehicle_log.csv`

### Sample CSV Entry
Video Timestamp, Plates Detected, Vehicle Count, Condition
Image: 4.jpg, MH 14BR 6899, 1, Lowlight

---

## Enhancements Implemented

- **Low-Light Boost:** Improves visibility using CLAHE before running detection
- **Fog/Rain Handling:** Automatically detects poor conditions and adjusts accordingly
- **Smart OCR Retry:** Applies image rotation and contrast enhancement if plate read fails
- **CCTV Stream Support:** Handles RTSP or webcam input for real-time use
- **Dark/Light Mode UI:** Custom toggle in React frontend for better accessibility

---

## Evaluation Highlights

- Real-time detection system ready for production
- Compatible with image uploads, recorded videos, or live camera streams
- Dashboard with previews and downloadable results
- Handles challenging visibility scenarios like fog, rain, and lowlight
- Clean architecture and scalable structure

---

## Future Scope

- Add fog severity classification or traffic congestion estimation
- Deploy on cloud or edge device for smart city integration
- Add admin panel with login and role-based access
- Real-time heatmap of vehicle flow

