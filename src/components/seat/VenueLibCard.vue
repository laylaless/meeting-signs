<script setup lang="ts">
import { computed, inject, nextTick, ref } from 'vue'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { loadVenues, saveVenues, useAppStore } from '@/store'
import { confirmDialog } from '@/composables/useConfirm'
import type { SeatApi } from './seat-api'

const store = useAppStore()
const seatApi = inject<SeatApi>('seatApi')!
const venueName = ref('')
const libVersion = ref(0)   // 会议室库改动后刷新列表（localStorage 非响应式）
const lib = computed(() => { void libVersion.value; return loadVenues() })

function refreshLib() { libVersion.value++ }

async function saveVenue() {
  const name = venueName.value.trim()
  if (!name) { toast.warning('请先输入会议室名称'); return }
  if (!store.venue.tables.length) { toast.warning('当前画布没有桌子，先添加并摆好桌子再保存'); return }
  const list = loadVenues()
  const old = list.find(v => v.name === name)
  const snap = JSON.parse(JSON.stringify(store.venue.tables))
  if (old) {
    const ok = await confirmDialog('覆盖保存', `已有同名会议室「${name}」，用当前布局覆盖它？`)
    if (!ok) return
    old.tables = snap; old.showNo = store.venue.showNo; old.savedAt = Date.now()
  } else {
    list.push({ id: 'v' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), name, tables: snap, showNo: store.venue.showNo, savedAt: Date.now() })
  }
  saveVenues(list); refreshLib(); venueName.value = ''
}

async function onLibAction(act: 'load' | 'del', id: string) {
  const list = loadVenues()
  const v = list.find(x => x.id === id)
  if (!v) return
  if (act === 'del') {
    const ok = await confirmDialog('删除会议室', `删除会议室「${v.name}」？`, { danger: true })
    if (!ok) return
    saveVenues(list.filter(x => x.id !== id)); refreshLib()
    return
  }
  // 载入：替换布局、清排座，名单保留
  if (store.venue.tables.length || Object.keys(store.venue.assign).length) {
    const ok = await confirmDialog('载入会议室', `载入「${v.name}」将替换当前会场布局并清空排座（名单保留）。确定？`)
    if (!ok) return
  }
  store.venue.tables = JSON.parse(JSON.stringify(v.tables))
  store.venue.assign = {}
  store.venue.disabled = []
  store.venue.sel = null
  store.venue.selSeat = null
  store.venue.showNo = v.showNo !== false
  store.save()
  seatApi.renderSeat()
  nextTick(() => requestAnimationFrame(() => { seatApi.zoomFit(); store.save() }))   // 载入后等画布渲染完成再「适应」居中
}
</script>

<template>
  <div class="space-y-2">
    <div class="flex flex-wrap gap-1.5">
      <Input id="venue-name-input" v-model="venueName" placeholder="会议室名称，如：三楼大会议室" class="h-8 min-w-[130px] flex-1" />
      <Button id="btn-save-venue" size="sm" @click="saveVenue">💾 保存为会议室</Button>
    </div>
    <p class="m-0 text-[13px] text-muted-foreground">保存当前桌子布局（不含名单与排座），换会议直接载入重排。</p>
    <div>
      <template v-if="lib.length">
        <div v-for="v in lib" :key="v.id" class="flex items-center gap-1.5 py-1 text-[13px]">
          <b class="flex-1 truncate font-medium">{{ v.name }}</b>
          <span class="text-xs text-muted-foreground">{{ v.tables.length }}桌</span>
          <Button size="sm" class="h-6 px-1.5 py-0 text-xs" data-act="load" @click="onLibAction('load', v.id)">载入</Button>
          <Button size="sm" variant="destructive" class="h-6 px-1.5 py-0 text-xs" data-act="del" @click="onLibAction('del', v.id)">删</Button>
        </div>
      </template>
      <p v-else class="py-1 text-[13px] text-muted-foreground">（尚无保存的会议室）</p>
    </div>
  </div>
</template>
