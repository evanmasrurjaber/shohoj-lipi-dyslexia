import { useState, useCallback } from 'react';

// F2: Readability Score (Before) badge — colour-coded: green Easy, orange Medium, red Hard
// F4: Readability Score (After) badge + score delta
// F5: Accessible Rendered Output — SiyamRupali font, 20px+, 1.8 line-height, alternating row tint
// F7: Text-to-Speech play/pause button
// F8: Copy & Download simplified text

// Colour-coded badge classes per Day 3 spec
const getBadgeStyle = (tier) => {
  switch (tier) {
    case 'Easy':   return 'bg-green-100 text-green-800 border-green-300';
    case 'Medium': return 'bg-orange-100 text-orange-800 border-orange-300';
    case 'Hard':   return 'bg-red-100 text-red-800 border-red-300';
    default:       return 'bg-gray-100 text-gray-800 border-gray-300';
  }
};

const getTierDot = (tier) => {
  switch (tier) {
    case 'Easy':   return 'bg-green-500';
    case 'Medium': return 'bg-orange-500';
    case 'Hard':   return 'bg-red-500';
    default:       return 'bg-gray-400';
  }
};

// ── FIX 1: Split text into sentences for line shading ──────────────────────
// Backend joins sentences with spaces (no \n). We split on Bangla sentence
// endings so multiple <p> elements are produced and nth-child(even) can fire.
function splitIntoSentences(text) {
  if (!text) return [];
  const parts = text.split(/(?<=[।!?])/u).flatMap(s => s.split('\n'));
  return parts.map(s => s.trim()).filter(Boolean);
}

// ── FIX 2: Frontend syllabifier (fallback when backend /syllabify is down) ─
// Mirrors the Python heuristic in ml/syllabifier.py:
//   split after each vowel matra or independent vowel, then join with U+00B7.
const MIDDOT = '\u00B7';
const _VOWEL_MATRAS = '\u09BE\u09BF\u09C0\u09C1\u09C2\u09C3\u09C7\u09C8\u09CB\u09CC';
const _INDEP_VOWELS = '\u0985\u0986\u0987\u0988\u0989\u098A\u098B\u098F\u0990\u0993\u0994';

function _syllabifyWord(word) {
  const pieces = [];
  let current = '';
  for (const ch of word) {
    current += ch;
    if (_VOWEL_MATRAS.includes(ch) || _INDEP_VOWELS.includes(ch)) {
      pieces.push(current);
      current = '';
    }
  }
  if (current) pieces.push(current);
  return (pieces.length > 1 ? pieces : [word]).join(MIDDOT);
}

function syllabifyFrontend(text) {
  return text.split(' ').map(token => {
    // Separate trailing punctuation before syllabifying
    const m = token.match(/^([\u0980-\u09FF]+)([\u0964\u0965,.!?;:'"]*)/u);
    if (!m || !m[1]) return token;
    return _syllabifyWord(m[1]) + (m[2] || '');
  }).join(' ');
}

// ── Render a single word, splitting on · and styling the dots ─────────────
function renderWord(word, isChanged) {
  if (!word.includes(MIDDOT)) {
    return isChanged
      ? <span className="diff-changed" title="Simplified word">{word}</span>
      : word;
  }
  const syllables = word.split(MIDDOT);
  return syllables.map((syl, si) => (
    <span key={si}>
      {isChanged
        ? <span className="diff-changed" title="Simplified word">{syl}</span>
        : syl}
      {si < syllables.length - 1 && (
        <span className="syllable-dot" aria-hidden="true">{MIDDOT}</span>
      )}
    </span>
  ));
}

// ── Main text renderer ─────────────────────────────────────────────────────
function renderTextWithDiff(simplifiedText, originalText, lineShade, syllabifiedText) {
  // Use syllabified text if available, otherwise simplified
  const sourceText = syllabifiedText || simplifiedText;

  // Split into sentences so alternating shade actually works
  const sentences = splitIntoSentences(sourceText);
  const originalWordSet = originalText
    ? new Set(originalText.split(/\s+/))
    : new Set();

  return sentences.map((sentence, sentIndex) => {
    const words = sentence.split(/\s+/);
    return (
      <p
        key={sentIndex}
        className={`p-3 leading-reading tracking-bangla word-spacing-wide text-gray-800${lineShade ? ' line-shade-even' : ''}`}
      >
        {words.map((word, wi) => {
          const cleanWord = word.replace(/\u00B7/g, '');
          const isChanged = !!originalText && !originalWordSet.has(cleanWord) && cleanWord.trim().length > 0;
          return (
            <span key={wi}>
              {renderWord(word, isChanged)}
              {wi < words.length - 1 ? ' ' : ''}
            </span>
          );
        })}
      </p>
    );
  });
}

export default function OutputPanel({ result, lineShade, syllableDots, onTTS, onTTSStop }) {
  const [copied, setCopied] = useState(false);
  const [ttsPlaying, setTtsPlaying] = useState(false);
  const [ttsError, setTtsError] = useState(null);

  // F8: Copy simplified text to clipboard
  const handleCopy = useCallback(() => {
    if (!result?.simplified_text) return;
    navigator.clipboard.writeText(result.simplified_text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [result]);

  // F8: Download as .txt file
  const handleDownload = useCallback(() => {
    if (!result?.simplified_text) return;
    const blob = new Blob([result.simplified_text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'shohoj_lipi_simplified.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [result]);

  // ── FIX 3: TTS — play() is called AFTER onended/onerror are attached ───────
  // Previously, App.jsx called audio.play() BEFORE returning the audio object.
  // If the audio ended before OutputPanel attached onended, the button stayed
  // stuck on "Stop" forever. Now OutputPanel owns play() so there's no race.
  //
  // Falls back to Web Speech API (built into every modern browser) when the
  // backend /tts is unavailable.

  const handleTTSClick = useCallback(async () => {
    if (ttsPlaying) return;
    setTtsError(null);
    setTtsPlaying(true);

    // 1. Try backend gTTS
    const audio = await onTTS();
    if (audio) {
      // Attach handlers BEFORE play() — avoids the race condition
      audio.onended = () => setTtsPlaying(false);
      audio.onerror = () => {
        setTtsPlaying(false);
        setTtsError('Audio playback failed. Try again.');
      };
      try {
        await audio.play();
      } catch {
        // play() was blocked (e.g. browser autoplay policy) — fall through to Web Speech
        audio.onended = null;
        audio.onerror = null;
        fallbackToWebSpeech(result?.simplified_text);
      }
      return;
    }

    // 2. Backend /tts unavailable — use browser Web Speech API
    fallbackToWebSpeech(result?.simplified_text);
  }, [onTTS, ttsPlaying, result]); // eslint-disable-line react-hooks/exhaustive-deps

  function fallbackToWebSpeech(text) {
    if (!text || !window.speechSynthesis) {
      setTtsPlaying(false);
      setTtsError('TTS not available. Please start the backend server.');
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'bn';
    utterance.rate = 0.85;
    utterance.onend  = () => setTtsPlaying(false);
    utterance.onerror = (e) => {
      setTtsPlaying(false);
      if (e.error !== 'interrupted') {
        setTtsError('Browser TTS failed. Try starting the backend server for full audio support.');
      }
    };
    window.speechSynthesis.speak(utterance);
  }

  // F7: TTS stop
  const handleTTSStop = useCallback(() => {
    onTTSStop?.();
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    setTtsPlaying(false);
  }, [onTTSStop]);

  // Score delta display
  const getScoreDelta = () => {
    if (result?.before_score == null || result?.after_score == null) return null;
    const delta = (result.before_score - result.after_score).toFixed(1);
    if (delta > 0) return `Difficulty reduced by ${delta} grade levels`;
    if (delta < 0) return `Difficulty increased by ${Math.abs(delta)} grade levels`;
    return 'No change in difficulty';
  };

  // ── FIX 2 (continued): Compute what text to actually render ───────────────
  // If syllableDots is on but the backend /syllabify failed (syllabified_text
  // is null), run the frontend heuristic syllabifier so the feature works
  // even without the backend.
  const displaySyllabified = syllableDots
    ? (result?.syllabified_text || (result?.simplified_text ? syllabifyFrontend(result.simplified_text) : null))
    : null;

  return (
    <div className="flex flex-col p-4 bg-white rounded-lg shadow min-h-[60vh] lg:min-h-0">

      {/* Header row */}
      <div className="flex flex-wrap justify-between items-start gap-3 mb-4">
        <h2 className="text-lg font-bold text-gray-800">Simplified Output</h2>

        {result && !result.error && (
          <div className="flex items-center gap-2 flex-wrap">
            {/* F7: TTS play / stop */}
            <button
              id="tts-play-btn"
              onClick={ttsPlaying ? handleTTSStop : handleTTSClick}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                ${ttsPlaying
                  ? 'bg-red-500 text-white hover:bg-red-600'
                  : 'bg-blue-600 text-white hover:bg-navy'
                }`}
              aria-label={ttsPlaying ? 'Stop text-to-speech' : 'Play text-to-speech'}
              title={ttsPlaying ? 'Stop reading' : 'Read simplified text aloud (Bangla TTS)'}
            >
              {ttsPlaying ? (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                  <rect x="5" y="5" width="10" height="10" rx="1" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                  <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
                </svg>
              )}
              {ttsPlaying ? 'Stop' : 'Listen'}
            </button>

            {/* F8: Copy */}
            <button
              id="copy-btn"
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
              aria-label="Copy simplified text"
              title="Copy simplified text to clipboard"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              {copied ? 'Copied!' : 'Copy'}
            </button>

            {/* F8: Download */}
            <button
              id="download-btn"
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
              aria-label="Download simplified text as .txt"
              title="Download simplified text as .txt file"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>
          </div>
        )}
      </div>

      {/* TTS error banner */}
      {ttsError && (
        <div className="flex items-start gap-2 mb-3 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
          <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{ttsError}</span>
          <button onClick={() => setTtsError(null)} className="ml-auto text-yellow-600 hover:text-yellow-800 font-bold">✕</button>
        </div>
      )}

      {/* F2 + F4: Before/After readability badges */}
      {result && !result.error && (
        <div className="flex flex-wrap gap-3 mb-4">
          {result.before_tier && (
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-bold ${getBadgeStyle(result.before_tier)}`}>
              <span className={`w-2 h-2 rounded-full ${getTierDot(result.before_tier)}`} />
              <span>Before: {result.before_tier}</span>
              {result.before_score != null && (
                <span className="bg-white/50 px-2 py-0.5 rounded text-xs">
                  Score: {Number(result.before_score).toFixed(1)}
                </span>
              )}
            </div>
          )}

          <span className="flex items-center text-gray-400 font-bold">→</span>

          {result.after_tier && (
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-bold ${getBadgeStyle(result.after_tier)}`}>
              <span className={`w-2 h-2 rounded-full ${getTierDot(result.after_tier)}`} />
              <span>After: {result.after_tier}</span>
              {result.after_score != null && (
                <span className="bg-white/50 px-2 py-0.5 rounded text-xs">
                  Score: {Number(result.after_score).toFixed(1)}
                </span>
              )}
            </div>
          )}

          {getScoreDelta() && (
            <span className="flex items-center text-xs text-green-700 font-medium bg-green-50 px-2 py-1 rounded-full border border-green-200">
              ✓ {getScoreDelta()}
            </span>
          )}
        </div>
      )}

      {/* F5: Accessible rendered output area */}
      <div className="flex-grow border rounded-lg bg-gray-50 overflow-y-auto">

        {/* Placeholder */}
        {!result && (
          <div className="p-6 text-gray-500 italic font-bangla leading-reading">
            এখানে আপনার সহজ করা লেখাটি প্রদর্শিত হবে।
            <br />
            <span className="text-sm not-italic text-gray-400 font-sans">
              (Your simplified text will appear here)
            </span>
          </div>
        )}

        {/* Error state — shown when backend is down OR returns an error */}
        {result?.error && (
          <div className="p-6">
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
              <svg className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-semibold text-red-700">Simplification Failed</p>
                <p className="text-sm text-red-600 mt-1 whitespace-pre-line">{result.error}</p>
              </div>
            </div>
          </div>
        )}

        {/* F5: Accessible text output */}
        {result && !result.error && (
          <div
            className="dyslexia-body"
            role="region"
            aria-label="Simplified text output"
          >
            {renderTextWithDiff(
              result.simplified_text,
              result.original_text,
              lineShade,
              displaySyllabified
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      {result && !result.error && result.original_text && (
        <p className="text-xs text-gray-400 mt-2">
          <span className="inline-block bg-amber-100 border border-amber-200 rounded px-1 mr-1">highlighted</span>
          words were changed during simplification
          {syllableDots && !result.syllabified_text && (
            <span className="ml-2 text-blue-400">(syllables: frontend heuristic)</span>
          )}
        </p>
      )}
    </div>
  );
}