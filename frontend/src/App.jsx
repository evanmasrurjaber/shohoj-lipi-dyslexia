import { useState, useCallback, useRef } from 'react';
import InputPanel from './components/InputPanel';
import ControlPanel from './components/ControlPanel';
import OutputPanel from './components/OutputPanel';

// Backend base URL — Member C's FastAPI server
const API_BASE = 'http://localhost:8001';

function App() {
  // F6: Font & Layout Controls — React state → CSS custom properties
  const [fontSize, setFontSize] = useState(20);
  const [lineShade, setLineShade] = useState(false);
  const [syllableDots, _setSyllableDots] = useState(false);

  // Pipeline state
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  // result shape: {
  //   original_text: string,
  //   simplified_text: string,
  //   before_score: number,
  //   before_tier: string,       // 'Easy' | 'Medium' | 'Hard'
  //   after_score: number,
  //   after_tier: string,
  //   syllabified_text: string | null,
  // }

  // Day 4: Wire the full flow: submit → /classify (before) → /simplify → /classify (after)
  // Day 4 spec: single /process endpoint returning {before_score, before_tier, simplified_text, after_score, after_tier}
  const handleSimplify = useCallback(async (text) => {
    setIsLoading(true);
    setResult(null);

    try {
      // POST to /process — the Day 4 endpoint that chains classify + simplify
      const response = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      if (response.ok) {
        const data = await response.json();
        // data: { before_score, before_tier, simplified_text, after_score, after_tier }

        let syllabified_text = null;

        // F5 stretch: call /syllabify if syllable dots are enabled
        if (syllableDots) { // eslint-disable-line react-hooks/exhaustive-deps
          try {
            const syllRes = await fetch(`${API_BASE}/syllabify`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: data.simplified_text }),
            });
            if (syllRes.ok) {
              const syllData = await syllRes.json();
              syllabified_text = syllData.syllabified_text;
            }
          } catch {
            // syllabify is a stretch feature — fail silently
          }
        }

        setResult({
          original_text: text,
          simplified_text: data.simplified_text,
          before_score: data.before_score,
          before_tier: data.before_tier,
          after_score: data.after_score,
          after_tier: data.after_tier,
          syllabified_text,
        });
      } else {
        const errData = await response.json().catch(() => ({}));
        console.error('Backend error:', errData);
        // Show error state in result
        setResult({ error: errData.detail || 'Server error. Please try again.' });
      }
    } catch (error) {
      console.error('API Error:', error);
      // Show a real error — not mock data that hides the problem
      setResult({
        error: 'Cannot reach the backend server. Make sure it is running on port 8001.\n' +
               `(${error?.message || error})`,
      });
    }

    setIsLoading(false);
  }, [syllableDots]);

  // F7: TTS play button — calls /tts endpoint (Member C, Day 2)
  // Returns the Audio object so OutputPanel can track onended and call stop()
  const ttsAudioRef = useRef(null);

  const handleTTS = useCallback(async () => {
    if (!result?.simplified_text) return null;
    try {
      const response = await fetch(`${API_BASE}/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: result.simplified_text }),
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        ttsAudioRef.current = audio;
        // Do NOT call audio.play() here — OutputPanel attaches onended/onerror
        // BEFORE calling play() to avoid the race condition where audio ends
        // before the handler is wired up (button stuck on "Stop").
        return audio;
      } else {
        console.error('TTS endpoint error');
      }
    } catch (error) {
      console.error('TTS API Error:', error);
    }
    return null;
  }, [result]);

  const handleTTSStop = useCallback(() => {
    if (ttsAudioRef.current) {
      ttsAudioRef.current.pause();
      ttsAudioRef.current.currentTime = 0;
      ttsAudioRef.current = null;
    }
  }, []);

  // Syllable dots toggle — fetches /syllabify on-demand if toggled on after simplification
  const handleSyllableDotsToggle = useCallback(async (value) => {
    _setSyllableDots(value);
    if (value && result?.simplified_text && !result?.syllabified_text) {
      try {
        const syllRes = await fetch(`${API_BASE}/syllabify`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: result.simplified_text }),
        });
        if (syllRes.ok) {
          const syllData = await syllRes.json();
          setResult((prev) => ({ ...prev, syllabified_text: syllData.syllabified_text }));
        }
      } catch {
        // fail silently — stretch feature
      }
    }
    // Toggling OFF: clear syllabified_text so output reverts immediately
    if (!value && result?.syllabified_text) {
      setResult((prev) => ({ ...prev, syllabified_text: null }));
    }
  }, [result]);

  // Update CSS custom property --font-size in real time — F6 spec
  const handleFontSizeChange = useCallback((size) => {
    setFontSize(size);
    document.documentElement.style.setProperty('--font-size', `${size}px`);
  }, []);

  return (
    // CSS custom property passed via inline style — F6 spec
    <div
      className="min-h-screen bg-gray-100 p-4 md:p-8"
      style={{ '--font-size': `${fontSize}px` }}
    >
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800 font-bangla">
          সহজ লিপি — Shohoj Lipi
        </h1>
        <p className="text-gray-600 mt-1">
          Enhancing Bangla Text Accessibility for Dyslexic Readers
        </p>
      </header>

      {/* 3-panel layout: InputPanel | ControlPanel | OutputPanel */}
      <main className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* InputPanel — F1 */}
        <div className="lg:col-span-4">
          <InputPanel onSubmit={handleSimplify} isLoading={isLoading} />
        </div>

        {/* ControlPanel — F6 */}
        <div className="lg:col-span-2">
          <ControlPanel
            fontSize={fontSize}
            setFontSize={handleFontSizeChange}
            lineShade={lineShade}
            setLineShade={setLineShade}
            syllableDots={syllableDots}
            setSyllableDots={handleSyllableDotsToggle}
          />
        </div>

        {/* OutputPanel — F2, F4, F5, F7, F8 */}
        <div className="lg:col-span-6" style={{ fontSize: `${fontSize}px` }}>
          <OutputPanel
            result={result}
            lineShade={lineShade}
            syllableDots={syllableDots}
            onTTS={handleTTS}
            onTTSStop={handleTTSStop}
          />
        </div>
      </main>
    </div>
  );
}

export default App;