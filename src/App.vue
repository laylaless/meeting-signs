<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { Toaster } from '@/components/ui/sonner'
import { useAppStore } from '@/store'
import { ensurePageStyle } from '@/utils/page-style'
import AppHeader from '@/components/layout/AppHeader.vue'
import GlobalConfirm from '@/components/layout/GlobalConfirm.vue'
import UpdateLogDialog from '@/components/layout/UpdateLogDialog.vue'
import PeopleTab from '@/components/people/PeopleTab.vue'
import SignTab from '@/components/sign/SignTab.vue'
import SeatTab from '@/components/seat/SeatTab.vue'
import BannerTab from '@/components/banner/BannerTab.vue'
import BnFull from '@/components/banner/BnFull.vue'

const store = useAppStore()
const updateLogOpen = ref(false)

store.load()
store.save()   // load 后立即回写，旧数据自动迁移
ensurePageStyle()

/* 撤销/重做快捷键（输入框聚焦时不拦截，避免与文本编辑冲突） */
function onKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && !e.altKey && e.key.toLowerCase() === 'z') {
    const el = e.target as HTMLElement | null
    const tag = el?.tagName || ''
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || el?.isContentEditable) return
    e.preventDefault()
    if (e.shiftKey) store.redo()
    else store.undo()
  }
}
function onAfterprint() { document.body.classList.remove('print-sign', 'print-seat') }

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('afterprint', onAfterprint)
})
onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('afterprint', onAfterprint)
})
</script>

<template>
  <div id="app-main" class="flex min-h-screen flex-col bg-muted/40">
    <AppHeader @open-update-log="updateLogOpen = true" />
    <main class="mx-auto w-full max-w-6xl flex-1 p-4" :class="store.activeTab === 'seat' ? 'max-w-[1500px]' : ''">
      <section id="tab-list" v-show="store.activeTab === 'list'"><PeopleTab /></section>
      <section id="tab-sign" v-show="store.activeTab === 'sign'"><SignTab /></section>
      <section id="tab-seat" v-show="store.activeTab === 'seat'"><SeatTab /></section>
      <section id="tab-banner" v-show="store.activeTab === 'banner'"><BannerTab /></section>
    </main>
    <footer class="mt-auto flex items-center justify-center gap-1.5 border-t bg-background py-3 text-xs text-muted-foreground">
      <span>design by layla</span>
      <a class="gh-link inline-flex opacity-60 hover:opacity-100" href="https://github.com/laylaless/meeting-signs"
        target="_blank" rel="noopener" title="GitHub 仓库（laylaless/meeting-signs）" aria-label="GitHub 仓库">
        <svg viewBox="0 0 16 16" width="11" height="11" aria-hidden="true" fill="currentColor">
          <path
            d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
        </svg>
      </a>
    </footer>
  </div>
  <div id="print-area"></div>
  <BnFull />
  <GlobalConfirm />
  <UpdateLogDialog v-model="updateLogOpen" />
  <Toaster position="top-center" :duration="2500" rich-colors />
</template>
