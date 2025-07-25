import React, { useState } from 'react';
import axios from 'axios';
import './UploadForm.css';

const UploadForm = ({ onFileProcessed }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadQueue, setUploadQueue] = useState([]);
  const [streamURL, setStreamURL] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    setUploadQueue(selectedFiles.map(file => ({ name: file.name, status: 'pending' })));

    for (let file of selectedFiles) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await axios.post('/api/upload', formData);
        const jobId = res.data.job_id;
        setUploadQueue(prev =>
          prev.map(f =>
            f.name === file.name ? { ...f, status: 'processing' } : f
          )
        );
        // Poll for job status
        let status = 'processing';
        let outputFile = null;
        while (status === 'processing') {
          await new Promise(r => setTimeout(r, 1500));
          const statusRes = await axios.get(`/api/status/${jobId}`);
          status = statusRes.data.status;
          if (status === 'completed') {
            outputFile = statusRes.data.output_image || statusRes.data.output_video;
            break;
          } else if (status === 'failed' || status === 'timeout' || status === 'error') {
            break;
          }
        }
        if (outputFile) {
          onFileProcessed(outputFile);
          setUploadQueue(prev =>
            prev.map(f =>
              f.name === file.name ? { ...f, status: 'done' } : f
            )
          );
        } else {
          setUploadQueue(prev =>
            prev.map(f =>
              f.name === file.name ? { ...f, status: 'error' } : f
            )
          );
        }
      } catch (err) {
        console.error(err);
        setUploadQueue(prev =>
          prev.map(f =>
            f.name === file.name ? { ...f, status: 'error' } : f
          )
        );
      }
    }

    setSelectedFiles([]);
    setUploading(false);
  };

  const handleCCTVSubmit = async () => {
    if (!streamURL.trim()) return;

    try {
      const res = await axios.post('/api/cctv', { stream_url: streamURL });
      alert(res.data.message);
    } catch (err) {
      alert('CCTV processing failed!');
      console.error(err);
    }
  };

  return (
    <div className="upload-form">
      <h2>🎯 Upload Image / Video Batch</h2>
      <input
        type="file"
        multiple
        accept="video/*,image/*"
        onChange={handleFileChange}
      />
      <button onClick={handleUpload} disabled={uploading}>
        {uploading ? 'Uploading...' : 'Upload & Detect'}
      </button>

      {uploadQueue.length > 0 && (
        <div className="upload-status">
          <h4>📦 Upload Queue:</h4>
          <ul>
            {uploadQueue.map((f, idx) => (
              <li key={idx} className={`status ${f.status}`}>
                {f.name} — {f.status}
              </li>
            ))}
          </ul>
        </div>
      )}

      <h3>📹 CCTV Stream URL</h3>
      <input
        type="text"
        placeholder="rtsp:// or http:// link"
        value={streamURL}
        onChange={(e) => setStreamURL(e.target.value)}
      />
      <button onClick={handleCCTVSubmit}>Submit Stream</button>
    </div>
  );
};

export default UploadForm;
