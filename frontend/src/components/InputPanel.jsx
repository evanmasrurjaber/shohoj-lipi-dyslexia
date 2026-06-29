export default function InputPanel() {
  return (
    <div className="flex flex-col h-full p-4 bg-white rounded-lg shadow">
      <h2 className="text-lg font-bold mb-2">Input Text</h2>
      <textarea 
        className="flex-grow w-full p-2 border rounded resize-none"
        placeholder="Paste Bangla text here..."
      />
      <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
        Simplify
      </button>
    </div>
  );
}