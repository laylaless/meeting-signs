<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, provide, ref, watch } from 'vue'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { V } from '@/constants'
import { useAppStore } from '@/store'
import { confirmDialog } from '@/composables/useConfirm'
import { clamp } from '@/utils/misc'
import { hitSeat, seatPerson, tableGeom, venueOrder } from '@/utils/venue'
import type { SeatBox, TableGeom } from '@/utils/venue'
import type { VTable } from '@/types'
import { setPageStyle } from '@/utils/page-style'
import CollapsibleCard from './CollapsibleCard.vue'
import VenueLibCard from './VenueLibCard.vue'
import TablePropCard from './TablePropCard.vue'
import TableFormCard from './TableFormCard.vue'
import SeatPeopleCard from './SeatPeopleCard.vue'

const store = useAppStore()
const canvasRef = ref<HTMLCanvasElement>()
const zoomLabel = computed(() => Math.round(store.venue.zoom * 100) + '%')

/* ================= 渲染 ================= */
let ctx: CanvasRenderingContext2D | null = null
let dragGhost: { x: number; y: number } | null = null

function fitCanvasDPR() {
  const canvas = canvasRef.value
  if (!canvas) return
  const r = canvas.parentElement!.getBoundingClientRect(), dpr = window.devicePixelRatio || 1
  canvas.width = Math.round(r.width * dpr)
  canvas.height = Math.round(r.height * dpr)
  canvas.style.width = r.width + 'px'
  canvas.style.height = r.height + 'px'
}
function screenToWorld(sx: number, sy: number) {
  const v = store.venue
  return { x: (sx - v.view.x) / (v.zoom * V.PXM), y: (sy - v.view.y) / (v.zoom * V.PXM) }
}
function canvasPos(e: { clientX: number; clientY: number }) {
  const r = canvasRef.value!.getBoundingClientRect()
  return { sx: e.clientX - r.left, sy: e.clientY - r.top }
}

function drawSeatBox(c: CanvasRenderingContext2D, s: SeatBox, no?: number) {
  const v = store.venue
  const p = seatPerson(v.assign, store.people, s.key)
  const dis = v.disabled.includes(s.key)
  c.fillStyle = p ? '#eef4ff' : dis ? '#e6e6e6' : '#fff'
  c.fillRect(s.x - s.w / 2, s.y - s.h / 2, s.w, s.h)
  if (dis) {
    c.save(); c.beginPath(); c.rect(s.x - s.w / 2, s.y - s.h / 2, s.w, s.h); c.clip()
    c.strokeStyle = '#c8c8c8'; c.lineWidth = .25
    c.beginPath()
    for (let x = -s.w / 2; x < s.w / 2 + s.h; x += 2.6) { c.moveTo(s.x + x, s.y + s.h / 2); c.lineTo(s.x + x - s.h, s.y - s.h / 2) }
    c.stroke(); c.restore()
    c.font = '4px sans-serif'; c.fillStyle = '#aaa'; c.textAlign = 'center'; c.textBaseline = 'middle'
    c.fillText('×', s.x, s.y)
  }
  c.strokeStyle = dis ? '#bbb' : (v.selSeat === s.key ? '#1a66ff' : '#333')
  c.lineWidth = v.selSeat === s.key && !dis ? .5 : .25
  c.strokeRect(s.x - s.w / 2, s.y - s.h / 2, s.w, s.h)
  if (p) {   // 名字随框宽缩放
    let fs = s.h * .62
    const name = p.name.length === 2 ? p.name[0] + ' ' + p.name[1] : p.name
    c.font = `${fs}px "SimHei","Heiti SC","PingFang SC",sans-serif`
    while (c.measureText(name).width > s.w - 3 && fs > 4) { fs -= .5; c.font = `${fs}px "SimHei","Heiti SC","PingFang SC",sans-serif` }
    c.fillStyle = '#111'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(name, s.x, s.y + .3)
  }
  if (store.venue.showNo && no && !dis) {   // 礼宾序号：座位上缘小字（禁用座不显示）
    c.font = '3.6px sans-serif'; c.fillStyle = '#1a66ff'; c.textAlign = 'center'; c.textBaseline = 'bottom'
    c.fillText(String(no), s.x, s.y - s.h / 2 - .6)
  }
}
function roundRect(c: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  c.beginPath(); c.moveTo(x + r, y)
  c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r)
  c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath()
}
function noMapForTable(): Record<string, number> {
  const m: Record<string, number> = {}
  venueOrder(store.venue).forEach(o => (m[o.key] = o.no))
  return m
}
function drawTable(c: CanvasRenderingContext2D, t: VTable, nos?: Record<string, number>) {
  const g: TableGeom = tableGeom(t), sel = store.venue.sel === t.id
  const noMap = nos ?? noMapForTable()
  c.save(); c.translate(t.x, t.y); c.rotate(t.rot * Math.PI / 180)
  c.fillStyle = '#f7f4ec'; c.strokeStyle = sel ? '#1a66ff' : '#444'; c.lineWidth = sel ? .6 : .35
  if (t.kind === 'round') { c.beginPath(); c.arc(0, 0, g.desk.r!, 0, 7); c.fill(); c.stroke() }
  else { roundRect(c, -g.desk.w! / 2, -g.desk.h! / 2, g.desk.w!, g.desk.h!, 3); c.fill(); c.stroke() }
  c.font = '8px "SimHei","Heiti SC",sans-serif'; c.fillStyle = '#8a7a55'; c.textAlign = 'center'; c.textBaseline = 'middle'
  c.fillText(String(t.no), 0, 0)
  // 座位（先下侧后上侧，人名后画避免被桌体盖住）
  g.seats.filter(s => s.side !== 'a' && s.side !== 'p').forEach(s => drawSeatBox(c, s, noMap[s.key]))
  g.seats.filter(s => s.side === 'a' || s.side === 'p').forEach(s => drawSeatBox(c, s, noMap[s.key]))
  c.restore()
}
function renderSeat() {
  const canvas = canvasRef.value
  if (!canvas) return
  if (!ctx) ctx = canvas.getContext('2d')
  if (!ctx) return
  const c2 = ctx
  const v = store.venue, dpr = window.devicePixelRatio || 1
  fitCanvasDPR()
  if (!canvas.width || !canvas.height) return   // 隐藏时画布 0 尺寸，跳过
  c2.setTransform(1, 0, 0, 1, 0, 0)
  c2.fillStyle = '#eef0f4'; c2.fillRect(0, 0, canvas.width, canvas.height)
  // mm 网格
  c2.setTransform(dpr * v.zoom * V.PXM, 0, 0, dpr * v.zoom * V.PXM, dpr * v.view.x, dpr * v.view.y)
  c2.strokeStyle = 'rgba(0,0,0,.05)'; c2.lineWidth = .15
  const gw = canvas.width / (dpr * v.zoom * V.PXM)
  for (let x = 0; x < gw; x += 20) { c2.beginPath(); c2.moveTo(x, 0); c2.lineTo(x, canvas.height / (dpr * v.zoom * V.PXM)); c2.stroke() }
  for (let y = 0; y < canvas.height / (dpr * v.zoom * V.PXM); y += 20) { c2.beginPath(); c2.moveTo(0, y); c2.lineTo(gw, y); c2.stroke() }
  ;[...v.tables].sort((a, b) => a.no - b.no).forEach(t => drawTable(c2, t))
  // 拖人 ghost
  if (dragGhost) {
    c2.setTransform(dpr * v.zoom * V.PXM, 0, 0, dpr * v.zoom * V.PXM, dpr * v.view.x, dpr * v.view.y)
    c2.fillStyle = 'rgba(26,102,255,.15)'; c2.strokeStyle = '#1a66ff'; c2.lineWidth = .4
    c2.fillRect(dragGhost.x - 18, dragGhost.y - 7.5, 36, 15); c2.strokeRect(dragGhost.x - 18, dragGhost.y - 7.5, 36, 15)
  }
}

/* 状态变化自动重绘（表格拖动/排座/撤销等全部覆盖；rAF 合并高频变更） */
watch(() => [store.venue, store.people], () => requestAnimationFrame(renderSeat), { deep: true })
watch(() => store.activeTab, t => { if (t === 'seat') nextTick(() => requestAnimationFrame(renderSeat)) })

function zoomFit() {
  const v = store.venue
  const canvas = canvasRef.value
  if (!canvas) return
  if (!v.tables.length) { v.zoom = 1; v.view = { x: 40, y: 30 }; renderSeat(); return }
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9
  for (const t of v.tables) {
    // 旋转感知 AABB（半宽半高 + 座位/人名余量）
    const g = tableGeom(t), dw = g.desk.w || 2 * (g.desk.r || 0), dh = g.desk.h || 2 * (g.desk.r || 0)
    const a = Math.abs(Math.cos(t.rot * Math.PI / 180)), b = Math.abs(Math.sin(t.rot * Math.PI / 180))
    const ex = (a * dw + b * dh) / 2 + 45, ey = (b * dw + a * dh) / 2 + 45
    x0 = Math.min(x0, t.x - ex); y0 = Math.min(y0, t.y - ey); x1 = Math.max(x1, t.x + ex); y1 = Math.max(y1, t.y + ey)
  }
  const r = canvas.getBoundingClientRect()
  v.zoom = Math.min(4, Math.max(.01, Math.min(r.width / ((x1 - x0) * V.PXM), r.height / ((y1 - y0) * V.PXM)) * .95))
  v.view.x = (r.width - (x0 + x1) * v.zoom * V.PXM) / 2
  v.view.y = (r.height - (y0 + y1) * v.zoom * V.PXM) / 2
  renderSeat()
}

/* ================= 画布交互：拖桌 / 拖人 / 平移 / 缩放 ================= */
type CanvasDrag =
  | { mode: 'pan'; sx: number; sy: number; vx: number; vy: number }
  | { mode: 'table'; id: string; ox: number; oy: number }
  | { mode: 'person'; fromKey: string }
let canvasDrag: CanvasDrag | null = null

function onCanvasMousedown(e: MouseEvent) { if (e.button === 1) e.preventDefault() }   // 中键：防浏览器自动滚动

function onCanvasPointerdown(e: PointerEvent) {
  const canvas = canvasRef.value
  if (!canvas || e.button === 2) return   // 右键留给「禁用座位」；左键/中键都可拖
  try { canvas.setPointerCapture(e.pointerId) } catch { /* 合成事件/特殊环境下捕获失败不阻断拖拽 */ }
  const { sx, sy } = canvasPos(e), w = screenToWorld(sx, sy)
  if (e.button !== 1) {   // 中键 = 纯平移：不选中/不拖桌子/不拖人
    const hs = hitSeat(store.venue.tables, w.x, w.y)
    if (hs && store.venue.assign[hs.s.key]) { canvasDrag = { mode: 'person', fromKey: hs.s.key }; store.venue.selSeat = hs.s.key; renderSeat(); return }
    const ht = hitTableLocal(w.x, w.y)
    if (ht) { canvasDrag = { mode: 'table', id: ht.id, ox: w.x - ht.x, oy: w.y - ht.y }; if (store.venue.sel !== ht.id) store.venue.sel = ht.id; renderSeat(); return }
    store.venue.sel = null
  }
  canvasDrag = { mode: 'pan', sx, sy, vx: store.venue.view.x, vy: store.venue.view.y }
  canvas.style.cursor = 'grabbing'; renderSeat()
}
function hitTableLocal(wx: number, wy: number): VTable | null {
  for (const t of [...store.venue.tables].sort((a, b) => b.no - a.no)) {
    const a = -t.rot * Math.PI / 180, dx = wx - t.x, dy = wy - t.y
    const lx = dx * Math.cos(a) - dy * Math.sin(a), ly = dx * Math.sin(a) + dy * Math.cos(a)
    const g = tableGeom(t)
    if (t.kind === 'round') { if (lx * lx + ly * ly <= (g.desk.r! + 4) ** 2) return t }
    else if (Math.abs(lx) <= g.desk.w! / 2 + 3 && Math.abs(ly) <= g.desk.h! / 2 + 3) return t
  }
  return null
}
/* 禁用座位：右键切换；禁用后不参与排座/指派 */
function onContextmenu(e: MouseEvent) {
  e.preventDefault()
  const { sx, sy } = canvasPos(e), w = screenToWorld(sx, sy), hs = hitSeat(store.venue.tables, w.x, w.y)
  if (!hs) return
  const D = store.venue.disabled, i = D.indexOf(hs.s.key)
  if (i >= 0) D.splice(i, 1)
  else { D.push(hs.s.key); delete store.venue.assign[hs.s.key]; if (store.venue.selSeat === hs.s.key) store.venue.selSeat = null }
  store.save(); renderSeat()
}
function onCanvasPointermove(e: PointerEvent) {
  if (!canvasDrag) return
  const { sx, sy } = canvasPos(e), w = screenToWorld(sx, sy)
  if (canvasDrag.mode === 'pan') {
    store.venue.view.x = canvasDrag.vx + (sx - canvasDrag.sx)
    store.venue.view.y = canvasDrag.vy + (sy - canvasDrag.sy)
    renderSeat()
  } else if (canvasDrag.mode === 'table') {
    const dg = canvasDrag
    const t = store.venue.tables.find(x => x.id === dg.id)
    if (t) { t.x = Math.round(w.x - dg.ox); t.y = Math.round(w.y - dg.oy); renderSeat() }
  } else if (canvasDrag.mode === 'person') {
    dragGhost = w
    let hs = hitSeat(store.venue.tables, w.x, w.y)
    if (hs && store.venue.disabled.includes(hs.s.key)) hs = null
    store.venue.selSeat = hs ? hs.s.key : null
    renderSeat()
  }
}
function onCanvasPointerup(e: PointerEvent) {
  if (!canvasDrag) return
  const { sx, sy } = canvasPos(e), w = screenToWorld(sx, sy)
  if (canvasDrag.mode === 'person') {
    let hs = hitSeat(store.venue.tables, w.x, w.y)
    if (hs && store.venue.disabled.includes(hs.s.key)) hs = null
    const A = store.venue.assign
    if (hs && hs.s.key !== canvasDrag.fromKey) {
      const pf = A[canvasDrag.fromKey], pt = A[hs.s.key]   // 移动或互换
      if (pt) A[canvasDrag.fromKey] = pt; else delete A[canvasDrag.fromKey]
      if (pf) A[hs.s.key] = pf
    } else if (!hs) { delete store.venue.assign[canvasDrag.fromKey] }   // 拖到空白/禁用座撤销
    dragGhost = null; store.save(); renderSeat()
  } else if (canvasDrag.mode === 'pan') { canvasRef.value!.style.cursor = 'grab'; store.save() }
  else store.save()
  canvasDrag = null
}
function onCanvasDblclick(e: MouseEvent) {
  const { sx, sy } = canvasPos(e), w = screenToWorld(sx, sy), hs = hitSeat(store.venue.tables, w.x, w.y)
  if (hs) { delete store.venue.assign[hs.s.key]; store.save(); renderSeat() }
}
function onWheel(e: WheelEvent) {
  e.preventDefault()
  const v = store.venue, { sx, sy } = canvasPos(e)
  v.zoom = Math.min(4, Math.max(.01, v.zoom * Math.exp(-e.deltaY * .0012)))
  const w = screenToWorld(sx, sy)
  v.view.x = sx - w.x * v.zoom * V.PXM
  v.view.y = sy - w.y * v.zoom * V.PXM
  renderSeat()
}

function onKeydown(e: KeyboardEvent) {
  if (store.activeTab !== 'seat') return
  const tag = (e.target as HTMLElement)?.tagName
  if ((e.key === 'Delete' || e.key === 'Backspace') && store.venue.sel && tag !== 'INPUT' && tag !== 'TEXTAREA')
    delTable(store.venue.sel)
}
function onResize() { if (store.activeTab === 'seat') renderSeat() }

onMounted(() => {
  const canvas = canvasRef.value!
  ctx = canvas.getContext('2d')
  canvas.addEventListener('mousedown', onCanvasMousedown)
  canvas.addEventListener('pointerdown', onCanvasPointerdown)
  canvas.addEventListener('pointermove', onCanvasPointermove)
  canvas.addEventListener('pointerup', onCanvasPointerup)
  canvas.addEventListener('dblclick', onCanvasDblclick)
  canvas.addEventListener('contextmenu', onContextmenu)
  canvas.addEventListener('wheel', onWheel, { passive: false })
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('resize', onResize)
  canvas.style.cursor = 'grab'
  requestAnimationFrame(renderSeat)
})
onUnmounted(() => {
  const canvas = canvasRef.value
  if (canvas) {
    canvas.removeEventListener('mousedown', onCanvasMousedown)
    canvas.removeEventListener('pointerdown', onCanvasPointerdown)
    canvas.removeEventListener('pointermove', onCanvasPointermove)
    canvas.removeEventListener('pointerup', onCanvasPointerup)
    canvas.removeEventListener('dblclick', onCanvasDblclick)
    canvas.removeEventListener('contextmenu', onContextmenu)
    canvas.removeEventListener('wheel', onWheel)
  }
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('resize', onResize)
})

/* ================= 桌子 CRUD ================= */
let nextTid = 1
function addTable(kind: 'long' | 'round' | 'podium') {
  const no = store.venue.tables.reduce((m, t) => Math.max(m, t.no), 0) + 1
  const t: VTable = {
    id: 't' + (nextTid++) + '_' + Date.now().toString(36), no, kind, x: 80, y: 70, rot: 0, flip: false,
    seatsA: kind === 'round' ? 10 : kind === 'podium' ? 7 : 6, seatsB: kind === 'long' ? 6 : 0,
  }
  // 自动避开已放置的桌子：4 列网格找第一个不重叠的空位（AABB 近似，含座位余量）
  const half = (tb: VTable) => {
    const g = tableGeom(tb), w = g.desk.w || 2 * (g.desk.r || 0), h = g.desk.h || 2 * (g.desk.r || 0)
    return [w / 2 + 50, h / 2 + 50] as const
  }
  const [hw, hh] = half(t)
  let ok = !store.venue.tables.length
  for (let row = 0; row < 60 && !ok; row++) for (let col = 0; col < 4 && !ok; col++) {
    const x = 80 + col * (2 * hw + 60), y = 70 + row * (2 * hh + 60)
    if (!store.venue.tables.some(o => { const [ow, oh] = half(o); return Math.abs(o.x - x) < hw + ow && Math.abs(o.y - y) < hh + oh })) {
      t.x = Math.round(x); t.y = Math.round(y); ok = true
    }
  }
  store.venue.tables.push(t)
  store.venue.sel = t.id
  store.save()
  // 视角平移到新桌子（zoom 保持不变，仅移动 view）；rAF 下一帧布局完全稳定后再取 rect
  renderSeat()
  requestAnimationFrame(() => {
    const r = canvasRef.value?.getBoundingClientRect()
    if (!r) return
    store.venue.view.x = Math.round(r.width / 2 - t.x * store.venue.zoom * V.PXM)
    store.venue.view.y = Math.round(r.height / 2 - t.y * store.venue.zoom * V.PXM)
    renderSeat()
  })
}
function normalizeNos() {
  const ts = [...store.venue.tables].sort((a, b) => (a.no - b.no) || ((a.id < b.id) ? -1 : 1))
  ts.forEach((t, i) => (t.no = i + 1))
}
function delTable(id: string) {
  const i = store.venue.tables.findIndex(t => t.id === id)
  if (i < 0) return
  store.venue.tables.splice(i, 1)
  for (const k in store.venue.assign) if (k.startsWith(id + ':')) delete store.venue.assign[k]
  store.venue.disabled = store.venue.disabled.filter(k => !k.startsWith(id + ':'))
  if (store.venue.sel === id) store.venue.sel = null
  normalizeNos(); store.save(); renderSeat()
}
function moveNo(id: string, dir: number) {
  const ts = [...store.venue.tables].sort((a, b) => a.no - b.no)
  const i = ts.findIndex(t => t.id === id), j = i + dir
  if (i < 0 || j < 0 || j >= ts.length) return
  const tmp = ts[i]!.no
  ts[i]!.no = ts[j]!.no
  ts[j]!.no = tmp
  normalizeNos(); store.save(); renderSeat()
}

/* ================= 一键排座 / 清空 ================= */
function autoSeat() {
  if (!store.people.length) { toast.warning('名单为空'); return }
  const order = venueOrder(store.venue)
  if (!order.length) { toast.warning('请先添加桌子'); return }
  store.venue.assign = {}
  order.forEach((o, i) => { if (i < store.people.length) store.venue.assign[o.key] = store.people[i]!.id })
  store.save(); renderSeat()
}
async function clearSeat() { store.venue.assign = {}; store.save(); renderSeat() }
async function clearTables() {
  if (!store.venue.tables.length) return
  const ok = await confirmDialog('清除全部桌子', '确定清除全部桌子？排座与禁用状态将一并清除（名单保留）。', { danger: true })
  if (!ok) return
  store.venue.tables = []; store.venue.assign = {}; store.venue.disabled = []
  store.venue.sel = null; store.venue.selSeat = null
  store.save(); renderSeat()
}

/* ================= 打印 / 导出 PNG（按当前画布 zoom 输出：所见即所得；打印不小于铺满 A4 的比例） ================= */
function renderHiRes(ppmm: number, mode: 'print' | 'png'): HTMLCanvasElement & { _wmm?: number; _hmm?: number } {
  const c = document.createElement('canvas') as HTMLCanvasElement & { _wmm?: number; _hmm?: number }
  if (!store.venue.tables.length) {
    c.width = 297 * ppmm; c.height = 210 * ppmm; c._wmm = 297; c._hmm = 210
    const g = c.getContext('2d')!
    g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height)
    g.fillStyle = '#999'; g.font = 20 * ppmm + 'px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'
    g.fillText('（空会场）', c.width / 2, c.height / 2)
    return c
  }
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9
  for (const t of store.venue.tables) {
    const gm = tableGeom(t), dw = gm.desk.w || 2 * (gm.desk.r || 0), dh = gm.desk.h || 2 * (gm.desk.r || 0)
    const m = Math.hypot(dw, dh) / 2 + 45   // 任意旋转角度下桌子最大半径 + 座位/人名余量
    x0 = Math.min(x0, t.x - m); y0 = Math.min(y0, t.y - m); x1 = Math.max(x1, t.x + m); y1 = Math.max(y1, t.y + m)
  }
  const w = x1 - x0, h = y1 - y0, z = store.venue.zoom || 1
  // 缩放：世界 mm → 纸面 mm。PNG 按当前 zoom（屏幕观感 1:1）；打印至少铺满 A4 可打印区（281x194mm，四周留 4mm 边距）
  const sFit = Math.min((297 - 8 - 8) / w, (210 - 8 - 8) / h)
  const s = mode === 'png' ? z : Math.max(z, sFit)
  const wmm = w * s + 8, hmm = h * s + 8
  if (mode === 'png') ppmm = Math.max(3, Math.min(ppmm, 9000 / Math.max(wmm, hmm)))   // 防超大画布
  c.width = Math.round(wmm * ppmm); c.height = Math.round(hmm * ppmm); c._wmm = wmm; c._hmm = hmm
  const g = c.getContext('2d')!
  g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height)
  const ox = (4 - x0 * s) * ppmm, oy = (4 - y0 * s) * ppmm, k = s * ppmm
  const nos = noMapForTable()
  for (const t of [...store.venue.tables].sort((a, b) => a.no - b.no)) {
    g.translate(ox, oy); g.scale(k, k); drawTable(g, t, nos); g.setTransform(1, 0, 0, 1, 0, 0)
  }
  return c
}
function printSeat() {
  setPageStyle('@page{size:A4 landscape;margin:8mm}')
  const pa = document.getElementById('print-area')!
  pa.innerHTML = ''
  const c = renderHiRes(8, 'print')
  const sc = Math.min(1, 281 / (c._wmm || 1), 194 / (c._hmm || 1))   // 超出 A4 可打印区时等比缩回
  c.style.cssText = `width:${((c._wmm || 0) * sc).toFixed(1)}mm;max-width:100%;display:block;margin:0 auto`
  pa.appendChild(c)
  document.body.classList.remove('print-sign')
  document.body.classList.add('print-seat')
  window.print()
}
function exportPNG() {
  renderHiRes(10, 'png').toBlob(b => {
    if (!b) return
    const a = document.createElement('a')
    a.href = URL.createObjectURL(b); a.download = '会场座位示意图.png'; a.click()
  })
}

/* 侧栏子组件可用的画布 API（拖人入画布 / 载入会议室后适应等） */
provide('seatApi', {
  renderSeat, zoomFit, delTable, moveNo,
  worldFromClient(clientX: number, clientY: number) {
    const r = canvasRef.value!.getBoundingClientRect()
    return screenToWorld(clientX - r.left, clientY - r.top)
  },
  inCanvas(clientX: number, clientY: number) {
    const r = canvasRef.value?.getBoundingClientRect()
    if (!r) return false
    return clientX >= r.left && clientX <= r.right && clientY >= r.top && clientY <= r.bottom
  },
  hitSeatWorld(wx: number, wy: number) { return hitSeat(store.venue.tables, wx, wy) },
  setSelSeat(key: string | null) { store.venue.selSeat = key },
  setDragGhost(w: { x: number; y: number } | null) { dragGhost = w },
})
</script>

<template>
  <div class="seat-layout flex items-start gap-4">
    <div class="flex min-w-0 flex-1 flex-col gap-3">
      <Card>
        <CardHeader class="pb-3"><CardTitle class="text-base">会场编辑</CardTitle></CardHeader>
        <CardContent class="space-y-2">
          <div class="flex flex-wrap items-center gap-2 text-[13px]">
            <Button id="btn-add-long" size="sm" @click="addTable('long')">＋ 长条桌</Button>
            <Button id="btn-add-round" size="sm" @click="addTable('round')">＋ 圆桌</Button>
            <Button id="btn-add-podium" size="sm" @click="addTable('podium')">＋ 主席台</Button>
            <span class="w-3"></span>
            <Button id="btn-zoom-out" variant="outline" size="sm" @click="store.venue.zoom = Math.max(.01, store.venue.zoom / 1.25); renderSeat(); store.save()">➖</Button>
            <span class="min-w-[48px] text-center">{{ zoomLabel }}</span>
            <Button id="btn-zoom-in" variant="outline" size="sm" @click="store.venue.zoom = Math.min(4, store.venue.zoom * 1.25); renderSeat(); store.save()">➕</Button>
            <Button id="btn-zoom-fit" variant="outline" size="sm" @click="zoomFit(); store.save()">⤢ 适应</Button>
            <Label class="flex items-center gap-1.5 font-normal">
              <input type="checkbox" id="seat-show-no" v-model="store.venue.showNo" class="size-4 accent-zinc-900"
                @change="store.save(); renderSeat()">
              礼宾序号
            </Label>
            <span class="w-3"></span>
            <Button id="btn-auto-seat" size="sm" @click="autoSeat">⚡ 按名单顺序一键排座</Button>
            <Button id="btn-clear-seat" variant="outline" size="sm" @click="clearSeat">清空座位</Button>
            <Button id="btn-print-seat" size="sm" @click="printSeat">🖨 打印示意图</Button>
            <Button id="btn-export-png" variant="outline" size="sm" @click="exportPNG">导出 PNG</Button>
          </div>
          <p class="text-[13px] leading-relaxed text-muted-foreground">
            桌型三种：长条桌（对坐）、圆桌、主席台。<b>拖动桌子</b>调整位置，选中桌子后在「桌子属性」里调座位数 / 旋转 /
            翻转；滚轮缩放，拖空白平移。<br>
            排座：<b>点击名单即自动指派到第一个空位</b>（或先点座位再点名单指定座位）；<b>把右侧名单中的人拖到座位上</b>即指派；<b>拖座位上的人</b>到另一座位为移动（两人互换）；拖到空白处撤销；双击座位清空；<b>右键座位
            = 禁用/恢复</b>（灰色斜纹座不参与排座）。序号规则：1 号位居中，2 号位在 1 号领导左手侧（图面右侧），依次向两侧展开，可用每桌「翻转」切换朝向。<br>
            <b>导出/导入备份</b>（页面右上角）：把当前会场布局、排座、名单和会议室库存成文件备用或换电脑使用；导入后自动保存在浏览器里（刷新不丢）。「恢复默认」重置台签/座位设置（名单保留）。
          </p>
        </CardContent>
      </Card>
      <div class="seat-canvas-wrap relative overflow-hidden rounded-lg border bg-[#eef0f4]"
        style="height:640px;max-height:calc(100vh - 230px)">
        <canvas id="seat-canvas" ref="canvasRef" class="block h-full w-full touch-none"></canvas>
        <div class="canvas-ops absolute right-3 top-3 flex gap-1.5">
          <button id="btn-undo" title="撤销（Ctrl/Cmd+Z）" :disabled="!store.canUndo"
            class="flex size-8 items-center justify-center rounded-full border bg-background shadow-sm transition-colors hover:bg-muted disabled:opacity-40"
            @click="store.undo()">↶</button>
          <button id="btn-redo" title="重做（Ctrl/Cmd+Shift+Z）" :disabled="!store.canRedo"
            class="flex size-8 items-center justify-center rounded-full border bg-background shadow-sm transition-colors hover:bg-muted disabled:opacity-40"
            @click="store.redo()">↷</button>
        </div>
      </div>
    </div>

    <aside class="seat-side sticky top-4 flex w-[280px] flex-shrink-0 flex-col gap-3"
      style="max-height:calc(100vh - 32px);overflow-y:auto">
      <CollapsibleCard col="venue" title="会议室管理">
        <VenueLibCard />
      </CollapsibleCard>
      <CollapsibleCard col="tableprop" title="桌子属性">
        <TablePropCard />
      </CollapsibleCard>
      <CollapsibleCard col="tables" title="桌子管理（编号顺序）">
        <template #title-right>
          <Button variant="destructive" size="sm" class="h-6 px-1.5 py-0 text-xs" @click.stop="clearTables">全清</Button>
        </template>
        <TableFormCard />
      </CollapsibleCard>
      <CollapsibleCard col="people" title="名单（点击/拖拽指派）">
        <SeatPeopleCard />
      </CollapsibleCard>
    </aside>
  </div>
</template>
