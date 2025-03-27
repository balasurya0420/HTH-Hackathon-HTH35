
// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './components/HomePage';
import AddMemoryPage from './components/AddMemoryPage';
import QueryMemoryPage from './components/QueryMemoryPage';
import MemoriesCollectionPage from './components/MemoriesCollectionPage';
import Navbar from './components/Navbar';
import './styles/App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <div className="content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/add-memory" element={<AddMemoryPage />} />
            <Route path="/query-memory" element={<QueryMemoryPage />} />
            <Route path="/memories-collection" element={<MemoriesCollectionPage />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;