
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { FaPlay, FaPause, FaVolumeUp, FaVolumeMute, FaRobot, FaTrash, FaSpinner, FaBook, FaHeart } from 'react-icons/fa';

const AudioInteraction = () => {
  const [message, setMessage] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [playingMessageId, setPlayingMessageId] = useState(null);
  const [currentAudioSrc, setCurrentAudioSrc] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [memoryImage, setMemoryImage] = useState(null);
  
  const audioRef = useRef(null);
  const chatContainerRef = useRef(null);
  
  const API_URL = 'http://localhost:8000';

  useEffect(() => {
    loadChatHistory();
    playIntroAudio();
    
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory]);
  
  useEffect(() => {
    if (chatHistory.length > 0) {
      localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    }
  }, [chatHistory]);

  const loadChatHistory = async () => {
    try {
      const savedHistory = localStorage.getItem('chatHistory');
      if (savedHistory) {
        setChatHistory(JSON.parse(savedHistory));
      }
      
      const response = await axios.get(`${API_URL}/get-chat-history`);
      if (response.data.chat_history && response.data.chat_history.length > 0) {
        const historyWithIds = response.data.chat_history.map(msg => ({
          ...msg,
          id: msg.id || Math.random().toString(36).substring(2, 9)
        }));
        setChatHistory(historyWithIds);
        localStorage.setItem('chatHistory', JSON.stringify(historyWithIds));
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const playIntroAudio = async () => {
    try {
      const audioUrl = `${API_URL}/get-intro`;
      setCurrentAudioSrc(audioUrl);
      
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        
        setTimeout(() => {
          audioRef.current.play()
            .then(() => {
              setIsPlaying(true);
              setPlayingMessageId('intro');
            })
            .catch(err => {
              console.error('Failed to play intro audio:', err);
            });
        }, 500);
      }
    } catch (error) {
      console.error('Error playing intro audio:', error);
    }
  };

  const handlePlayMessage = (messageIndex, audioUrl) => {
    const msgId = chatHistory[messageIndex]?.id || `msg-${messageIndex}`;
    
    if (isPlaying && playingMessageId === msgId) {
      if (audioRef.current) {
        audioRef.current.pause();
        setIsPlaying(false);
        setPlayingMessageId(null);
      }
      return;
    }
    
    try {
      if (!audioUrl && chatHistory[messageIndex]?.role === 'assistant') {
        audioUrl = `${API_URL}/get-audio/response_${messageIndex + 1}.mp3`;
      }
      
      if (audioUrl) {
        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          audioRef.current.play()
            .then(() => {
              setIsPlaying(true);
              setPlayingMessageId(msgId);
              setCurrentAudioSrc(audioUrl);
            })
            .catch(err => {
              console.error('Failed to play audio:', err);
            });
        }
      }
    } catch (error) {
      console.error('Error playing message audio:', error);
    }
  };

  const handleGlobalPlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
        setPlayingMessageId(null);
      } else if (currentAudioSrc) {
        audioRef.current.play()
          .then(() => {
            setIsPlaying(true);
          })
          .catch(err => console.error('Failed to play audio:', err));
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const messageTrimmed = message.trim();
    if (!messageTrimmed) return;
    
    setIsLoading(true);
    setIsProcessing(true);
    
    try {
      const messageId = Math.random().toString(36).substring(2, 9);
      const userMessage = { 
        id: messageId,
        role: 'user', 
        content: messageTrimmed, 
        timestamp: new Date().toISOString() 
      };
      setChatHistory(prev => [...prev, userMessage]);
      
      const response = await axios.post(`${API_URL}/text-to-speech`, {
        message: messageTrimmed
      });
      
      if (response.data.chat_history) {
        const historyWithIds = response.data.chat_history.map(msg => ({
          ...msg,
          id: msg.id || Math.random().toString(36).substring(2, 9)
        }));
        setChatHistory(historyWithIds);
      } else if (response.data.reply) {
        const assistantId = Math.random().toString(36).substring(2, 9);
        const assistantMessage = { 
          id: assistantId,
          role: 'assistant', 
          content: response.data.reply, 
          timestamp: new Date().toISOString(),
          audio_url: response.data.file_url
        };
        setChatHistory(prev => [...prev, assistantMessage]);
      }
      
      if (response.data.file_url) {
        const audioUrl = `${API_URL}${response.data.file_url}`;
        setCurrentAudioSrc(audioUrl);
        
        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          
          setTimeout(() => {
            audioRef.current.play()
              .then(() => {
                setIsPlaying(true);
                const lastMessageId = response.data.chat_history ? 
                  response.data.chat_history[response.data.chat_history.length - 1].id || 
                  `msg-${response.data.chat_history.length - 1}` :
                  Math.random().toString(36).substring(2, 9);
                setPlayingMessageId(lastMessageId);
              })
              .catch(err => {
                console.error('Failed to play audio:', err);
              });
          }, 500);
        }
      }
      
      setMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
      setIsProcessing(false);
    }
  };

  const handleGetNarrative = async () => {
    setIsLoading(true);
    
    try {
      const response = await axios.get(`${API_URL}/get-narrative`);
      const chapters = response.data.chapters || [];
      
      // Check if there's an image and save it to state
      if (response.data.memory_image) {
        setMemoryImage(`${API_URL}${response.data.memory_image}`);
      }
      
      // Add chapters to chat history
      if (chapters.length > 0) {
        const narrativeMessages = chapters.map(chapter => ({
          id: Math.random().toString(36).substring(2, 9),
          role: 'narrative',
          content: chapter,
          timestamp: new Date().toISOString()
        }));
        
        setChatHistory(prev => [...prev, ...narrativeMessages]);
      }
    } catch (error) {
      console.error('Error getting narrative:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const clearHistory = async () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      try {
        await axios.post(`${API_URL}/clear-chat-history`);
        setChatHistory([]);
        setMemoryImage(null);
        localStorage.removeItem('chatHistory');
      } catch (error) {
        console.error('Error clearing chat history:', error);
      }
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return '';
    }
  };

  return (
    <div className="audio-interaction-container">
      <div className="chat-container">
        <div className="chat-header">
          <div className="header-content">
            <div className="logo-section">
              <div className="logo-icon">
                <FaHeart className="heart-icon" />
              </div>
              <h2>Memory Companion</h2>
            </div>
            <p>Your AI companion to help you reminisce about life's special moments</p>
          </div>
          
          <div className="header-actions">
            <button 
              className="audio-control-button"
              onClick={handleGlobalPlayPause}
              disabled={!currentAudioSrc}
              title={isPlaying ? "Pause audio" : "Play audio"}
            >
              {isPlaying ? <FaPause /> : <FaPlay />}
            </button>
            
            <button 
              className="clear-button" 
              onClick={clearHistory}
              title="Clear chat history"
            >
              <FaTrash />
            </button>
          </div>
        </div>
        
        <div className="chat-messages" ref={chatContainerRef}>
          {chatHistory.length === 0 ? (
            <div className="welcome-message">
              <div className="welcome-icon-wrapper">
                <FaRobot className="welcome-icon" />
              </div>
              <div className="welcome-text">
                <h3>Hello there!</h3>
                <p>I'm your Memory Companion, here to help you recall and explore your life's special moments. What would you like to talk about today?</p>
              </div>
            </div>
          ) : (
            chatHistory.map((msg, index) => (
              <div key={msg.id || index}>
                <div 
                  className={`message ${msg.role === 'user' ? 'user-message' : msg.role === 'narrative' ? 'narrative-message' : 'ai-message'}`}
                >
                  <div className="message-content">
                    {msg.content}
                  </div>
                  
                  <div className="message-footer">
                    <div className="message-timestamp">
                      {formatTimestamp(msg.timestamp)}
                    </div>
                    
                    {msg.role === 'assistant' && (
                      <button 
                        className={`message-audio-button ${playingMessageId === (msg.id || `msg-${index}`) ? 'playing' : ''}`}
                        onClick={() => handlePlayMessage(index, msg.audio_url)}
                        title={playingMessageId === (msg.id || `msg-${index}`) ? "Pause" : "Play message"}
                      >
                        {playingMessageId === (msg.id || `msg-${index}`) ? <FaVolumeMute /> : <FaVolumeUp />}
                      </button>
                    )}
                  </div>
                </div>
                
                {msg.role === 'narrative' && index === chatHistory.findIndex(m => m.role === 'narrative') && memoryImage && (
                  <div className="memory-image-container">
                    <img 
                      src={memoryImage} 
                      alt="Generated memory visualization" 
                      className="memory-image" 
                    />
                    <p className="memory-image-caption">A visual representation of your memories</p>
                  </div>
                )}
              </div>
            ))
          )}
          
          {isProcessing && (
            <div className="loading-indicator">
              <div className="loading-dots">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
        </div>
        
        <audio 
          ref={audioRef} 
          onEnded={() => {
            setIsPlaying(false);
            setPlayingMessageId(null);
          }}
          onError={(e) => console.error('Audio error:', e)}
          style={{ display: 'none' }}
        />
        
        <form className="message-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Share a memory or ask a question..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={isLoading}
            className="message-input"
          />
          <button 
            type="submit" 
            disabled={isLoading || !message.trim()}
            className="send-button"
          >
            {isLoading ? <FaSpinner className="spinner" /> : 'Send'}
          </button>
        </form>
        
        {chatHistory.length >= 3 && (
          <div className="narrative-section">
            <button 
              className="narrative-button"
              onClick={handleGetNarrative}
              disabled={isLoading}
            >
              <FaBook className="narrative-icon" />
              <span>Generate My Memory Story</span>
            </button>
          </div>
        )}
      </div>
      
      <style jsx>{`
        .audio-interaction-container {
          width: 100%;
          height: 100vh;
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 0;
          margin: 0;
          background-color: #e6f0ef;
          font-family: 'Poppins', sans-serif;
          overflow: hidden;
        }
        
        .chat-container {
          width: 1200px;
          max-width: 95%;
          background: #ffffff;
          border-radius: 24px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
          overflow: hidden;
          display: flex;
          flex-direction: column;
          height: 95vh;
          position: relative;
          border: 1px solid #f0f0f0;
        }
        
        .chat-header {
          padding: 25px 30px;
          background: linear-gradient(120deg, #f8bdff, #c1a1ff);
          color: #39257a;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .header-content {
          flex: 1;
        }
        
        .logo-section {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
        }
        
        .logo-icon {
          width: 40px;
          height: 40px;
          background: rgba(255, 255, 255, 0.3);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 15px;
        }
        
        .heart-icon {
          color: #ff6596;
          font-size: 22px;
        }
        
        .chat-header h2 {
          margin: 0;
          font-size: 26px;
          font-weight: 700;
          background: linear-gradient(120deg, #5e2f84, #2f3a8f);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        
        .chat-header p {
          margin: 0;
          font-size: 14px;
          color: #4a3583;
          opacity: 0.9;
        }
        
        .header-actions {
          display: flex;
          gap: 15px;
        }
        
        .audio-control-button, .clear-button {
          background: rgba(255, 255, 255, 0.3);
          border: none;
          color: #39257a;
          width: 40px;
          height: 40px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 16px;
        }
        
        .audio-control-button:hover:not(:disabled), .clear-button:hover {
          background: rgba(255, 255, 255, 0.5);
          transform: translateY(-2px);
        }
        
        .audio-control-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .clear-button {
          color: #b33c7e;
        }
        
        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 30px;
          display: flex;
          flex-direction: column;
          gap: 20px;
          scroll-behavior: smooth;
          background-color: #fcfbff;
        }
        
        .welcome-message {
          display: flex;
          align-items: flex-start;
          background: linear-gradient(120deg, #f1e7ff, #e7f0ff);
          border-radius: 20px;
          padding: 25px;
          margin-bottom: 20px;
          box-shadow: 0 5px 15px rgba(160, 113, 255, 0.1);
          animation: fadeIn 0.5s ease-out;
        }
        
        .welcome-icon-wrapper {
          background: linear-gradient(120deg, #a071ff, #7e95ff);
          width: 60px;
          height: 60px;
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 20px;
          flex-shrink: 0;
        }
        
        .welcome-icon {
          font-size: 30px;
          color: white;
        }
        
        .welcome-text h3 {
          margin: 0 0 10px 0;
          color: #39257a;
          font-size: 20px;
        }
        
        .welcome-text p {
          margin: 0;
          color: #5a4895;
          line-height: 1.6;
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(15px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        .message {
          max-width: 85%;
          padding: 20px 24px;
          border-radius: 20px;
          position: relative;
          margin-bottom: 8px;
          animation: fadeIn 0.3s ease-out;
          box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
        }
        
        .user-message {
          align-self: flex-end;
          background: linear-gradient(120deg, #9c42a1, #6e3cbc);
          color: white;
          border-bottom-right-radius: 5px;
          margin-left: auto;
        }
        
        .ai-message {
          align-self: flex-start;
          background: linear-gradient(120deg, #f8f9ff, #eef1ff);
          color: #39257a;
          border-bottom-left-radius: 5px;
          border-left: 4px solid #c1a1ff;
        }
        
        .narrative-message {
          align-self: center;
          background: linear-gradient(120deg, #fff8e1, #fffbe7);
          color: #5d4037;
          border-radius: 16px;
          border-left: 4px solid #ffc107;
          width: 92%;
          font-style: italic;
          box-shadow: 0 5px 15px rgba(255, 193, 7, 0.1);
          font-size: 16px;
        }
        
        .message-content {
          line-height: 1.6;
          word-wrap: break-word;
          font-size: 16px;
        }
        
        .message-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 10px;
        }
        
        .message-timestamp {
          font-size: 12px;
          opacity: 0.7;
        }
        
        .message-audio-button {
          background: none;
          border: none;
          color: #a071ff;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 6px;
          border-radius: 50%;
          transition: all 0.2s;
          opacity: 0.7;
        }
        
        .message-audio-button:hover {
          background: rgba(160, 113, 255, 0.1);
          opacity: 1;
        }
        
        .message-audio-button.playing {
          color: #ff6596;
          animation: pulse 1.5s infinite;
          opacity: 1;
        }
        
        .memory-image-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          margin: 10px 0 30px;
          max-width: 100%;
          animation: fadeIn 1s ease-out;
        }
        
        .memory-image {
          max-width: 100%;
          width: auto;
          max-height: 400px;
          border-radius: 16px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
          border: 4px solid white;
        }
        
        .memory-image-caption {
          margin-top: 12px;
          font-size: 14px;
          color: #777;
          font-style: italic;
        }
        
        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.2);
          }
        }
        
        .loading-indicator {
          align-self: center;
          margin: 20px 0;
        }
        
        .loading-dots {
          display: flex;
          gap: 8px;
        }
        
        .dot {
          width: 10px;
          height: 10px;
          background: linear-gradient(120deg, #a071ff, #7e95ff);
          border-radius: 50%;
          animation: bounce 1.5s infinite ease-in-out;
        }
        
        .dot:nth-child(1) {
          animation-delay: 0s;
        }
        
        .dot:nth-child(2) {
          animation-delay: 0.2s;
        }
        
        .dot:nth-child(3) {
          animation-delay: 0.4s;
        }
        
        @keyframes bounce {
          0%, 80%, 100% {
            transform: translateY(0);
          }
          40% {
            transform: translateY(-10px);
          }
        }
        
        .message-form {
          display: flex;
          padding: 20px 25px;
          background: #fcfbff;
          border-top: 1px solid #f0f0f0;
        }
        
        .message-input {
          flex: 1;
          padding: 18px 24px;
          border: 2px solid #eaeaea;
          border-radius: 30px;
          font-size: 16px;
          outline: none;
          transition: all 0.3s;
          background: white;
          color: #39257a;
        }
        
        .message-input:focus {
          border-color: #c1a1ff;
          box-shadow: 0 0 0 3px rgba(193, 161, 255, 0.2);
        }
        
        .message-input::placeholder {
          color: #a8a8a8;
        }
        
        .send-button {
          background: linear-gradient(120deg, #a071ff, #7e95ff);
          color: white;
          border: none;
          padding: 0 25px;
          margin-left: 15px;
          border-radius: 30px;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.3s;
          display: flex;
          justify-content: center;
          align-items: center;
          min-width: 100px;
          box-shadow: 0 4px 12px rgba(126, 149, 255, 0.2);
        }
        
        .send-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 6px 15px rgba(126, 149, 255, 0.3);
        }
        
        .send-button:disabled {
          background: #e0e0e0;
          cursor: not-allowed;
          box-shadow: none;
        }
        
        .spinner {
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        .narrative-section {
          padding: 15px 30px 20px;
          display: flex;
          justify-content: center;
          background: #fcfbff;
        }
        
        .narrative-button {
          background: linear-gradient(120deg, #ffd16b, #ffaa6b);
          color: #774c00;
          border: none;
          padding: 16px 35px;
          border-radius: 30px;
          font-weight: 600;
          font-size: 16px;
          cursor: pointer;
          transition: all 0.3s;
          box-shadow: 0 4px 15px rgba(255, 170, 107, 0.2);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
        }
        
        .narrative-icon {
          font-size: 18px;
        }
        
        .narrative-button:hover:not(:disabled) {
          transform: translateY(-3px);
          box-shadow: 0 6px 20px rgba(255, 170, 107, 0.3);
        }
        
        .narrative-button:disabled {
          background: #e0e0e0;
          cursor: not-allowed;
          box-shadow: none;
        }
        
        @media (max-width: 768px) {
          .chat-container {
            height: 100vh;
            max-width: 100%;
            border-radius: 0;
          }
          
          .chat-header {
            padding: 15px 20px;
          }
          
          .welcome-message {
            flex-direction: column;
            align-items: center;
            text-align: center;
          }
          
          .welcome-icon-wrapper {
            margin-right: 0;
            margin-bottom: 15px;
          }
          
          .message {
            max-width: 90%;
            padding: 16px 20px;
          }
          
          .message-form {
            padding: 15px;
          }
          
          .message-input {
            padding: 12px 18px;
          }
          
          .send-button {
            padding: 0 20px;
            min-width: 80px;
          }
          
          .narrative-button {
            padding: 14px 25px;
            font-size: 15px;
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
};

export default AudioInteraction;
