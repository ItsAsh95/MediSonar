import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/symptom-analyzer/', // CRITICAL for serving from a sub-route
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  // build: { // This section is optional if you are happy with the default 'dist'
  //   outDir: 'dist' 
  // }
});