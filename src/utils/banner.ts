import { FONTS } from '../constants'
import type { Banner } from '../types'

export function hexNorm(s: unknown, fb: string) {
  let v = String(s || '').trim()
  if (!v.startsWith('#')) v = '#' + v
  return /^#[0-9a-fA-F]{6}$/.test(v) ? v.toUpperCase() : fb
}

export function hex2rgb(h: string) {
  const v = hexNorm(h, '#000000')
  return [parseInt(v.slice(1, 3), 16), parseInt(v.slice(3, 5), 16), parseInt(v.slice(5, 7), 16)] as const
}

export function bnFont(b: Banner) {
  return b.font === 'custom' ? (b.customFont && b.customFont.trim() ? b.customFont.trim() : 'SimHei') : (FONTS[b.font] || FONTS.zhongsong)
}

/* 日期：存储统一 ISO（YYYY-MM-DD），画面渲染中文；旧版本中文字符串自动迁移 */
export function dateToISO(s: string) {
  if (!s) return ''
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s
  const m = String(s).match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?/)
  if (m) return `${m[1]}-${String(m[2]).padStart(2, '0')}-${String(m[3]).padStart(2, '0')}`
  const d = new Date(s)
  return isNaN(d.getTime()) ? '' : `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export function isoToCN(iso: string) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '')
  return m ? `${+m[1]!}年${+m[2]!}月${+m[3]!}日` : (iso || '')
}

export function bnShadowCss(b: Banner, k: number) {
  const s = b.shadow || { color: '#000000', opacity: 0, angle: 0, dist: 0, blur: 0 }
  const a = (Number(s.angle) || 0) * Math.PI / 180
  const x = ((Number(s.dist) || 0) * Math.cos(a) * 4 / 3 * k).toFixed(1)
  const y = ((Number(s.dist) || 0) * Math.sin(a) * 4 / 3 * k).toFixed(1)
  const bl = ((Number(s.blur) || 0) * 4 / 3 * k).toFixed(1)
  const [r, g, bb] = hex2rgb(s.color)
  return `${x}px ${y}px ${bl}px rgba(${r},${g},${bb},${(1 - (Number(s.opacity) || 0) / 100).toFixed(2)})`
}

/* 画面渲染：一切按画面高度/1080 等比（k = clientHeight/1080，pt→px 系数 4/3），
   字号/间距/偏移/阴影全部乘 k —— 预览、全屏、任意屏幕比例下视觉占比恒定 */
export function bnRenderStage(el: HTMLElement, b: Banner) {
  const k = (el.clientHeight || 540) / 1080
  el.style.background = b.bg
  el.innerHTML = ''
  const fam = bnFont(b)   // 完整回退串（每项自带引号），不能再整体包引号，否则会被解析成一个非法字体名
  const sp = (b.spacing == null ? 3 : b.spacing) * 4 / 3 * k
  const lh = String(b.lineH == null ? 1.5 : b.lineH)
  const t = document.createElement('pre')
  t.className = 'bn-title'
  t.textContent = b.title || ''
  t.style.cssText = `font-family:${fam};color:${b.fg};font-size:${(b.titleSize * 4 / 3 * k).toFixed(2)}px;text-shadow:${bnShadowCss(b, k)};transform:translateY(${((b.titleOff || 0) * 4 / 3 * k).toFixed(1)}px);letter-spacing:${sp.toFixed(2)}px;line-height:${lh}`
  el.appendChild(t)
  const d = document.createElement('div')
  d.className = 'bn-date'
  d.textContent = isoToCN(b.date)
  d.style.cssText = `font-family:${fam};color:${b.fg};font-size:${(b.dateSize * 4 / 3 * k).toFixed(2)}px;text-shadow:${bnShadowCss(b, k)};transform:translateY(${((b.dateOff || 0) * 4 / 3 * k).toFixed(1)}px);letter-spacing:${sp.toFixed(2)}px;line-height:${lh}`
  el.appendChild(d)
}
