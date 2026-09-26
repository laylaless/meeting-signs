import { toast } from 'vue-sonner'
import { loadVenues, saveVenues, useAppStore } from '../store'
import { defaultVenue } from '../store'
import type { VenueBackup } from '../types'
import { confirmDialog } from '../composables/useConfirm'

/* 导出会场配置 JSON（含名单、布局、排座、会议室库） */
export function exportBackup() {
  const store = useAppStore()
  const data: VenueBackup = {
    app: 'meeting-signs', format: 'venue', version: 4, exportedAt: new Date().toISOString(),
    people: store.people, nextPid: store.nextPid,
    venue: {
      tables: store.venue.tables, assign: store.venue.assign, disabled: store.venue.disabled,
      showNo: store.venue.showNo, zoom: store.venue.zoom, view: store.venue.view,
    },
    banners: store.banners,
    venueLib: loadVenues(),
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  const t = new Date(), p = (n: number) => String(n).padStart(2, '0')
  a.download = `会场配置_${t.getFullYear()}${p(t.getMonth() + 1)}${p(t.getDate())}_${p(t.getHours())}${p(t.getMinutes())}.json`
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 3000)
}

export async function importBackupFile(f: File) {
  const store = useAppStore()
  let d: VenueBackup
  try {
    d = JSON.parse(await f.text())
  } catch (err) {
    toast.error('文件不是有效的 JSON：' + (err as Error).message)
    return
  }
  if (!d || d.format !== 'venue' || !Array.isArray(d.people) || !d.venue || !Array.isArray(d.venue.tables)) {
    toast.error('这不是本应用导出的会场配置文件（缺少 format:venue / people / venue 数据）。')
    return
  }
  const ok = await confirmDialog(
    `导入「${f.name}」`,
    `名单 ${d.people.length} 人，桌子 ${d.venue.tables.length} 张${Array.isArray(d.venueLib) && d.venueLib.length ? `，会议室库 ${d.venueLib.length} 个（同名覆盖、新的追加）` : ''}。\n将替换当前的名单、会场布局和排座结果，确定？`,
  )
  if (!ok) return
  store.people = d.people
  store.nextPid = d.nextPid || d.people.reduce((m, p) => Math.max(m, Number(p.id?.slice(1)) || 0), 0) + 1
  store.venue = {
    ...defaultVenue(),
    tables: d.venue.tables, assign: d.venue.assign || {},
    disabled: Array.isArray(d.venue.disabled) ? d.venue.disabled : [],
    showNo: d.venue.showNo !== false, zoom: d.venue.zoom || 1, view: d.venue.view || { x: 40, y: 30 },
  }
  store.sign.excluded = []
  // 会标：随文件恢复（旧文件无此字段则不动本机会标）
  if (d.banners && Array.isArray(d.banners.list) && d.banners.list.length) {
    store.banners = { list: d.banners.list, sel: Math.min(d.banners.sel || 0, d.banners.list.length - 1) }
  }
  // 会议室库：同名覆盖、不同名追加（旧文件无此字段则不动本机库）
  if (Array.isArray(d.venueLib) && d.venueLib.length) {
    const lib = loadVenues()
    d.venueLib.forEach(v => {
      if (v && v.name && Array.isArray(v.tables)) {
        const old = lib.find(x => x.name === v.name)
        if (old) Object.assign(old, v)
        else lib.push(v)
      }
    })
    saveVenues(lib)
  }
  store.save()   // 立即存入浏览器 localStorage，刷新不丢
  toast.success('导入成功，已保存在浏览器里。')
}
