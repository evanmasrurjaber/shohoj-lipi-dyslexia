// F6: Font & Layout Controls
// - Range input for font size (16–30px via CSS custom property)
// - Toggle switches for line-shade and syllable dots
// - All updating CSS custom properties in real time (Day 2 & 3 spec)

export default function ControlPanel({
  fontSize,
  setFontSize,
  lineShade,
  setLineShade,
  syllableDots,
  setSyllableDots,
}) {
  return (
    <div className="flex flex-col p-4 bg-gray-50 rounded-lg shadow">
      <h2 className="text-lg font-bold mb-6 text-gray-800">Layout Controls</h2>

      <div className="space-y-6">

        {/* Font Size Slider — 16–30px per F6 spec */}
        <div>
          <label
            htmlFor="font-size-slider"
            className="flex justify-between text-sm font-medium text-gray-700 mb-2"
          >
            <span>Font Size</span>
            <span className="font-bold text-blue-600">{fontSize}px</span>
          </label>
          <input
            id="font-size-slider"
            type="range"
            min="16"
            max="30"
            value={fontSize}
            onChange={(e) => setFontSize(Number(e.target.value))}
            className="w-full accent-blue-600 cursor-pointer"
            aria-label="Font size"
            aria-valuemin={16}
            aria-valuemax={30}
            aria-valuenow={fontSize}
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>16px</span>
            <span>30px</span>
          </div>
        </div>

        {/* Alternating Line Shade Toggle — even:bg-blue-50 per F5/F6 spec */}
        <div className="flex items-center justify-between">
          <label htmlFor="line-shade-toggle" className="text-sm font-medium text-gray-700 cursor-pointer">
            Alternating Line Shade
          </label>
          <button
            id="line-shade-toggle"
            role="switch"
            aria-checked={lineShade}
            onClick={() => setLineShade(!lineShade)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1
              ${lineShade ? 'bg-blue-600' : 'bg-gray-300'}`}
            aria-label="Toggle alternating line shade"
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform
                ${lineShade ? 'translate-x-6' : 'translate-x-1'}`}
            />
          </button>
        </div>

        {/* Syllable Dots Toggle — stretch feature (Day 5 spec) */}
        <div className="flex items-center justify-between">
          <label htmlFor="syllable-dots-toggle" className="text-sm font-medium text-gray-700 cursor-pointer">
            Syllable Boundary Dots
          </label>
          <button
            id="syllable-dots-toggle"
            role="switch"
            aria-checked={syllableDots}
            onClick={() => setSyllableDots(!syllableDots)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1
              ${syllableDots ? 'bg-blue-600' : 'bg-gray-300'}`}
            aria-label="Toggle syllable boundary dots"
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform
                ${syllableDots ? 'translate-x-6' : 'translate-x-1'}`}
            />
          </button>
        </div>

      </div>

      {/* Accessibility legend */}
      <div className="mt-8 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 font-medium mb-2">Readability Tiers</p>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-green-500 inline-block"></span>
            <span className="text-xs text-gray-600">Easy</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-orange-500 inline-block"></span>
            <span className="text-xs text-gray-600">Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span>
            <span className="text-xs text-gray-600">Hard</span>
          </div>
        </div>
      </div>
    </div>
  );
}