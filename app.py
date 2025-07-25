from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import subprocess
import threading
import json
import csv
import io
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import logging
from PIL import Image
import base64

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', 'output')
TEMP_INPUT_FOLDER = os.environ.get('TEMP_INPUT_FOLDER', 'temp_input')
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}

# Ensure directories exist
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, TEMP_INPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Job tracking
active_jobs = {}
job_results = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_image_file(filename):
    return filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

def is_video_file(filename):
    return filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov', 'mkv'}

def image_to_base64(image_path):
    """Convert image to base64 for preview"""
    try:
        with Image.open(image_path) as img:
            # Resize for preview (max 800px width)
            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Save to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        return None

def parse_csv_results(csv_path):
    """Parse the CSV file and return structured data"""
    results = []
    try:
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                results.append({
                    'timestamp': row.get('Video Timestamp', ''),
                    'plates': row.get('Plates Detected', ''),
                    'vehicle_count': int(row.get('Vehicle Count', 0)),
                    'condition': row.get('Condition', '')
                })
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
    return results

def process_file_async(job_id, input_path, filename):
    """Process file in background thread"""
    try:
        logger.info(f"[JOB {job_id}] Starting process_file_async for file: {filename}")
        active_jobs[job_id] = {
            'status': 'processing',
            'started_at': datetime.now(),
            'filename': filename,
            'progress': 'Starting detection...'
        }
        
        # Update progress
        active_jobs[job_id]['progress'] = 'Running vehicle detection...'
        
        # Create a temporary input directory for this job
        job_input_dir = os.path.join(TEMP_INPUT_FOLDER, job_id)
        os.makedirs(job_input_dir, exist_ok=True)
        logger.info(f"[JOB {job_id}] Created job input dir: {job_input_dir}")
        
        # Copy file to job input directory
        job_input_path = os.path.join(job_input_dir, filename)
        os.rename(input_path, job_input_path)
        logger.info(f"[JOB {job_id}] Moved input file to: {job_input_path}")
        
        # Run detection (modify main.py to accept custom input/output dirs)
        env = os.environ.copy()
        env['INPUT_DIR'] = job_input_dir
        env['OUTPUT_DIR'] = OUTPUT_FOLDER
        logger.info(f"[JOB {job_id}] Running main.py with INPUT_DIR={job_input_dir} OUTPUT_DIR={OUTPUT_FOLDER}")
        
        result = subprocess.run(
            ['python', 'main.py'],
            capture_output=True,
            text=True,
            timeout=6000,
            env=env
        )
        logger.info(f"[JOB {job_id}] main.py finished with return code {result.returncode}")
        logger.info(f"[JOB {job_id}] main.py stdout: {result.stdout}")
        logger.info(f"[JOB {job_id}] main.py stderr: {result.stderr}")
        
        if result.returncode == 0:
            active_jobs[job_id]['progress'] = 'Processing complete, generating preview...'
            
            # Determine output files
            output_image_path = None
            output_video_path = None
            csv_path = os.path.join(OUTPUT_FOLDER, "vehicle_log.csv")
            
            if is_image_file(filename):
                output_image_path = os.path.join(OUTPUT_FOLDER, f"annotated_{filename}")
            elif is_video_file(filename):
                output_video_path = os.path.join(OUTPUT_FOLDER, f"annotated_{filename}")
                # For videos, we'll extract a frame for preview
                # You might want to modify main.py to also output a preview frame
            
            # Parse CSV results
            csv_data = parse_csv_results(csv_path)
            
            # Generate preview
            preview_image = None
            if output_image_path and os.path.exists(output_image_path):
                preview_image = image_to_base64(output_image_path)
            
            job_results[job_id] = {
                'status': 'completed',
                'completed_at': datetime.now(),
                'filename': filename,
                'file_type': 'image' if is_image_file(filename) else 'video',
                'output_image': f"annotated_{filename}" if output_image_path else None,
                'output_video': f"annotated_{filename}" if output_video_path else None,
                'preview_image': preview_image,
                'csv_data': csv_data,
                'total_vehicles': len(csv_data),
                'stdout': result.stdout
            }
        else:
            job_results[job_id] = {
                'status': 'failed',
                'error': result.stderr,
                'completed_at': datetime.now(),
                'filename': filename
            }
        
        # Cleanup temp directory
        import shutil
        shutil.rmtree(job_input_dir, ignore_errors=True)
            
    except subprocess.TimeoutExpired:
        logger.error(f"[JOB {job_id}] main.py timed out.")
        job_results[job_id] = {
            'status': 'timeout',
            'error': 'Processing timeout exceeded',
            'completed_at': datetime.now(),
            'filename': filename
        }
    except Exception as e:
        logger.error(f"[JOB {job_id}] Exception in process_file_async: {e}")
        job_results[job_id] = {
            'status': 'error',
            'error': str(e),
            'completed_at': datetime.now(),
            'filename': filename
        }
    finally:
        logger.info(f"[JOB {job_id}] Finished process_file_async.")
        # Clean up active job
        active_jobs.pop(job_id, None)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': 'File type not allowed',
            'allowed_types': list(ALLOWED_EXTENSIONS)
        }), 400
    
    try:
        # Generate unique job ID and filename
        job_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        
        # Save file
        input_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(input_path)
        
        # Start background processing
        thread = threading.Thread(
            target=process_file_async,
            args=(job_id, input_path, filename)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started processing job {job_id} for file {filename}")
        
        return jsonify({
            'job_id': job_id,
            'filename': filename,
            'message': 'File uploaded and processing started',
            'status': 'processing'
        }), 202
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    # Check if job is still active
    if job_id in active_jobs:
        job = active_jobs[job_id]
        processing_time = datetime.now() - job['started_at']
        return jsonify({
            'job_id': job_id,
            'status': job['status'],
            'filename': job['filename'],
            'progress': job.get('progress', 'Processing...'),
            'started_at': job['started_at'].isoformat(),
            'processing_time': str(processing_time).split('.')[0]  # Remove microseconds
        })
    
    # Check if job is completed
    if job_id in job_results:
        result = job_results[job_id]
        response = {
            'job_id': job_id,
            'status': result['status'],
            'filename': result['filename'],
            'completed_at': result['completed_at'].isoformat()
        }
        
        if result['status'] == 'completed':
            response.update({
                'file_type': result['file_type'],
                'output_image': result.get('output_image'),
                'output_video': result.get('output_video'),
                'preview_image': result.get('preview_image'),
                'csv_data': result['csv_data'],
                'total_vehicles': result['total_vehicles']
            })
        elif result['status'] in ['failed', 'timeout', 'error']:
            response['error'] = result['error']
            
        return jsonify(response)
    
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/output/<filename>', methods=['GET'])
def get_output(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

@app.route('/api/download-csv/<job_id>', methods=['GET'])
def download_csv(job_id):
    """Download CSV data for a specific job"""
    if job_id not in job_results:
        return jsonify({'error': 'Job not found'}), 404
    
    result = job_results[job_id]
    if result['status'] != 'completed':
        return jsonify({'error': 'Job not completed'}), 400
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Timestamp', 'License Plates', 'Vehicle Count', 'Condition'])
    
    # Write data
    for row in result['csv_data']:
        writer.writerow([
            row['timestamp'],
            row['plates'],
            row['vehicle_count'],
            row['condition']
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    # Return as downloadable file
    from flask import Response
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={result["filename"]}_results.csv'
        }
    )


@app.route('/api/csv-json', methods=['GET'])
def csv_as_json():
    import csv
    csv_path = os.path.join(OUTPUT_FOLDER, "vehicle_log.csv")
    data = []
    if os.path.exists(csv_path):
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
    return jsonify(data)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'active_jobs': len(active_jobs),
        'completed_jobs': len(job_results),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)