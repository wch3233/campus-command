import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === 'build' ? './' : '/',
  optimizeDeps: {
    include: ['katex', 'mermaid', 'plotly.js-dist-min', 'marked'],
  },
}))
