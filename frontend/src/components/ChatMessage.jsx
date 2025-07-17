// frontend/src/components/ChatMessage.jsx
import React from 'react';

const ChatMessage = ({ message }) => {
  const isAgent = message.sender === 'agent';

  return (
    <div className={`flex ${isAgent ? 'justify-start' : 'justify-end'} mb-4`}>
      <div
        className={`rounded-lg px-4 py-2 max-w-md ${
          isAgent
            ? 'bg-gray-200 text-gray-800'
            : 'bg-blue-500 text-white'
        }`}
      >
        {message.content}
      </div>
    </div>
  );
};

export default ChatMessage;