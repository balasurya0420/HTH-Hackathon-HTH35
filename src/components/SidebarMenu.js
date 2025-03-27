
// src/components/SidebarMenu.js
import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/components.css';

function SidebarMenu() {
  return (
    <div className="sidebar-menu">
      <div className="sidebar-header">
        <div className="logo-with-text">
          <span className="sidebar-title">RecallMe</span>
        </div>
      </div>
      
      <div className="sidebar-items">
        <Link to="/memories-collection?category=family" className="sidebar-item">
          <div className="sidebar-icon">👪</div>
          <span>Family</span>
        </Link>
        
        <Link to="/memories-collection?category=identify" className="sidebar-item">
          <div className="sidebar-icon">🔍</div>
          <span>Identify</span>
        </Link>
        
        <Link to="/memories-collection?category=photos" className="sidebar-item">
          <div className="sidebar-icon">📷</div>
          <span>Photos</span>
        </Link>
        
        <Link to="/memories-collection?category=unknown" className="sidebar-item">
          <div className="sidebar-icon">❓</div>
          <span>Unknown</span>
        </Link>
      </div>
    </div>
  );
}

export default SidebarMenu;
