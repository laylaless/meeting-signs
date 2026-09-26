import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import { injectFonts } from './fonts-loader'
import { useAppStore } from './store'
import { installTestHook } from './test-hook'

injectFonts()

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
installTestHook(useAppStore())
app.mount('#app')
