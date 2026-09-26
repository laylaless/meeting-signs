<script setup lang="ts">
import { computed, inject } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { KIND_NAME } from '@/constants'
import { useAppStore } from '@/store'
import { clamp } from '@/utils/misc'
import type { SeatApi } from './seat-api'

const store = useAppStore()
const seatApi = inject<SeatApi>('seatApi')!

const tables = computed(() => [...store.venue.tables].sort((a, b) => a.no - b.no))

function changeNo(id: string, v: number | string, fallback: number) {
  const t = store.venue.tables.find(x => x.id === id)
  if (!t) return
  t.no = clamp(+v || fallback, 1, 99)
  normalizeNosLocal()
  store.save(); seatApi.renderSeat()
}
function normalizeNosLocal() {
  const ts = [...store.venue.tables].sort((a, b) => (a.no - b.no) || (a.id < b.id ? -1 : 1))
  ts.forEach((t, i) => (t.no = i + 1))
}
</script>

<template>
  <div v-if="!tables.length" class="text-[13px] text-muted-foreground">尚未添加桌子。</div>
  <div v-else class="flex flex-col gap-1.5">
    <div v-for="t in tables" :key="t.id" class="flex items-center gap-1.5 text-[13px]">
      <Input type="number" min="1" :model-value="t.no" class="no h-7 w-12" @change="changeNo(t.id, ($event.target as HTMLInputElement).value, t.no)" />
      <span class="kind text-muted-foreground">{{ KIND_NAME[t.kind] }}</span>
      <span class="text-xs text-muted-foreground">{{ t.kind === 'long' ? t.seatsA + '+' + t.seatsB : t.seatsA }} 座</span>
      <span class="flex-1"></span>
      <Button variant="outline" size="sm" class="h-6 px-1.5 py-0 text-xs" @click="seatApi.moveNo(t.id, -1)">↑</Button>
      <Button variant="outline" size="sm" class="h-6 px-1.5 py-0 text-xs" @click="seatApi.moveNo(t.id, 1)">↓</Button>
      <Button variant="destructive" size="sm" class="h-6 px-1.5 py-0 text-xs" @click="seatApi.delTable(t.id)">删</Button>
    </div>
  </div>
</template>
