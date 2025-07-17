// frontend/src/App.jsx
import React, { useState, useEffect, useRef } from 'react';
import InputBar from './components/InputBar';

function App() {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws');
    ws.current.onopen = () => setIsConnected(true);
    ws.current.onclose = () => setIsConnected(false);

    ws.current.onmessage = (event) => {
      const receivedData = JSON.parse(event.data);
      const newMessage = {
        sender: 'agent',
        type: receivedData.type,
        content: receivedData.content,
      };
      setMessages((prevMessages) => [...prevMessages, newMessage]);
    };

    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  const handleSendMessage = (message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'user', type: 'status', content: message },
      ]);
      ws.current.send(message);
    } else {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'agent', type: 'status', content: 'Error: Not connected to the server.' },
      ]);
    }
  };

  return (
    // Updated main container with new dark background
    <div className="flex flex-col h-screen bg-gray-800 text-gray-200 font-sans">
      
      {/* Header with a slightly lighter background */}
      <div className="bg-gray-900 shadow-md p-4 text-center border-b border-gray-700">
        <h1 className="text-2xl font-bold text-gray-100">Conversational Agent</h1>
        <p className="text-sm text-gray-400">
          Status: {isConnected ? <span className="text-cyan-400 font-semibold">Connected</span> : <span className="text-red-400 font-semibold">Disconnected</span>}
        </p>
      </div>
      
      {/* Chat messages area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`flex items-end gap-2 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`p-3 rounded-lg max-w-xl shadow-md ${
                msg.sender === 'user' 
                ? 'bg-gray-200 text-gray-800' // User messages are light gray
                : 'bg-gradient-to-br from-blue-900 to-gray-800 text-white' // Agent messages have a dark blue gradient
            }`}>
              
              {/* Image Rendering Logic */}
              {msg.type === 'image' ? (
                <img 
                  src={msg.content} 
                  alt="Browser Action Screenshot" 
                  className="rounded-md max-w-md"
                />
              ) : (
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <InputBar onSendMessage={handleSendMessage} />
    </div>
  );
}

export default App;
