
// src/components/MemoryBubble.js
import React from 'react';
import '../styles/components.css';

function MemoryBubble({ response }) {
  return (
    <div className="memory-bubble-container">
      <div className="memory-bubble">
        {response.image && (
          <img src={response.image} alt="Memory visualization" className="memory-image" />
        )}
      </div>
      <p className="memory-text">{response.text || "Ask Any Question Related To Your Life so that I can help you feel calm"}</p>
    </div>
  );
}

export default MemoryBubble;
