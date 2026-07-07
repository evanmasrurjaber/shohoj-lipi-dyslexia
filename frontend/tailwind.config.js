/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // fontFamily.bangla — per Day 2 spec
      fontFamily: {
        bangla: ['SiyamRupali', 'Nirmala UI', 'sans-serif'],
      },
      // lineHeight.reading (1.8) — per Day 2 spec
      lineHeight: {
        reading: '1.8',
      },
      // letterSpacing.bangla (0.02em) — per Day 2 spec
      letterSpacing: {
        bangla: '0.02em',
      },
      colors: {
        // navy for button hover state — per Day 2 spec
        navy: '#000080',
      },
    },
  },
  plugins: [
    // wordSpacing utility via plugin — per Day 2 spec
    function ({ addUtilities }) {
      const newUtilities = {
        '.word-spacing-wide': {
          wordSpacing: '0.2em',
        },
        '.word-spacing-wider': {
          wordSpacing: '0.3em',
        },
      }
      addUtilities(newUtilities)
    }
  ],
}