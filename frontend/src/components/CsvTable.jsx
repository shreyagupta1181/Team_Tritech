import React from 'react';

const CsvTable = ({ csvData }) => {
  if (!csvData || !csvData.length) return <div>No CSV data available.</div>;

  return (
    <div style={{ margin: '2rem 0' }}>
      <h2>📋 All Detected Vehicles (CSV Log)</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {Object.keys(csvData[0]).map((col, i) => (
              <th key={i} style={{ border: '1px solid #ccc', padding: '0.5rem', background: '#f8f8f8' }}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {csvData.map((row, i) => (
            <tr key={i}>
              {Object.values(row).map((val, j) => (
                <td key={j} style={{ border: '1px solid #ccc', padding: '0.5rem' }}>{val}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CsvTable; 