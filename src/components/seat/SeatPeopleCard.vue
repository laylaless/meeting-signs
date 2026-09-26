<script setup lang="ts">
import { computed, inject } from 'vue'
import { useAppStore } from '@/store'
import { venueOrder } from '@/utils/venue'
import type { SeatApi } from './seat-api'

const store = useAppStore()
const seatApi = inject<SeatApi>('seatApi')!

/* 每人当前座位信息（N号桌 X号位） */
const seatInfo = computed(() => {
  const order = venueOrder(store.venue)
  const map: Record<string, string> = {}
  for (const p of store.people) {
    const seatKey = Object.keys(store.venue.assign).find(k => store.venue.assign[k] === p.id)
    if (!seatKey) { map[p.id] = ''; continue }
    const t = store.venue.tables.find(x => x.id === seatKey.split(':')[0])
    if (!t) { map[p.id] = ''; continue }
    const o = order.find(x => x.key === seatKey)
    map[p.id] = `（${t.no}号桌${o ? ' ' + o.no + '号位' : ''}）`
  }
  return map
})
const assigned = computed(() => new Set(Object.values(store.venue.assign)))

function onClickChip(pid: string, chip: EventTarget | null) {
  const el = chip as HTMLElement | null
  const D = store.venue.disabled, sel = store.venue.selSeat
  if (sel && !D.includes(sel)) {   // 已选中座位：指派到该座
    for (const k in store.venue.assign) if (store.venue.assign[k] === pid) delete store.venue.assign[k]
    store.venue.assign[sel] = pid
    store.venue.selSeat = null
    store.save(); seatApi.renderSeat(); return
  }
  // 未选座位：自动指派到礼宾序第一个空位（跳过禁用座）
  const target = venueOrder(store.venue).find(o => !store.venue.assign[o.key])
  if (!target) { el?.classList.add('flash'); setTimeout(() => el?.classList.remove('flash'), 600); return }
  for (const k in store.venue.assign) if (store.venue.assign[k] === pid) delete store.venue.assign[k]
  store.venue.assign[target.key] = pid
  store.save(); seatApi.renderSeat()
}

/* 名单 chip 拖入画布 */
function onChipPointerdown(e: PointerEvent, pid: string, name: string) {
  e.preventDefault()
  let ghost: HTMLElement | null = null
  let moved = false
  const startX = e.clientX, startY = e.clientY
  const mv = (ev: PointerEvent) => {
    if (!moved && Math.hypot(ev.clientX - startX, ev.clientY - startY) < 5) return
    moved = true
    if (!ghost) {
      ghost = document.createElement('div')
      ghost.textContent = name
      ghost.style.cssText = 'position:fixed;z-index:99;padding:2px 8px;background:#1a66ff;color:#fff;border-radius:4px;font-size:13px;pointer-events:none'
      document.body.appendChild(ghost)
    }
    ghost.style.left = ev.clientX + 10 + 'px'
    ghost.style.top = ev.clientY - 8 + 'px'
    if (seatApi.inCanvas(ev.clientX, ev.clientY)) {
      const w = seatApi.worldFromClient(ev.clientX, ev.clientY)
      const hs = seatApi.hitSeatWorld(w.x, w.y)
      seatApi.setSelSeat(hs ? hs.s.key : null)
      seatApi.setDragGhost(hs ? w : null)
      seatApi.renderSeat()
    }
  }
  const up = (ev: PointerEvent) => {
    window.removeEventListener('pointermove', mv)
    window.removeEventListener('pointerup', up)
    ghost?.remove()
    seatApi.setDragGhost(null)
    if (!moved) return
    if (seatApi.inCanvas(ev.clientX, ev.clientY)) {
      const w = seatApi.worldFromClient(ev.clientX, ev.clientY)
      const hs = seatApi.hitSeatWorld(w.x, w.y)
      if (hs && !store.venue.disabled.includes(hs.s.key)) store.venue.assign[hs.s.key] = pid
    }
    store.save(); seatApi.renderSeat()
  }
  window.addEventListener('pointermove', mv)
  window.addEventListener('pointerup', up)
}
</script>

<template>
  <div id="seat-people" class="plist flex flex-col gap-1">
    <div v-for="p in store.people" :key="p.id" class="pchip cursor-grab select-none rounded-md border px-2 py-1 text-[13px]"
      :class="assigned.has(p.id) ? 'on' : ''" :data-pid="p.id"
      @click="onClickChip(p.id, $event.currentTarget)"
      @pointerdown="onChipPointerdown($event, p.id, p.name)">
      {{ p.name }}<small class="ml-1 text-xs text-muted-foreground">{{ p.title || '' }}{{ seatInfo[p.id] }}</small>
    </div>
    <span v-if="!store.people.length" class="text-[13px] text-muted-foreground">名单为空</span>
  </div>
</template>
