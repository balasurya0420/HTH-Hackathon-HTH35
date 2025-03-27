
// src/components/QueryMemoryPage.js
import React, { useState } from 'react';
import MemoryBubble from './MemoryBubble';
import '../styles/components.css';
import { useNavigate } from 'react-router-dom';

function QueryMemoryPage() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState({ text: '', image: null });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch(`http://localhost:8080/query?query=${encodeURIComponent(query)}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch memory');
      }
      
      const data = await response.json();
      setResponse(data);
      setQuery('');
    } catch (err) {
      setError(err.message);
      setResponse({ text: 'Sorry, I had trouble retrieving that memory.', image: null });
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewMemory = () => {
    navigate('/add-memory');
  };

  return (
    <div className="query-memory-container">
      <div className="sidebar">
        <button className="new-memory-button" onClick={handleNewMemory}>+ New Memory</button>
      </div>
      <div className="memory-content">
        <MemoryBubble response={response} />
        
        <form onSubmit={handleSubmit} className="query-form">
          <input
            type="text"
            className="query-input"
            placeholder="Ask about your memories..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="submit-arrow">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default QueryMemoryPage;