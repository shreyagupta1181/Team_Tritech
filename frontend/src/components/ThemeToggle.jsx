import React from 'react';
import './ThemeToggle.css';

const ThemeToggle = ({ onToggle, currentTheme }) => {
  return (
    <button className="theme-toggle" onClick={onToggle}>
      {currentTheme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
    </button>
  );
};

export default ThemeToggle;
