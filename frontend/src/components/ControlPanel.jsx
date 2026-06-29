export default function ControlPanel() {
  return (
    <div className="flex flex-col h-full p-4 bg-gray-50 rounded-lg shadow">
      <h2 className="text-lg font-bold mb-4">Controls</h2>
      {/* Placeholders for Day 2/4 controls */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Font Size</label>
          <input type="range" className="w-full" />
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" id="lineShade" />
          <label htmlFor="lineShade" className="text-sm">Alternating Line Shade</label>
        </div>
      </div>
    </div>
  );
}