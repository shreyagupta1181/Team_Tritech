import React from 'react';
import './PreviewGallery.css';

const PreviewGallery = ({ files, onRemove }) => {
  if (!files.length) return null;

  return (
    <div className="preview-gallery">
      <h2>🖼️ Processed Output Preview</h2>
      <div className="gallery-grid">
        {files.map((fileName, idx) => {
          if (typeof fileName !== 'string') return null;
          const isVideo = fileName.match(/\.(mp4|avi|mov|mkv)$/i);
          const isImage = fileName.match(/\.(jpg|jpeg|png)$/i);
          const backendUrl = 'http://localhost:5000'; 
          const fileURL = `${backendUrl}/api/output/${fileName}`;

          return (
            <div key={idx} className="preview-card">
              <button
                className="close-btn"
                style={{ position: 'absolute', top: 8, right: 12, background: 'transparent', border: 'none', fontSize: '1.3rem', cursor: 'pointer', color: '#888' }}
                title="Close"
                onClick={() => onRemove && onRemove(fileName)}
              >
                ×
              </button>
              <p className="file-name">{fileName}</p>
              {isVideo ? (
                <video controls>
                  <source src={fileURL} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              ) : isImage ? (
                <img src={fileURL} alt={fileName} />
              ) : (
                <p>Unsupported</p>
              )}
              <a className="download-btn" href={fileURL} download>
                ⬇ Download
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PreviewGallery;
