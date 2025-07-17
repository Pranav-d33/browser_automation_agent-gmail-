// frontend/src/components/InputBar.jsx
import React, { useState } from 'react';

const InputBar = ({ onSendMessage }) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div className="p-4 bg-gray-100 border-t border-gray-200 flex">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        className="flex-1 border rounded-l-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="Type your message..."
      />
      <button
        onClick={handleSend}
        className="bg-blue-500 text-white px-4 rounded-r-lg hover:bg-blue-600 focus:outline-none"
      >
        Send
      </button>
    </div>
  );
};

export default InputBar;