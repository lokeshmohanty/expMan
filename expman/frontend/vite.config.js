import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    root: '.',
    base: '/static/',
    build: {
        outDir: '../static',
        emptyOutDir: false,
        rollupOptions: {
            input: {
                main: path.resolve(__dirname, 'index.html'),
            },
            output: {
                manualChunks: {
                    plotly: ['plotly.js-dist-min'],
                }
            }
        }
    }
})
