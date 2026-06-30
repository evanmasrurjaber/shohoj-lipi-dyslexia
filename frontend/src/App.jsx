import { useState } from 'react';
import InputPanel from './components/InputPanel';
import ControlPanel from './components/ControlPanel';
import OutputPanel from './components/OutputPanel';

function App() {
  const [fontSize, setFontSize] = useState(20);

  return (
    <div 
      className="min-h-screen bg-gray-100 p-4 md:p-8"
      style={{ '--font-size': `${fontSize}px` }} 
    >
      {/* CSS custom property --font-size is applied to the wrapper div above */}
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800 font-bangla">Shohoj Lipi</h1>
        <p className="text-gray-600">Enhancing Bangla Text Accessibility</p>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[80vh]">
        <div className="lg:col-span-4 h-full">
          <InputPanel />
        </div>

        <div className="lg:col-span-2 h-full">
          {/* We will pass setFontSize here on Day 4 to let the slider control it */}
          <ControlPanel />
        </div>

        <div className="lg:col-span-6 h-full text-[length:var(--font-size)]">
          <OutputPanel />
        </div>
      </main>
    </div>
  );
}

export default App;