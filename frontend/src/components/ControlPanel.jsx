export default function ControlPanel({ fontSize, setFontSize, lineShade, setLineShade }) {
  return (
    <div className="flex flex-col h-full p-4 bg-gray-50 rounded-lg shadow">
      <h2 className="text-lg font-bold mb-6">Layout Controls</h2>
      
      <div className="space-y-6">
        {/* Font Size Slider (16-30px) */}
        <div>
          <label className="flex justify-between text-sm font-medium text-gray-700 mb-2">
            <span>Font Size</span>
            <span>{fontSize}px</span>
          </label>
          <input 
            type="range" 
            min="16" 
            max="30" 
            value={fontSize}
            onChange={(e) => setFontSize(e.target.value)}
            className="w-full accent-blue-600" 
          />
        </div>

        {/* Line Shade Toggle */}
        <div className="flex items-center justify-between">
          <label htmlFor="lineShade" className="text-sm font-medium text-gray-700">
            Alternating Line Shade
          </label>
          <button 
            id="lineShade"
            onClick={() => setLineShade(!lineShade)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${lineShade ? 'bg-blue-600' : 'bg-gray-300'}`}
          >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${lineShade ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>
      </div>
    </div>
  );
}