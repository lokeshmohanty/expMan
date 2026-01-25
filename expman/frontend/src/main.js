import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
// import 'remixicon/fonts/remixicon.css' - Using CDN in index.html 
// Actually package.json didn't have remixicon, adding CDN link to index.html is safer or I can add it to package.json.
// Let's stick to CDN in index.html for icons to keep package small? Or install it. 
// I'll add the CDN link to index.html in a future step or just Install it now.
// Let's rely on the CDN I'll add to index.html to avoid another huge node_module.

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.mount('#app')
