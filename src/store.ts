import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { LS_KEY, VENUES_KEY } from './constants'
import type { Banner, BannersState, Person, SignConfig, VenueLibItem, VenueState } from './types'

/* 首个会标 66/30 大字号，其余默认 32/24；所有默认样式与第一个一致 */
export function defaultBanner(titleSize?: number, dateSize?: number): Banner {
  const t = new Date()
  return {
    id: 'b' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    title: 'XX街道工作会议',
    date: `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`,
    bg: '#A52615', fg: '#FFFF00', titleSize: titleSize || 32, dateSize: dateSize || 24,
    font: 'zhongsong', customFont: '', titleOff: 0, dateOff: 0, spacing: 3, lineH: 1.5,
    shadow: { color: '#000000', opacity: 60, angle: 45, dist: 8, blur: 3 },
  }
}

export function defaultSign(): SignConfig {
  return { mode: 'standard', perPage: 4, size: 0, font: 'xinwei', customFont: '', showTitle: false, bold: false, excluded: [] }
}

export function defaultVenue(): VenueState {
  return { tables: [], assign: {}, disabled: [], sel: null, selSeat: null, showNo: true, zoom: 1, view: { x: 40, y: 30 } }
}

export function defaultBanners(): BannersState {
  return { list: [defaultBanner(66, 30), defaultBanner()], sel: 0 }
}

export function loadVenues(): VenueLibItem[] {
  try { return JSON.parse(localStorage.getItem(VENUES_KEY) || '') || [] } catch { return [] }
}
export function saveVenues(v: VenueLibItem[]) {
  try { localStorage.setItem(VENUES_KEY, JSON.stringify(v)) } catch { /* 忽略配额/隐私模式错误 */ }
}

const UNDO_MAX = 50

export const useAppStore = defineStore('app', () => {
  const people = ref<Person[]>([])
  const sign = ref<SignConfig>(defaultSign())
  const venue = ref<VenueState>(defaultVenue())
  const banners = ref<BannersState>(defaultBanners())
  const nextPid = ref(1)
  const activeTab = ref<'list' | 'sign' | 'seat' | 'banner'>('list')

  /* ---- 撤销/重做：状态快照栈（save 时若有变化，把前一版压栈；新操作清空重做栈） ---- */
  let undoStack: string[] = []
  let redoStack: string[] = []
  let lastSnap: string | null = null
  const undoLen = ref(0)
  const redoLen = ref(0)
  const canUndo = computed(() => undoLen.value > 0)
  const canRedo = computed(() => redoLen.value > 0)

  function stateJSON() {
    return JSON.stringify({ people: people.value, sign: sign.value, venue: venue.value, banners: banners.value, nextPid: nextPid.value })
  }
  function syncLens() { undoLen.value = undoStack.length; redoLen.value = redoStack.length }

  function save() {
    const now = stateJSON()
    if (lastSnap !== null && now !== lastSnap) {
      undoStack.push(lastSnap); redoStack = []
      if (undoStack.length > UNDO_MAX) undoStack.shift()
    }
    lastSnap = now
    syncLens()
    try { localStorage.setItem(LS_KEY, now) } catch { /* 忽略 */ }
  }

  function applyState(json: string) {
    const d = JSON.parse(json)
    people.value = d.people
    nextPid.value = d.nextPid || 1
    Object.assign(sign.value, d.sign || {})
    venue.value = d.venue
    if (d.banners && Array.isArray(d.banners.list) && d.banners.list.length) banners.value = d.banners
    lastSnap = stateJSON()
    try { localStorage.setItem(LS_KEY, lastSnap) } catch { /* 忽略 */ }
    syncLens()
  }

  function undo() { if (!undoStack.length) return; redoStack.push(stateJSON()); applyState(undoStack.pop()!) }
  function redo() { if (!redoStack.length) return; undoStack.push(stateJSON()); applyState(redoStack.pop()!) }

  /* v1→v4 旧数据迁移：v3 及更早只保名单+台签设置，会场 2.0 重新开始 */
  function load() {
    try {
      const v4 = localStorage.getItem(LS_KEY)
      const v3 = localStorage.getItem('meeting-signs-v3')
      const v2 = localStorage.getItem('meeting-signs-v2')
      const v1 = localStorage.getItem('meeting-signs-v1')
      const d = JSON.parse(v4 || v3 || v2 || v1 || '')
      if (d && d.people) {
        people.value = d.people
        nextPid.value = d.nextPid || d.people.length + 1
        if (v4) { Object.assign(sign.value, d.sign || {}); Object.assign(venue.value, d.venue || {}) }
        else if (v3) Object.assign(sign.value, d.sign || {})
      }
      if (d && d.banners && Array.isArray(d.banners.list) && d.banners.list.length) banners.value = d.banners
    } catch { /* 无数据或损坏：保持默认 */ }
  }

  function uid() { return 'p' + (nextPid.value++) }

  /* 除名单外的全部设置恢复默认（名单保留） */
  function restoreDefaults() {
    sign.value = defaultSign()
    venue.value = defaultVenue()
    banners.value = defaultBanners()   // 会标恢复默认（日期=当天）
    save()
  }

  return {
    people, sign, venue, banners, nextPid, activeTab,
    canUndo, canRedo,
    save, load, undo, redo, uid, applyState, restoreDefaults,
  }
})
