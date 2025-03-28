// import React, { useState, useRef, useEffect } from 'react';
// import axios from 'axios';
// import { FaMicrophone, FaStop, FaPlay, FaPause, FaVolumeUp, FaRobot } from 'react-icons/fa';

// const AudioInteraction = () => {
//   const [message, setMessage] = useState('');
//   const [isRecording, setIsRecording] = useState(false);
//   const [isPlaying, setIsPlaying] = useState(false);
//   const [aiResponse, setAiResponse] = useState('');
//   const [isLoading, setIsLoading] = useState(false);
//   const [chatHistory, setChatHistory] = useState([]);
//   const [audioSrc, setAudioSrc] = useState('');
  
//   const audioRef = useRef(null);
//   const mediaRecorderRef = useRef(null);
//   const audioChunksRef = useRef([]);

//   const API_URL = 'http://localhost:5000';

//   useEffect(() => {
//     // Load intro audio when component mounts
//     playIntroAudio();
    
//     // Clean up audio resources when component unmounts
//     return () => {
//       if (audioRef.current) {
//         audioRef.current.pause();
//         audioRef.current.src = '';
//       }
//     };
//   }, []);

//   const playIntroAudio = async () => {
//     try {
//       const audioUrl = `${API_URL}/get-intro`;
//       setAudioSrc(audioUrl);
      
//       // Wait a bit before playing to ensure audio is loaded
//       setTimeout(() => {
//         if (audioRef.current) {
//           audioRef.current.play()
//             .then(() => {
//               setIsPlaying(true);
//             })
//             .catch(err => {
//               console.error('Failed to play intro audio:', err);
//             });
//         }
//       }, 1000);
//     } catch (error) {
//       console.error('Error playing intro audio:', error);
//     }
//   };

//   const startRecording = async () => {
//     try {
//       const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//       mediaRecorderRef.current = new MediaRecorder(stream);
//       audioChunksRef.current = [];

//       mediaRecorderRef.current.ondataavailable = (event) => {
//         if (event.data.size > 0) {
//           audioChunksRef.current.push(event.data);
//         }
//       };

//       mediaRecorderRef.current.onstop = () => {
//         const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
//         const audioUrl = URL.createObjectURL(audioBlob);
        
//         // Here you would normally send this audio to your speech-to-text service
//         // For now, we'll just use the text input
//       };

//       mediaRecorderRef.current.start();
//       setIsRecording(true);
//     } catch (error) {
//       console.error('Error starting recording:', error);
//     }
//   };

//   const stopRecording = () => {
//     if (mediaRecorderRef.current && isRecording) {
//       mediaRecorderRef.current.stop();
//       setIsRecording(false);
      
//       // Stop all audio tracks
//       if (mediaRecorderRef.current.stream) {
//         mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
//       }
//     }
//   };

//   const handlePlayPause = () => {
//     if (audioRef.current) {
//       if (isPlaying) {
//         audioRef.current.pause();
//       } else {
//         audioRef.current.play()
//           .catch(err => console.error('Failed to play audio:', err));
//       }
//       setIsPlaying(!isPlaying);
//     }
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();
    
//     if (!message.trim()) return;
    
//     // Add user message to chat history
//     const userMessage = { role: 'user', content: message };
//     setChatHistory(prev => [...prev, userMessage]);
    
//     setIsLoading(true);
    
//     try {
//       // Send message to the backend
//       const response = await axios.post(`${API_URL}/text-to-speech`, {
//         message: message
//       });
      
//       // Update AI response
//       setAiResponse(response.data.reply);
      
//       // Add AI response to chat history
//       const aiMessage = { role: 'assistant', content: response.data.reply };
//       setChatHistory(prev => [...prev, aiMessage]);
      
//       // Set the audio source to the returned URL
//       setAudioSrc(`${API_URL}/get-audio?${new Date().getTime()}`); // Add timestamp to prevent caching
      
//       // Play the audio after a short delay to ensure it's loaded
//       setTimeout(() => {
//         if (audioRef.current) {
//           audioRef.current.play()
//             .then(() => {
//               setIsPlaying(true);
//             })
//             .catch(err => {
//               console.error('Failed to play audio:', err);
//             });
//         }
//       }, 1000);
      
//       // Clear the input field
//       setMessage('');
//     } catch (error) {
//       console.error('Error sending message:', error);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const handleGetNarrative = async () => {
//     setIsLoading(true);
    
//     try {
//       const response = await axios.get(`${API_URL}/get-narrative`);
//       const chapters = response.data.chapters;
      
//       // Process chapters as needed
//       setAiResponse("Your personal narrative has been generated!");
      
//       // Add chapters to chat history
//       chapters.forEach(chapter => {
//         if (chapter.trim()) {
//           const chapterMessage = { role: 'narrative', content: chapter.trim() };
//           setChatHistory(prev => [...prev, chapterMessage]);
//         }
//       });
//     } catch (error) {
//       console.error('Error getting narrative:', error);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   return (
//     <div className="audio-interaction-container">
//       <div className="chat-container">
//         <div className="chat-header">
//           <h2>Memory Companion</h2>
//           <p>Chat with your AI companion to reminisce about your memories</p>
//         </div>
        
//         <div className="chat-messages">
//           {chatHistory.length === 0 ? (
//             <div className="welcome-message">
//               <FaRobot className="welcome-icon" />
//               <p>Hello! I'm here to help you recall memories and meaningful moments from your life. Feel free to tell me about a memory, and I'll help you explore it further.</p>
//             </div>
//           ) : (
//             chatHistory.map((msg, index) => (
//               <div key={index} className={`message ${msg.role === 'user' ? 'user-message' : msg.role === 'narrative' ? 'narrative-message' : 'ai-message'}`}>
//                 <div className="message-content">
//                   {msg.content}
//                 </div>
//               </div>
//             ))
//           )}
          
//           {isLoading && (
//             <div className="loading-indicator">
//               <div className="loading-dots">
//                 <div className="dot"></div>
//                 <div className="dot"></div>
//                 <div className="dot"></div>
//               </div>
//             </div>
//           )}
//         </div>
        
//         <div className="audio-controls">
//           <div className="audio-player">
//             <audio 
//               ref={audioRef} 
//               src={audioSrc} 
//               onEnded={() => setIsPlaying(false)}
//               onError={(e) => console.error('Audio error:', e)}
//             />
            
//             <button 
//               className={`play-button ${isPlaying ? 'playing' : ''}`}
//               onClick={handlePlayPause}
//               disabled={!audioSrc}
//             >
//               {isPlaying ? <FaPause /> : <FaPlay />}
//             </button>
            
//             <div className="volume-indicator">
//               <FaVolumeUp className={isPlaying ? 'active' : ''} />
//             </div>
//           </div>
          
//           <button 
//             className={`record-button ${isRecording ? 'recording' : ''}`}
//             onClick={isRecording ? stopRecording : startRecording}
//           >
//             {isRecording ? <FaStop /> : <FaMicrophone />}
//           </button>
//         </div>
        
//         <form className="message-form" onSubmit={handleSubmit}>
//           <input
//             type="text"
//             placeholder="Share a memory or ask a question..."
//             value={message}
//             onChange={(e) => setMessage(e.target.value)}
//             disabled={isLoading}
//           />
//           <button type="submit" disabled={isLoading || !message.trim()}>
//             Send
//           </button>
//         </form>
        
//         <div className="narrative-section">
//           <button 
//             className="narrative-button"
//             onClick={handleGetNarrative}
//             disabled={isLoading || chatHistory.length < 3}
//           >
//             Generate My Memory Narrative
//           </button>
//         </div>
//       </div>
      
//       <style jsx>{`
//         .audio-interaction-container {
//           width: 100%;
//           max-width: 800px;
//           margin: 0 auto;
//           padding: 20px;
//           font-family: 'Poppins', sans-serif;
//         }
        
//         .chat-container {
//           background: white;
//           border-radius: 16px;
//           box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
//           overflow: hidden;
//           display: flex;
//           flex-direction: column;
//           height: 80vh;
//         }
        
//         .chat-header {
//           padding: 20px;
//           background: linear-gradient(90deg, #9C42A1, #6E3CBC);
//           color: white;
//           text-align: center;
//         }
        
//         .chat-header h2 {
//           margin: 0 0 8px 0;
//           font-size: 24px;
//         }
        
//         .chat-header p {
//           margin: 0;
//           font-size: 14px;
//           opacity: 0.9;
//         }
        
//         .chat-messages {
//           flex: 1;
//           overflow-y: auto;
//           padding: 20px;
//           display: flex;
//           flex-direction: column;
//           gap: 16px;
//         }
        
//         .welcome-message {
//           display: flex;
//           align-items: center;
//           background-color: #f0f7ff;
//           border-radius: 12px;
//           padding: 16px;
//           margin-bottom: 20px;
//         }
        
//         .welcome-icon {
//           font-size: 30px;
//           color: #6E3CBC;
//           margin-right: 15px;
//           flex-shrink: 0;
//         }
        
//         .message {
//           max-width: 80%;
//           padding: 12px 16px;
//           border-radius: 16px;
//           position: relative;
//           margin-bottom: 8px;
//         }
        
//         .user-message {
//           align-self: flex-end;
//           background: linear-gradient(90deg, #9C42A1, #6E3CBC);
//           color: white;
//           border-bottom-right-radius: 4px;
//         }
        
//         .ai-message {
//           align-self: flex-start;
//           background-color: #f0f7ff;
//           color: #333;
//           border-bottom-left-radius: 4px;
//         }
        
//         .narrative-message {
//           align-self: center;
//           background-color: #fff8e1;
//           color: #5d4037;
//           border-radius: 12px;
//           border-left: 4px solid #ffc107;
//           width: 90%;
//         }
        
//         .message-content {
//           line-height: 1.5;
//         }
        
//         .loading-indicator {
//           align-self: center;
//           margin: 20px 0;
//         }
        
//         .loading-dots {
//           display: flex;
//           gap: 8px;
//         }
        
//         .dot {
//           width: 10px;
//           height: 10px;
//           background-color: #9C42A1;
//           border-radius: 50%;
//           animation: bounce 1.5s infinite ease-in-out;
//         }
        
//         .dot:nth-child(1) {
//           animation-delay: 0s;
//         }
        
//         .dot:nth-child(2) {
//           animation-delay: 0.2s;
//         }
        
//         .dot:nth-child(3) {
//           animation-delay: 0.4s;
//         }
        
//         @keyframes bounce {
//           0%, 80%, 100% {
//             transform: translateY(0);
//           }
//           40% {
//             transform: translateY(-10px);
//           }
//         }
        
//         .audio-controls {
//           display: flex;
//           justify-content: space-between;
//           align-items: center;
//           padding: 15px 20px;
//           background-color: #f5f5f5;
//         }
        
//         .audio-player {
//           display: flex;
//           align-items: center;
//           gap: 15px;
//         }
        
//         .play-button, .record-button {
//           width: 50px;
//           height: 50px;
//           border-radius: 50%;
//           border: none;
//           display: flex;
//           align-items: center;
//           justify-content: center;
//           cursor: pointer;
//           font-size: 20px;
//           transition: all 0.2s ease;
//         }
        
//         .play-button {
//           background: linear-gradient(135deg, #9C42A1, #6E3CBC);
//           color: white;
//           box-shadow: 0 4px 10px rgba(110, 60, 188, 0.3);
//         }
        
//         .play-button:disabled {
//           background: #ccc;
//           cursor: not-allowed;
//           box-shadow: none;
//           opacity: 0.7;
//         }
        
//         .play-button:hover:not(:disabled) {
//           transform: scale(1.1);
//           box-shadow: 0 6px 15px rgba(110, 60, 188, 0.4);
//         }
        
//         .play-button.playing {
//           background: linear-gradient(135deg, #6E3CBC, #9C42A1);
//         }
        
//         .volume-indicator {
//           color: #9C42A1;
//           font-size: 24px;
//           opacity: 0.5;
//           transition: opacity 0.3s ease;
//         }
        
//         .volume-indicator .active {
//           opacity: 1;
//         }
        
//         .record-button {
//           background-color: white;
//           color: #E94CA1;
//           box-shadow: 0 4px 10px rgba(233, 76, 161, 0.2);
//         }
        
//         .record-button:hover {
//           transform: scale(1.1);
//           box-shadow: 0 6px 15px rgba(233, 76, 161, 0.3);
//         }
        
//         .record-button.recording {
//           background-color: #E94CA1;
//           color: white;
//           animation: pulse 1.5s infinite;
//         }
        
//         @keyframes pulse {
//           0% {
//             box-shadow: 0 0 0 0 rgba(233, 76, 161, 0.5);
//           }
//           70% {
//             box-shadow: 0 0 0 10px rgba(233, 76, 161, 0);
//           }
//           100% {
//             box-shadow: 0 0 0 0 rgba(233, 76, 161, 0);
//           }
//         }
        
//         .message-form {
//           display: flex;
//           padding: 15px 20px;
//           border-top: 1px solid #eee;
//         }
        
//         .message-form input {
//           flex: 1;
//           padding: 12px 15px;
//           border: 1px solid #ddd;
//           border-radius: 25px;
//           font-size: 16px;
//           outline: none;
//           transition: border-color 0.3s;
//         }
        
//         .message-form input:focus {
//           border-color: #9C42A1;
//         }
        
//         .message-form button {
//           background: linear-gradient(135deg, #9C42A1, #6E3CBC);
//           color: white;
//           border: none;
//           padding: 12px 20px;
//           margin-left: 10px;
//           border-radius: 25px;
//           cursor: pointer;
//           font-weight: 600;
//           transition: all 0.3s;
//         }
        
//         .message-form button:hover:not(:disabled) {
//           transform: translateY(-2px);
//           box-shadow: 0 4px 12px rgba(110, 60, 188, 0.3);
//         }
        
//         .message-form button:disabled {
//           background: #ccc;
//           cursor: not-allowed;
//         }
        
//         .narrative-section {
//           padding: 15px 20px;
//           display: flex;
//           justify-content: center;
//           background-color: #f9f9f9;
//         }
        
//         .narrative-button {
//           background: linear-gradient(135deg, #ffc107, #ff9800);
//           color: white;
//           border: none;
//           padding: 12px 25px;
//           border-radius: 25px;
//           font-weight: 600;
//           cursor: pointer;
//           transition: all 0.3s;
//           box-shadow: 0 4px 12px rgba(255, 152, 0, 0.2);
//         }
        
//         .narrative-button:hover:not(:disabled) {
//           transform: translateY(-2px);
//           box-shadow: 0 6px 15px rgba(255, 152, 0, 0.3);
//         }
        
//         .narrative-button:disabled {
//           background: #ccc;
//           cursor: not-allowed;
//           box-shadow: none;
//         }
        
//         @media (max-width: 768px) {
//           .audio-interaction-container {
//             padding: 10px;
//           }
          
//           .chat-container {
//             height: 85vh;
//           }
          
//           .message {
//             max-width: 90%;
//           }
          
//           .play-button, .record-button {
//             width: 45px;
//             height: 45px;
//             font-size: 18px;
//           }
          
//           .message-form input {
//             padding: 10px 15px;
//           }
          
//           .message-form button {
//             padding: 10px 15px;
//           }
//         }
//       `}</style>
//     </div>
//   );
// };

// export default AudioInteraction;

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { FaMicrophone, FaStop, FaPlay, FaPause, FaVolumeUp, FaRobot, FaTrash, FaSpinner } from 'react-icons/fa';

const AudioInteraction = () => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentAudioSrc, setCurrentAudioSrc] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [transcribedText, setTranscribedText] = useState('');
  const [recordingStatus, setRecordingStatus] = useState('');
  
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatContainerRef = useRef(null);
  
  const API_URL = 'http://localhost:5000';

  // Load chat history when component mounts
  useEffect(() => {
    loadChatHistory();
    playIntroAudio();
    
    return () => {
      stopRecording();
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  // Scroll to bottom when chat history updates
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory]);
  
  // Save chat history to localStorage
  useEffect(() => {
    if (chatHistory.length > 0) {
      localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    }
  }, [chatHistory]);

  const loadChatHistory = async () => {
    try {
      // First try to get history from localStorage for immediate display
      const savedHistory = localStorage.getItem('chatHistory');
      if (savedHistory) {
        setChatHistory(JSON.parse(savedHistory));
      }
      
      // Then try to get the most up-to-date history from the server
      const response = await axios.get(`${API_URL}/get-chat-history`);
      if (response.data.chat_history && response.data.chat_history.length > 0) {
        setChatHistory(response.data.chat_history);
        localStorage.setItem('chatHistory', JSON.stringify(response.data.chat_history));
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
        
        // Wait a bit to ensure audio is loaded
        setTimeout(() => {
          audioRef.current.play()
            .then(() => {
              setIsPlaying(true);
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

  const startRecording = async () => {
    try {
      setTranscribedText('');
      setRecordingStatus('Listening...');
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        setRecordingStatus('Processing speech...');
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processAudioBlob(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      setRecordingStatus('Error accessing microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop all audio tracks
      if (mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
    }
  };

  const processAudioBlob = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob);
      
      const response = await axios.post(`${API_URL}/speech-to-text`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data && response.data.text) {
        setTranscribedText(response.data.text);
        setMessage(response.data.text);
        setRecordingStatus('');
      } else {
        setRecordingStatus('Could not understand audio');
      }
    } catch (error) {
      console.error('Error processing audio:', error);
      setRecordingStatus('Error processing speech');
    }
  };

  const handlePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play()
          .catch(err => console.error('Failed to play audio:', err));
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const messageTrimmed = message.trim();
    if (!messageTrimmed) return;
    
    setIsLoading(true);
    
    try {
      // Add user message to chat history (optimistic update)
      const userMessage = { role: 'user', content: messageTrimmed, timestamp: new Date().toISOString() };
      setChatHistory(prev => [...prev, userMessage]);
      
      // Send message to backend
      const response = await axios.post(`${API_URL}/text-to-speech`, {
        message: messageTrimmed
      });
      
      // Update chat history with server response
      if (response.data.chat_history) {
        setChatHistory(response.data.chat_history);
      } else if (response.data.reply) {
        // Fallback if server doesn't return full history
        const assistantMessage = { 
          role: 'assistant', 
          content: response.data.reply, 
          timestamp: new Date().toISOString() 
        };
        setChatHistory(prev => [...prev, assistantMessage]);
      }
      
      // Set the audio source
      if (response.data.file_url) {
        const audioUrl = `${API_URL}${response.data.file_url}`;
        setCurrentAudioSrc(audioUrl);
        
        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          
          // Play the audio after a short delay
          setTimeout(() => {
            audioRef.current.play()
              .then(() => {
                setIsPlaying(true);
              })
              .catch(err => {
                console.error('Failed to play audio:', err);
              });
          }, 500);
        }
      }
      
      // Clear the input field
      setMessage('');
      setTranscribedText('');
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGetNarrative = async () => {
    setIsLoading(true);
    
    try {
      const response = await axios.get(`${API_URL}/get-narrative`);
      const chapters = response.data.chapters || [];
      
      // Add chapters to chat history
      if (chapters.length > 0) {
        const narrativeMessages = chapters.map(chapter => ({
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
          <h2>Memory Companion</h2>
          <p>Chat with your AI companion to reminisce about your memories</p>
          <button 
            className="clear-button" 
            onClick={clearHistory}
            title="Clear chat history"
          >
            <FaTrash />
          </button>
        </div>
        
        <div className="chat-messages" ref={chatContainerRef}>
          {chatHistory.length === 0 ? (
            <div className="welcome-message">
              <FaRobot className="welcome-icon" />
              <p>Hello! I'm here to help you recall memories and meaningful moments from your life. Feel free to tell me about a memory, and I'll help you explore it further.</p>
            </div>
          ) : (
            chatHistory.map((msg, index) => (
              <div key={index} className={`message ${msg.role === 'user' ? 'user-message' : msg.role === 'narrative' ? 'narrative-message' : 'ai-message'}`}>
                <div className="message-content">
                  {msg.content}
                </div>
                <div className="message-timestamp">
                  {formatTimestamp(msg.timestamp)}
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="loading-indicator">
              <div className="loading-dots">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
          
          {recordingStatus && (
            <div className="recording-status">
              <div className="recording-indicator"></div>
              <p>{recordingStatus}</p>
            </div>
          )}
        </div>
        
        <div className="audio-controls">
          <div className="audio-player">
            <audio 
              ref={audioRef} 
              onEnded={() => setIsPlaying(false)}
              onError={(e) => console.error('Audio error:', e)}
            />
            
            <button 
              className={`play-button ${isPlaying ? 'playing' : ''}`}
              onClick={handlePlayPause}
              disabled={!currentAudioSrc}
              title={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? <FaPause /> : <FaPlay />}
            </button>
            
            <div className={`volume-indicator ${isPlaying ? 'active' : ''}`}>
              <FaVolumeUp />
            </div>
          </div>
          
          <button 
            className={`record-button ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isLoading}
            title={isRecording ? "Stop recording" : "Start recording"}
          >
            {isRecording ? <FaStop /> : <FaMicrophone />}
          </button>
        </div>
        
        {transcribedText && (
          <div className="transcribed-text">
            <p>You said: <strong>{transcribedText}</strong></p>
          </div>
        )}
        
        <form className="message-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Share a memory or ask a question..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={isLoading || isRecording}
          />
          <button 
            type="submit" 
            disabled={isLoading || isRecording || !message.trim()}
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
              Generate My Memory Story
            </button>
          </div>
        )}
      </div>
      
      <style jsx>{`
        .audio-interaction-container {
          width: 100%;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
          font-family: 'Poppins', sans-serif;
        }
        
        .chat-container {
          background: white;
          border-radius: 16px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
          overflow: hidden;
          display: flex;
          flex-direction: column;
          height: 80vh;
          position: relative;
        }
        
        .chat-header {
          padding: 20px;
          background: linear-gradient(90deg, #9C42A1, #6E3CBC);
          color: white;
          text-align: center;
          position: relative;
        }
        
        .chat-header h2 {
          margin: 0 0 8px 0;
          font-size: 24px;
        }
        
        .chat-header p {
          margin: 0;
          font-size: 14px;
          opacity: 0.9;
        }
        
        .clear-button {
          position: absolute;
          right: 15px;
          top: 50%;
          transform: translateY(-50%);
          background: rgba(255, 255, 255, 0.2);
          border: none;
          color: white;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .clear-button:hover {
          background: rgba(255, 255, 255, 0.3);
          transform: translateY(-50%) scale(1.1);
        }
        
        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          scroll-behavior: smooth;
        }
        
        .welcome-message {
          display: flex;
          align-items: center;
          background-color: #f0f7ff;
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 20px;
        }
        
        .welcome-icon {
          font-size: 30px;
          color: #6E3CBC;
          margin-right: 15px;
          flex-shrink: 0;
        }
        
        .message {
          max-width: 80%;
          padding: 12px 16px;
          border-radius: 16px;
          position: relative;
          margin-bottom: 8px;
          animation: fadeIn 0.3s ease-out;
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        .user-message {
          align-self: flex-end;
          background: linear-gradient(90deg, #9C42A1, #6E3CBC);
          color: white;
          border-bottom-right-radius: 4px;
        }
        
        .ai-message {
          align-self: flex-start;
          background-color: #f0f7ff;
          color: #333;
          border-bottom-left-radius: 4px;
        }
        
        .narrative-message {
          align-self: center;
          background-color: #fff8e1;
          color: #5d4037;
          border-radius: 12px;
          border-left: 4px solid #ffc107;
          width: 90%;
          font-style: italic;
        }
        
        .message-content {
          line-height: 1.5;
          word-wrap: break-word;
        }
        
        .message-timestamp {
          font-size: 11px;
          opacity: 0.7;
          margin-top: 5px;
          text-align: right;
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
          background-color: #9C42A1;
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
        
        .recording-status {
          display: flex;
          align-items: center;
          gap: 10px;
          align-self: center;
          background: rgba(233, 76, 161, 0.1);
          padding: 10px 16px;
          border-radius: 20px;
          margin: 10px 0;
        }
        
        .recording-indicator {
          width: 12px;
          height: 12px;
          background-color: #E94CA1;
          border-radius: 50%;
          animation: pulse 1.2s infinite;
        }
        
        @keyframes pulse {
          0% {
            transform: scale(0.8);
            opacity: 0.8;
          }
          50% {
            transform: scale(1.2);
            opacity: 1;
          }
          100% {
            transform: scale(0.8);
            opacity: 0.8;
          }
        }
        
        .recording-status p {
          margin: 0;
          color: #E94CA1;
          font-weight: 500;
        }
        
        .transcribed-text {
          padding: 0 20px;
          margin-bottom: 10px;
          background-color: #f5f5f5;
          border-radius: 5px;
          font-size: 14px;
        }
        
        .audio-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px 20px;
          background-color: #f5f5f5;
        }
        
        .audio-player {
          display: flex;
          align-items: center;
          gap: 15px;
        }
        
        .play-button, .record-button {
          width: 50px;
          height: 50px;
          border-radius: 50%;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          font-size: 20px;
          transition: all 0.2s ease;
        }
        
        .play-button {
          background: linear-gradient(135deg, #9C42A1, #6E3CBC);
          color: white;
          box-shadow: 0 4px 10px rgba(110, 60, 188, 0.3);
        }
        
        .play-button:disabled {
          background: #ccc;
          cursor: not-allowed;
          box-shadow: none;
          opacity: 0.7;
        }
        
        .play-button:hover:not(:disabled) {
          transform: scale(1.1);
          box-shadow: 0 6px 15px rgba(110, 60, 188, 0.4);
        }
        
        .play-button.playing {
          background: linear-gradient(135deg, #6E3CBC, #9C42A1);
        }
        
        .volume-indicator {
          color: #9C42A1;
          font-size: 24px;
          opacity: 0.5;
          transition: opacity 0.3s ease;
        }
        
        .volume-indicator.active {
          opacity: 1;
          animation: wave 1.5s infinite;
        }
        
        @keyframes wave {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.2);
          }
        }
        
        .record-button {
          background-color: white;
          color: #E94CA1;
          box-shadow: 0 4px 10px rgba(233, 76, 161, 0.2);
        }
        
        .record-button:hover:not(:disabled) {
          transform: scale(1.1);
          box-shadow: 0 6px 15px rgba(233, 76, 161, 0.3);
        }
        
        .record-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        
        .record-button.recording {
          background-color: #E94CA1;
          color: white;
          animation: pulse 1.5s infinite;
        }
        
        .message-form {
          display: flex;
          padding: 15px 20px;
          border-top: 1px solid #eee;
        }
        
        .message-form input {
          flex: 1;
          padding: 12px 15px;
          border: 1px solid #ddd;
          border-radius: 25px;
          font-size: 16px;
          outline: none;
          transition: border-color 0.3s;
        }
        
        .message-form input:focus {
          border-color: #9C42A1;
        }
        
        .message-form button {
          background: linear-gradient(135deg, #9C42A1, #6E3CBC);
          color: white;
          border: none;
          padding: 12px 20px;
          margin-left: 10px;
          border-radius: 25px;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.3s;
          min-width: 80px;
          display: flex;
          justify-content: center;
          align-items: center;
        }
        
        .message-form button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(110, 60, 188, 0.3);
        }
        
        .message-form button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }
        
        .spinner {
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        .narrative-section {
          padding: 15px 20px;
          display: flex;
          justify-content: center;
          background-color: #f9f9f9;
        }
        
        .narrative-button {
          background: linear-gradient(135deg, #ffc107, #ff9800);
          color: white;
          border: none;
          padding: 12px 25px;
          border-radius: 25px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s;
          box-shadow: 0 4px 12px rgba(255, 152, 0, 0.2);
        }
        
        .narrative-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 6px 15px rgba(255, 152, 0, 0.3);
        }
        
        .narrative-button:disabled {
          background: #ccc;
          cursor: not-allowed;
          box-shadow: none;
        }
        
        @media (max-width: 768px) {
          .audio-interaction-container {
            padding: 10px;
          }
          
          .chat-container {
            height: 85vh;
          }
          
          .message {
            max-width: 90%;
          }
          
          .play-button, .record-button {
            width: 45px;
            height: 45px;
            font-size: 18px;
          }
          
          .message-form input {
            padding: 10px 15px;
          }
          
          .message-form button {
            padding: 10px 15px;
            min-width: 70px;
          }
        }
      `}</style>
    </div>
  );
};

export default AudioInteraction;
