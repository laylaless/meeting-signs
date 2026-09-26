<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { APP_VERSION } from '@/constants'
import { useAppStore } from '@/store'
import { confirmDialog } from '@/composables/useConfirm'
import { exportBackup, importBackupFile } from '@/utils/backup'

const emit = defineEmits<{ (e: 'open-update-log'): void }>()
const store = useAppStore()
const fileInput = ref<HTMLInputElement>()

const tabs = [
  { key: 'list', label: '① 名单' },
  { key: 'sign', label: '② 台签打印' },
  { key: 'seat', label: '③ 座位示意图' },
  { key: 'banner', label: '④ 会标' },
] as const

function onImportFile(e: Event) {
  const input = e.target as HTMLInputElement
  const f = input.files?.[0]
  if (f) importBackupFile(f)
  input.value = ''   // 允许重复选同一文件
}

async function onReset() {
  const ok = await confirmDialog('恢复默认', '除名单外的全部设置（台签样式、会场布局、排座结果、会标）将恢复默认，确定？')
  if (ok) store.restoreDefaults()
}
</script>

<template>
  <header class="flex flex-wrap items-center gap-x-3 gap-y-2 px-4 py-2.5 text-white" style="background:#18181b">
    <div class="flex items-baseline gap-2">
      <h1 class="text-[15px] font-semibold tracking-wide">会议台签与座位图助手</h1>
      <span class="flex items-center gap-1 text-xs opacity-80">
        <span id="app-ver" class="cursor-pointer hover:underline" title="查看更新记录" @click="emit('open-update-log')">{{ APP_VERSION }}</span>
        <span>｜</span>
        <span>design by layla</span>
        <a class="gh-link ml-0.5 inline-flex opacity-60 hover:opacity-100" href="https://github.com/laylaless/meeting-signs"
          target="_blank" rel="noopener" title="GitHub 仓库（laylaless/meeting-signs）" aria-label="GitHub 仓库">
          <svg viewBox="0 0 16 16" width="11" height="11" aria-hidden="true" fill="currentColor">
            <path
              d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
          </svg>
        </a>
      </span>
    </div>
    <nav class="flex gap-1.5">
      <button v-for="t in tabs" :key="t.key" :data-tab="t.key"
        class="rounded-md px-3 py-1.5 text-[13px] transition-colors"
        :class="store.activeTab === t.key ? 'bg-white text-zinc-900 font-medium' : 'text-zinc-300 hover:bg-white/10'"
        @click="store.activeTab = t.key">{{ t.label }}</button>
    </nav>
    <span class="opacity-40">｜</span>
    <div class="ml-auto flex items-center gap-1.5">
      <Button id="btn-export-venue" variant="secondary" size="sm" title="把名单、会场布局、排座、会议室库导出为 JSON 文件备份"
        @click="exportBackup()">导出备份</Button>
      <Button id="btn-import-venue" variant="secondary" size="sm" title="从备份 JSON 文件恢复名单、会场与会议室库"
        @click="fileInput?.click()">导入备份</Button>
      <Button id="btn-reset" variant="secondary" size="sm" title="台签/座位/会标设置与排座恢复默认（名单保留）"
        @click="onReset">↺ 恢复默认</Button>
      <input ref="fileInput" type="file" id="venue-json-file" accept=".json,application/json" class="hidden" @change="onImportFile">
    </div>
  </header>
</template>
