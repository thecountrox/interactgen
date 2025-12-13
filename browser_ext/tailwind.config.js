/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./*.html",
    "./**/*.html",
    "./**/*.js"
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "primary": "#22C55E",
        "primary-hover": "#1a6bd8",
        "background-light": "#f6f8f7",
        "background-dark": "#112117",
        "surface-dark": "#1e293b",
        "border-dark": "#334155",
        "text-secondary": "#94a3b8",
        "accent-green": "#10b981",
        "accent-red": "#ef4444",
        "card-dark": "#0D1F12",
        "input-dark": "#050B06",
        "surface-card": "#0D1F12",
        "surface-inner": "#050B06",
      },
      fontFamily: {
        "display": ["Inter", "Spline Sans", "sans-serif"],
        "body": ["Noto Sans", "sans-serif"]
      },
      borderRadius: {
        DEFAULT: "1rem",
        lg: "2rem",
        xl: "3rem",
        full: "9999px"
      },
      boxShadow: {
        "glow": "0 0 20px -5px rgba(54, 226, 123, 0.3)",
        "neon": "0 0 20px -5px rgba(34, 197, 94, 0.4)",
        "card-glow": "0 0 60px -15px rgba(34, 197, 94, 0.15)",
      }
    },
  },
  plugins: [],
}
