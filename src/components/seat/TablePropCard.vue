<script setup lang="ts">
import { computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { KIND_NAME } from '@/constants'
import { useAppStore } from '@/store'
import { clamp } from '@/utils/misc'
import { tableGeom } from '@/utils/venue'
import { inject } from 'vue'
import type { SeatApi } from './seat-api'

const store = useAppStore()
const seatApi = inject<SeatApi>('seatApi')!

const t = computed(() => store.venue.tables.find(x => x.id === store.venue.sel))

/* 座位数变化：裁掉超出座位上的人 */
function upd() {
  const tb = t.value
  if (!tb) return
  const long = tb.kind === 'long'
  tb.seatsA = clamp(tb.seatsA || 0, long ? 0 : tb.kind === 'round' ? 4 : 3, 50)
  if (long) {
    tb.seatsB = clamp(tb.seatsB || 0, 0, 50)
    tb.seatsL = clamp(tb.seatsL ?? 0, 0, 50)
    tb.seatsR = clamp(tb.seatsR ?? 0, 0, 50)
  }
  const keep = new Set(tableGeom(tb).seats.map(s => s.key))
  for (const k in store.venue.assign) if (k.startsWith(tb.id + ':') && !keep.has(k)) delete store.venue.assign[k]
  store.venue.disabled = store.venue.disabled.filter(k => !k.startsWith(tb.id + ':') || keep.has(k))
  store.save(); seatApi.renderSeat()
}
function rotate() { const tb = t.value!; tb.rot = (tb.rot + 90) % 360; store.save(); seatApi.renderSeat() }
function flip() { const tb = t.value!; tb.flip = !tb.flip; store.save(); seatApi.renderSeat() }
</script>

<template>
  <div v-if="!t" class="text-[13px] text-muted-foreground">点击画布中的桌子选中。</div>
    <div v-else-if="t" class="space-y-2 text-[13px]">
    <div class="flex items-center gap-2"><b>{{ KIND_NAME[t.kind] }} #{{ t.no }}</b></div>
    <div class="flex flex-wrap items-center gap-x-3 gap-y-1.5">
      <template v-if="t.kind === 'long'">
        <Label class="flex items-center gap-1">上侧座位
          <Input type="number" min="0" max="50" v-model.number="t.seatsA" class="h-7 w-14" @change="upd" /></Label>
        <Label class="flex items-center gap-1">下侧座位
          <Input type="number" min="0" max="50" v-model.number="t.seatsB" class="h-7 w-14" @change="upd" /></Label>
        <Label class="flex items-center gap-1">左端座位
          <Input type="number" min="0" max="50" :model-value="t.seatsL ?? t.seatsE ?? 0" class="h-7 w-14"
            @update:model-value="v => { if (t) t.seatsL = Number(v) }" @change="upd" /></Label>
        <Label class="flex items-center gap-1">右端座位
          <Input type="number" min="0" max="50" :model-value="t.seatsR ?? t.seatsE ?? 0" class="h-7 w-14"
            @update:model-value="v => { if (t) t.seatsR = Number(v) }" @change="upd" /></Label>
      </template>
      <Label v-else class="flex items-center gap-1">座位数
        <Input type="number" :min="t.kind === 'round' ? 4 : 3" max="50" v-model.number="t.seatsA" class="h-7 w-14" @change="upd" /></Label>
    </div>
    <div class="flex flex-wrap gap-1.5">
      <Button size="sm" variant="outline" @click="rotate">↻ 旋转 90°（当前 {{ t.rot }}°）</Button>
      <Button size="sm" variant="outline" @click="flip">⇋ 翻转{{ t.flip ? '（开）' : '' }}</Button>
      <Button size="sm" variant="destructive" @click="seatApi.delTable(t.id)">删除桌子</Button>
    </div>
  </div>
</template>
