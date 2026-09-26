<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useAppStore } from '@/store'
import { bnRenderStage } from '@/utils/banner'
import { bnFullRequest } from './bn-full'

/* 全屏显示：只显示画面；↑↓ / PgUp PgDn / 滚轮切换会标；ESC 退出（浏览器原生；失败回退 fixed 全屏） */
const store = useAppStore()
const fullEl = ref<HTMLElement>()
const stageEl = ref<HTMLElement>()
let idx = 0
let hintTimer: ReturnType<typeof setTimeout> | null = null
let wheelTs = 0

function show(showHint: boolean) {
  if (!stageEl.value) return
  bnRenderStage(stageEl.value, store.banners.list[idx]!)
  if (showHint) {
    fullEl.value!.classList.remove('hint-fade')
    if (hintTimer) clearTimeout(hintTimer)
    hintTimer = setTimeout(() => fullEl.value?.classList.add('hint-fade'), 3000)
  }
}
function fallbackActive() { return fullEl.value?.style.display === 'block' }
function exitFallback() {
  if (!fullEl.value) return
  fullEl.value.style.cssText = ''
  stageEl.value!.innerHTML = ''
}

function enter() {
  idx = Math.min(store.banners.sel, store.banners.list.length - 1)
  try {
    const p: Promise<unknown> = fullEl.value!.requestFullscreen()
    Promise.resolve(p).catch(() => {
      if (!fullEl.value) return
      fullEl.value.style.cssText = 'display:block;position:fixed;inset:0;z-index:9999'
      show(true)
    })
  } catch {
    if (!fullEl.value) return
    fullEl.value.style.cssText = 'display:block;position:fixed;inset:0;z-index:9999'
    show(true)
  }
}
watch(bnFullRequest, n => { if (n) enter() })

function switchBanner(dir: number) {
  const n = store.banners.list.length
  if (n <= 1) return
  idx = (idx + dir + n) % n
  store.banners.sel = idx
  store.save()
  show(false)
}
function onFullscreenchange() {
  if (document.fullscreenElement === fullEl.value) show(true)
  else stageEl.value && (stageEl.value.innerHTML = '')
}
function onKeydown(e: KeyboardEvent) {
  const active = document.fullscreenElement === fullEl.value || fallbackActive()
  if (!active) return
  if (e.key === 'Escape' && fallbackActive()) {   // 回退全屏：ESC 手动退出（原生全屏浏览器自理）
    exitFallback(); return
  }
  if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown' && e.key !== 'PageUp' && e.key !== 'PageDown') return
  e.preventDefault()
  switchBanner(e.key === 'ArrowDown' || e.key === 'PageDown' ? 1 : -1)
}
function onWheel(e: WheelEvent) {
  if (!(document.fullscreenElement === fullEl.value || fallbackActive()) || !e.deltaY) return
  e.preventDefault()
  const now = Date.now()
  if (now - wheelTs < 350) return   // 节流防触控板惯性连跳
  wheelTs = now
  switchBanner(e.deltaY > 0 ? 1 : -1)
}
function onClick() { if (fallbackActive()) exitFallback() }

onMounted(() => {
  document.addEventListener('fullscreenchange', onFullscreenchange)
  document.addEventListener('keydown', onKeydown)
  fullEl.value?.addEventListener('wheel', onWheel, { passive: false })
})
onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFullscreenchange)
  document.removeEventListener('keydown', onKeydown)
  fullEl.value?.removeEventListener('wheel', onWheel)
})
</script>

<template>
  <div id="bn-full" ref="fullEl" @click="onClick">
    <div class="bn-stage" id="bn-full-stage" ref="stageEl"></div>
    <div id="bn-full-hint">↑↓ / 滚轮 / PgUp PgDn 切换会标 ｜ ESC 退出</div>
  </div>
</template>
