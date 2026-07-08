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

// F5 stretch: Diff highlight — find changed words between original and simplified (Day 5 spec)
// Insert U+00B7 midpoint dot for syllable boundaries (provided by backend /syllabify)
function renderTextWithDiff(simplifiedText, originalText, lineShade, syllabifiedText) {
  // Split into paragraphs/lines
  const lines = (syllabifiedText || simplifiedText).split('\n').filter(Boolean);
  const originalLines = originalText ? originalText.split('\n').filter(Boolean) : [];

  return lines.map((line, lineIndex) => {
    const originalLine = originalLines[lineIndex] || '';

    // Compute word-level diff for amber highlight
    const simplifiedWords = line.split(/\s+/);
    const originalWords = originalLine.split(/\s+/);
    const originalWordSet = new Set(originalWords);

    return (
      <p
        key={lineIndex}
        className={`p-3 leading-reading tracking-bangla word-spacing-wide text-gray-800
          ${lineShade ? 'line-shade-even' : ''}
        `}
      >
        {simplifiedWords.map((word, wordIndex) => {
          // Diff: word not in original → highlight in light amber (Day 5 spec)
          const isChanged = originalText && !originalWordSet.has(word) && word.trim().length > 0;
          return (
            <span key={wordIndex}>
              {isChanged ? (
                <span className="diff-changed" title="Simplified word">
                  {word}
                </span>
              ) : (
                word
              )}
              {wordIndex < simplifiedWords.length - 1 ? ' ' : ''}
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

  // F7: TTS play — awaits the audio object and listens to onended for accurate state
  const handleTTSClick = useCallback(async () => {
    if (ttsPlaying) return;
    setTtsPlaying(true);
    const audio = await onTTS();
    if (audio) {
      audio.onended = () => setTtsPlaying(false);
      audio.onerror = () => setTtsPlaying(false);
    } else {
      // onTTS failed or returned nothing — reset immediately
      setTtsPlaying(false);
    }
  }, [onTTS, ttsPlaying]);

  // F7: TTS stop
  const handleTTSStop = useCallback(() => {
    onTTSStop?.();
    setTtsPlaying(false);
  }, [onTTSStop]);

  // Score delta display — Day 4 spec: 'Difficulty reduced from Grade X → Grade Y'
  const getScoreDelta = () => {
    if (!result?.before_score || !result?.after_score) return null;
    const delta = (result.before_score - result.after_score).toFixed(1);
    if (delta > 0) {
      return `Difficulty reduced by ${delta} grade levels`;
    } else if (delta < 0) {
      return `Difficulty increased by ${Math.abs(delta)} grade levels`;
    }
    return 'No change in difficulty';
  };

  return (
    <div className="flex flex-col p-4 bg-white rounded-lg shadow min-h-[60vh] lg:min-h-0">

      {/* Header row with title and action buttons */}
      <div className="flex flex-wrap justify-between items-start gap-3 mb-4">
        <h2 className="text-lg font-bold text-gray-800">Simplified Output</h2>

        {result && !result.error && (
          <div className="flex items-center gap-2 flex-wrap">
            {/* F7: TTS play / stop button */}
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
                /* Stop icon */
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                  <rect x="5" y="5" width="10" height="10" rx="1" />
                </svg>
              ) : (
                /* Speaker icon */
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                  <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
                </svg>
              )}
              {ttsPlaying ? 'Stop' : 'Listen'}
            </button>

            {/* F8: Copy to clipboard */}
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

            {/* F8: Download as .txt */}
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

      {/* F2 + F4: Before/After readability score badges — side by side */}
      {result && !result.error && (
        <div className="flex flex-wrap gap-3 mb-4">
          {/* F2: Before score badge */}
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

          {/* Arrow between badges */}
          <span className="flex items-center text-gray-400 font-bold">→</span>

          {/* F4: After score badge */}
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

          {/* F4: Score delta — 'Difficulty reduced from Grade X → Grade Y' (Day 4 spec) */}
          {getScoreDelta() && (
            <span className="flex items-center text-xs text-green-700 font-medium bg-green-50 px-2 py-1 rounded-full border border-green-200">
              ✓ {getScoreDelta()}
            </span>
          )}
        </div>
      )}

      {/* F5: Accessible rendered output area */}
      <div className="flex-grow border rounded-lg bg-gray-50 overflow-y-auto">
        {/* Error state */}
        {result?.error && (
          <div className="p-6 text-red-600">
            <p className="font-medium">Error</p>
            <p className="text-sm mt-1">{result.error}</p>
          </div>
        )}

        {/* Placeholder when no result */}
        {!result && (
          <div className="p-6 text-gray-500 italic font-bangla leading-reading">
            এখানে আপনার সহজ করা লেখাটি প্রদর্শিত হবে।
            <br />
            <span className="text-sm not-italic text-gray-400 font-sans">
              (Your simplified text will appear here)
            </span>
          </div>
        )}

        {/* F5: dyslexia-body accessible layout — SiyamRupali font, 20px+, 1.8 line-height */}
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
              syllableDots ? result.syllabified_text : null
            )}
          </div>
        )}
      </div>

      {/* Legend for diff highlight */}
      {result && !result.error && result.original_text && (
        <p className="text-xs text-gray-400 mt-2">
          <span className="inline-block bg-amber-100 border border-amber-200 rounded px-1 mr-1">highlighted</span>
          words were changed during simplification
        </p>
      )}
    </div>
  );
}