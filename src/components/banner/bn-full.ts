import { ref } from 'vue'

/* BannerTab → BnFull（挂在 App 根部）的全屏打开请求 */
export const bnFullRequest = ref(0)

export function requestBannerFullscreen() {
  bnFullRequest.value++
}
