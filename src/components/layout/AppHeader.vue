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
