
// src/components/AddMemoryPage.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/components.css';

function AddMemoryPage() {
  const [memory, setMemory] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!memory.trim()) {
      setError('Please enter a memory');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8080/postMemory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: memory,
          metadata: {
            timestamp: new Date().toISOString(),
          },
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to save memory');
      }
      
      setMemory('');
      navigate('/memories-collection');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const currentDate = new Date();
  const formattedDate = `${currentDate.toLocaleDateString()} - ${currentDate.toLocaleTimeString()}`;

  return (
    <div className="memory-journal-container">
      <div className="journal-page">
        <div className="journal-binding">
          {Array(12).fill().map((_, i) => (
            <div key={i} className="binding-ring"></div>
          ))}
        </div>
        <div className="journal-content">
          <h2 className="journal-title">Memory Journal</h2>
          <p className="journal-date">{formattedDate}</p>
          
          <form onSubmit={handleSubmit}>
            <textarea
              className="memory-textarea"
              placeholder="Write your memory here..."
              value={memory}
              onChange={(e) => setMemory(e.target.value)}
              rows={10}
            />
            
            {error && <p className="error-message">{error}</p>}
            
            <button 
              type="submit" 
              className="preserve-button"
              disabled={isLoading}
            >
              {isLoading ? 'Saving...' : 'Preserve this Memory'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AddMemoryPage;