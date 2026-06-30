/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        bangla: ['SiyamRupali', 'sans-serif'], // fontFamily.bangla
      },
      lineHeight: {
        reading: '1.8', // lineHeight.reading (1.8)
      },
      letterSpacing: {
        bangla: '0.02em', // letterSpacing.bangla (0.02em)
      },
      colors: {
        navy: '#000080', // Adding navy for the button hover state[cite: 3]
      }
    },
  },
  plugins: [
    // wordSpacing utility via plugin[cite: 3]
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