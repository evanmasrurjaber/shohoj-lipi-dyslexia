import InputPanel from './components/InputPanel';
import ControlPanel from './components/ControlPanel';
import OutputPanel from './components/OutputPanel';

function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-4 md:p-8">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800">Shohoj Lipi</h1>
        <p className="text-gray-600">Enhancing Bangla Text Accessibility</p>
      </header>

      {/* 3-Panel Layout Grid */}
      <main className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[80vh]">
        
        {/* Left: Input */}
        <div className="lg:col-span-4 h-full">
          <InputPanel />
        </div>

        {/* Middle: Controls */}
        <div className="lg:col-span-2 h-full">
          <ControlPanel />
        </div>

        {/* Right: Output */}
        <div className="lg:col-span-6 h-full">
          <OutputPanel />
        </div>

      </main>
    </div>
  );
}

export default App;