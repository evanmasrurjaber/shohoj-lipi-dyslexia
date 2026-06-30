export default function OutputPanel({ result, lineShade }) {
  // Readability badge (colour-coded: green Easy, orange Medium, red Hard)[cite: 4]
  const getBadgeColor = (tier) => {
    switch(tier) {
      case 'Easy': return 'bg-green-100 text-green-800 border-green-300';
      case 'Medium': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'Hard': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="flex flex-col h-full p-4 bg-white rounded-lg shadow">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-bold">Simplified Output</h2>
        
        {/* Readability Score Badge[cite: 4] */}
        {result && (
          <div className={`px-3 py-1 rounded-full border text-sm font-bold flex items-center gap-2 ${getBadgeColor(result.tier)}`}>
            <span>Grade: {result.tier}</span>
            <span className="bg-white/50 px-2 py-0.5 rounded text-xs">Score: {result.score}</span>
          </div>
        )}
      </div>
      
      <div className="flex-grow border rounded bg-gray-50 overflow-y-auto">
        {!result ? (
          <div className="p-6 text-gray-500 italic font-bangla">
            এখানে আপনার সহজ করা লেখাটি প্রদর্শিত হবে।
          </div>
        ) : (
          <div className="font-bangla leading-reading tracking-bangla word-spacing-wide text-gray-800">
            {/* Split text by sentences/newlines to apply alternating row tint[cite: 4] */}
            {result.text.split('\n').map((paragraph, index) => (
              <p 
                key={index} 
                className={`p-4 ${lineShade ? 'even:bg-blue-50' : ''}`}
              >
                {paragraph}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}