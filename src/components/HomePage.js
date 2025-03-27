
// src/components/HomePage.js
import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/components.css';

function HomePage() {
  return (
    <div className="home-container">
      <div className="memory-card">
        <h2 className="memory-title">PRESERVING PRECIOUS MEMORIES</h2>
        <div className="memory-images">
          <div 
            className="memory-image-circle"
            style={{
              backgroundImage: `url('/sample-images/memory1.jpg')`,
              zIndex: 3,
              left: '20%'
            }}
          />
          <div 
            className="memory-image-circle"
            style={{
              backgroundImage: `url('/sample-images/memory2.jpg')`,
              zIndex: 2,
              left: '40%'
            }}
          />
          <div 
            className="memory-image-circle"
            style={{
              backgroundImage: `url('/sample-images/memory3.jpg')`,
              zIndex: 1,
              left: '60%'
            }}
          />
        </div>
      </div>
      <div className="home-buttons">
        <Link to="/add-memory" className="home-button">Add a New Memory</Link>
        <Link to="/memories-collection" className="home-button">Relive memories</Link>
      </div>
    </div>
  );
}

export default HomePage;