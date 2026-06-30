import { useState } from 'react';

export default function InputPanel() {
  const [text, setText] = useState('');

  return (
    <div className="flex flex-col h-full p-4 bg-white rounded-lg shadow">
      <h2 className="text-lg font-bold mb-2">Input Text</h2>
      
      {/* textarea with rounded-xl border-2[cite: 3] */}
      <textarea 
        className="flex-grow w-full p-3 border-2 rounded-xl resize-none font-bangla focus:outline-none focus:border-blue-500"
        placeholder="Paste Bangla text here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      
      <div className="flex justify-between items-center mt-4">
        {/* char counter as text-sm text-gray-400[cite: 3] */}
        <span className="text-sm text-gray-400">
          {text.length} / 2000 characters
        </span>
        
        {/* submit button with bg-navy hover state[cite: 3] */}
        <button className="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-navy transition-colors">
          Simplify
        </button>
      </div>
    </div>
  );
}