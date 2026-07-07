import { useState } from 'react';

// F1: Text Input & Normalisation
// - Paste box with char counter warning at 2,000 chars
// - Submit button with bg-navy hover state (Day 2 spec)
// - Loading spinner (Day 3 spec)
export default function InputPanel({ onSubmit, isLoading }) {
  const [text, setText] = useState('');

  const handleSubmit = () => {
    if (text.trim().length > 0 && text.length <= 2000) {
      onSubmit(text);
    }
  };

  const handleKeyDown = (e) => {
    // Ctrl+Enter or Cmd+Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit();
    }
  };

  const charCount = text.length;
  const isOverLimit = charCount > 2000;
  const isEmpty = charCount === 0;

  return (
    <div className="flex flex-col h-full p-4 bg-white rounded-lg shadow min-h-[60vh] lg:min-h-0">
      <h2 className="text-lg font-bold mb-3 text-gray-800">Input Text</h2>

      {/* Textarea — rounded-xl border-2, char counter as text-sm text-gray-400 (Day 2 spec) */}
      <textarea
        id="bangla-input"
        className={`flex-grow w-full p-3 border-2 rounded-xl resize-none font-bangla focus:outline-none transition-colors
          ${isOverLimit
            ? 'border-red-400 focus:border-red-500'
            : 'border-gray-200 focus:border-blue-500'
          }
          ${isLoading ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'}
        `}
        placeholder="এখানে বাংলা লেখা পেস্ট করুন... (Paste Bangla text here)"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
        aria-label="Bangla text input"
        aria-describedby="char-counter"
        style={{ minHeight: '300px' }}
      />

      <div className="flex justify-between items-center mt-3">
        {/* Char counter — text-sm text-gray-400 per Day 2 spec; red at >2000 */}
        <span
          id="char-counter"
          className={`text-sm ${isOverLimit ? 'text-red-500 font-medium' : 'text-gray-400'}`}
        >
          {charCount} / 2000 characters
          {isOverLimit && ' — limit exceeded'}
        </span>

        {/* Submit button — bg-navy hover state per Day 2 spec */}
        <button
          id="simplify-btn"
          onClick={handleSubmit}
          disabled={isLoading || isEmpty || isOverLimit}
          className="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg
            hover:bg-navy transition-colors
            disabled:bg-gray-400 disabled:cursor-not-allowed
            flex items-center gap-2"
          aria-label="Simplify text"
        >
          {/* Loading Spinner — Day 3 spec */}
          {isLoading && (
            <svg
              className="animate-spin h-4 w-4 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12" cy="12" r="10"
                stroke="currentColor" strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          )}
          {isLoading ? 'Processing...' : 'Simplify →'}
        </button>
      </div>

      <p className="text-xs text-gray-400 mt-2">
        Tip: Press <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs">Ctrl+Enter</kbd> to submit
      </p>
    </div>
  );
}