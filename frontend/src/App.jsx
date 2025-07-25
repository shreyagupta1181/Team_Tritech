import React, { useState, useEffect } from 'react';
import UploadForm from './components/UploadForm';
import PreviewGallery from './components/PreviewGallery';
import ThemeToggle from './components/ThemeToggle';
import CsvTable from './components/CsvTable';
import axios from 'axios';
import './App.css';

const App = () => {
  const [theme, setTheme] = useState('light');
  const [outputFiles, setOutputFiles] = useState([]); // [{ fileName, csvData }]
  const [csvData, setCsvData] = useState([]);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  // Function to reload CSV data
  const reloadCsvData = async () => {
    try {
      const res = await axios.get('/api/csv-json');
      setCsvData(res.data);
    } catch (err) {
      setCsvData([]);
    }
  };

  // Load CSV data on mount
  useEffect(() => {
    reloadCsvData();
  }, []);

  // After each upload, reload CSV data
  const addOutputFile = (fileName) => {
    setOutputFiles((prev) => [...prev, fileName]);
    reloadCsvData();
  };

  // Remove an output file from the gallery
  const removeOutputFile = (fileName) => {
    setOutputFiles((prev) => prev.filter(f => f !== fileName));
  };

  return (
    <div className={`app ${theme}`}>
      <header className="header">
        <h1>🚘 Smart Vehicle Detection</h1>
        <ThemeToggle onToggle={toggleTheme} currentTheme={theme} />
      </header>

      <main>
        <UploadForm onFileProcessed={addOutputFile} />
        {outputFiles.length > 0 && <PreviewGallery files={outputFiles} onRemove={removeOutputFile} />}
        <CsvTable csvData={csvData} reloadCsvData={reloadCsvData} />
      </main>
    </div>
  );
};

export default App;
