import { useState } from 'react';
import InputPanel from './components/InputPanel';
import ControlPanel from './components/ControlPanel';
import OutputPanel from './components/OutputPanel';

function App() {
  const [fontSize, setFontSize] = useState(20);
  const [lineShade, setLineShade] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [classificationResult, setClassificationResult] = useState(null);

  // POST to /classify[cite: 4]
  const handleSimplify = async (text) => {
    setIsLoading(true);
    try {
      // Assumes backend is running on localhost:8000
      const response = await fetch('http://localhost:8000/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
      });
      
      if (response.ok) {
        const data = await response.json();
        setClassificationResult({
          text: text, // Temporarily displaying the original text until Day 4's /simplify is wired
          tier: data.tier, // Expected: 'Easy', 'Medium', or 'Hard'
          score: data.score // Expected: Numeric score
        });
      } else {
        console.error("Failed to classify text");
      }
    } catch (error) {
      console.error("API Error:", error);
      // Fallback for frontend testing if Member C's backend isn't running yet
      setTimeout(() => {
        setClassificationResult({
          text: text,
          tier: 'Hard',
          score: 8.5
        });
        setIsLoading(false);
      }, 1000);
      return;
    }
    setIsLoading(false);
  };

  return (
    <div 
      className="min-h-screen bg-gray-100 p-4 md:p-8"
      style={{ '--font-size': `${fontSize}px` }} 
    >
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800 font-bangla">Shohoj Lipi</h1>
        <p className="text-gray-600">Enhancing Bangla Text Accessibility</p>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[80vh]">
        <div className="lg:col-span-4 h-full">
          <InputPanel onSubmit={handleSimplify} isLoading={isLoading} />
        </div>

        <div className="lg:col-span-2 h-full">
          <ControlPanel 
            fontSize={fontSize} 
            setFontSize={setFontSize} 
            lineShade={lineShade} 
            setLineShade={setLineShade} 
          />
        </div>

        <div className="lg:col-span-6 h-full text-[length:var(--font-size)]">
          <OutputPanel result={classificationResult} lineShade={lineShade} />
        </div>
      </main>
    </div>
  );
}

export default App;