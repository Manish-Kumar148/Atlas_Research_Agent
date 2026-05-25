/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0a0b0e",
        bg1: "#111318",
        bg2: "#181b22",
        bg3: "#1e2230",
        border: "#2a2f3e",
        border2: "#333a4d",
        accent: "#4f8eff",
        accent2: "#7c3aed",
        accent3: "#10b981",
        accent4: "#f59e0b",
        accent5: "#ef4444",
        cyan: "#22d3ee",
        pink: "#ec4899",
      },
      fontFamily: {
        ui: ["Syne", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
