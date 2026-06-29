export default function OutputPanel() {
  return (
    <div className="flex flex-col h-full p-4 bg-white rounded-lg shadow">
      <h2 className="text-lg font-bold mb-2">Simplified Output</h2>
      <div className="flex-grow p-4 border rounded bg-gray-50" style={{ fontFamily: 'SiyamRupali, sans-serif' }}>
        <p className="text-gray-500 italic">Simplified text will appear here...</p>
      </div>
    </div>
  );
}