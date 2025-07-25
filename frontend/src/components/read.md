# [Your Official Team Name Here]

## Team Members

- **Full Name 1** — email1@example.com
- **Full Name 2** — email2@example.com
- **Full Name 3** — email3@example.com
- *(Add/remove as needed)*

---

## Assigned Problem Statement

*Vehicle Detection and License Plate Recognition Web Application*  
(Replace this with your exact assigned problem statement if different.)

---

## Quick Start Guide

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/your-team-repo.git
cd your-team-repo
```

### 2. Backend Setup

- **Install Python dependencies:**
  ```bash
  pip install -r requirements.txt
  ```
  *requirements.txt includes: ultralytics==8.3.144, paddleocr==2.10.0, paddlepaddle==3.0.0, opencv-python, numpy, Pillow, flask, werkzeug*
- **Ensure you have the YOLOv8 weights file (`best.pt`) in the project root.**
- **Start the backend server:**
  ```bash
  python app.py
  ```
  The backend will run on [http://localhost:5000](http://localhost:5000).

### 3. Frontend Setup

- **Install Node.js dependencies:**
  ```bash
  cd frontend
  npm install
  ```
- **Start the React frontend:**
  ```bash
  npm start
  ```
  The frontend will run on [http://localhost:3000](http://localhost:3000).

### 4. Usage Example

- Open [http://localhost:3000](http://localhost:3000) in your browser.
- Upload images or videos for vehicle and license plate detection.
- View processed results in the gallery and download annotated outputs.
- See all detection results in the live CSV log table at the bottom of the page.

---

## Project Structure

```
.
├── app.py              # Flask backend server
├── main.py             # AI processing script (YOLOv8 + PaddleOCR)
├── requirements.txt    # Python dependencies
├── best.pt             # YOLOv8 model weights
├── frontend/           # React frontend app
├── uploads/            # Uploaded files
├── output/             # Processed files and CSV log
├── temp_input/         # Temporary job folders
└── ...
```

---

## API Endpoints

- `POST /api/upload` — Upload a file for processing
- `GET /api/status/<job_id>` — Poll for job status/results
- `GET /api/output/<filename>` — Download/view processed output
- `GET /api/csv-json` — Fetch CSV log as JSON for frontend table

---

## Additional Notes

- All code, documentation, and related work are committed to this repository.
- Please refer to commit history for collaboration and progress tracking.
- For any issues, contact the team members listed above.

---

*Make sure to rename your forked repository to your official team name before submission!*

---

**You can now copy and save this as `README.md` in your project root.**  
If you want me to make any edits or add more details, just let me know!
