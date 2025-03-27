
// src/components/Navbar.js
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/components.css';

function Navbar() {
  const location = useLocation();
  const showMenu = location.pathname !== '/';
  
  return (
    <div className="navbar">
      <div className="navbar-left">
        {showMenu && (
          <>
            <Link to="/add-memory" className="nav-button">Add memory</Link>
            <Link to="/query-memory" className="nav-button">Queries</Link>
          </>
        )}
      </div>
      <div className="logo-container">
        {location.pathname === '/memories-collection' ? (
          <div className="center-logo">
            <span className="recall-text">RECALL ME</span>
          </div>
        ) : (
          <Link to="/">
            <span className="logo-text">MEMORY<span className="vault-text">VAULT</span></span>
          </Link>
        )}
      </div>
      <div className="navbar-right">
        <Link to="/memories-collection" className="recall-button">Recall me</Link>
      </div>
    </div>
  );
}

export default Navbar;
