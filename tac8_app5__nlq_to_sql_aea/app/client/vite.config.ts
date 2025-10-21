import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: parseInt(process.env.FRONTEND_PORT || '5173'),
    strictPort: true,
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})