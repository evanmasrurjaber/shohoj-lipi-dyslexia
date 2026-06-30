import { useState } from 'react';

export default function InputPanel({ onSubmit, isLoading }) {
  const [text, setText] = useState('');

  const handleSubmit = () => {
    if (text.trim().length > 0) {
      onSubmit(text);
    }
  };

  return (
    <div className="flex flex-col h-full p-4 bg-white rounded-lg shadow">
      <h2 className="text-lg font-bold mb-2">Input Text</h2>
      
      <textarea 
        className="flex-grow w-full p-3 border-2 rounded-xl resize-none font-bangla focus:outline-none focus:border-blue-500"
        placeholder="Paste Bangla text here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={isLoading}
      />
      
      <div className="flex justify-between items-center mt-4">
        <span className={`text-sm ${text.length > 2000 ? 'text-red-500' : 'text-gray-400'}`}>
          {text.length} / 2000 characters
        </span>
        
        <button 
          onClick={handleSubmit}
          disabled={isLoading || text.length === 0 || text.length > 2000}
          className="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-navy transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {/* Loading Spinner[cite: 4] */}
          {isLoading && (
            <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          {isLoading ? 'Classifying...' : 'Simplify'}
        </button>
      </div>
    </div>
  );
}