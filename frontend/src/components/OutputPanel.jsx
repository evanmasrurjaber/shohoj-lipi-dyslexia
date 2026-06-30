export default function OutputPanel() {
  return (
    <div className="flex flex-col h-full p-4 bg-white rounded-lg shadow">
      <h2 className="text-lg font-bold mb-2">Simplified Output</h2>
      
      {/* accessible layout using custom tokens[cite: 3] */}
      <div className="flex-grow p-6 border rounded bg-gray-50 overflow-y-auto">
        <p 
          className="font-bangla leading-reading tracking-bangla word-spacing-wide text-gray-800"
        >
          {/* placeholder text in accessible layout[cite: 3] */}
          এখানে আপনার সহজ করা লেখাটি প্রদর্শিত হবে। (Your simplified text will appear here...)
        </p>
      </div>
    </div>
  );
}