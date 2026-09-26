import type { useAppStore } from './store'
import { APP_VERSION, V } from './constants'

/* Playwright 测试钩子：page.evaluate 里经 window.__MS__ 读写应用状态
   （对应旧版的裸全局 state / save() / V.PXM 等） */
declare global {
  interface Window {
    __MS__?: {
      store: ReturnType<typeof useAppStore>
      V: typeof V
      APP_VERSION: string
    }
  }
}

export function installTestHook(store: ReturnType<typeof useAppStore>) {
  window.__MS__ = { store, V, APP_VERSION }
}
