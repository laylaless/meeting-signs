<script setup lang="ts">
import { ref, watch } from 'vue'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { UPDATE_LOG } from '@/update-log'

const open = defineModel<boolean>({ default: false })
const log = ref('加载中…')

watch(open, async v => {
  if (!v) return
  log.value = '加载中…'
  try {
    // 优先读取同目录 UPDATE.md（网页服务器访问时生效）；file:// 直开时浏览器禁止读取本地文件，回退内置记录
    const r = await fetch('./UPDATE.md', { cache: 'no-store' })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    log.value = await r.text()
  } catch {
    log.value = '⚠️ 无法读取 UPDATE.md：浏览器限制，双击直接打开（file://）时网页不可读取本地文件；通过网页服务器访问时可自动读取最新。\n\n———— 以下为内置记录（随版本发布同步） ————\n\n' + UPDATE_LOG
  }
})
</script>

<template>
  <Dialog :open="open" @update:open="v => (open = v)">
    <DialogContent class="max-w-2xl">
      <DialogHeader>
        <DialogTitle>更新记录</DialogTitle>
      </DialogHeader>
      <ScrollArea class="max-h-[70vh] rounded-md border bg-muted/30 p-4">
        <pre id="ver-log" class="whitespace-pre-wrap break-words font-sans text-[13px] leading-relaxed">{{ log }}</pre>
      </ScrollArea>
    </DialogContent>
  </Dialog>
</template>
