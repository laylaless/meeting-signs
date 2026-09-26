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
  </div>
  <div id="print-area"></div>
  <BnFull />
  <GlobalConfirm />
  <UpdateLogDialog v-model="updateLogOpen" />
  <Toaster position="top-center" :duration="2500" rich-colors />
</template>
