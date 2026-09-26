import { FONTS } from '../constants'
import type { Person, SignConfig } from '../types'
import { esc } from './misc'

export function signFont(cfg: SignConfig) {
  // 自定义字体：直接使用输入的 font-family 名；为空回退华文新魏
  if (cfg.font === 'custom') return cfg.customFont && cfg.customFont.trim() ? cfg.customFont.trim() : FONTS.xinwei
  return FONTS[cfg.font] || FONTS.xinwei
}

export function autoFontSize(len: number, mode: string, perPage: number) {
  if (mode === 'standard' || mode === 'paper190' || mode === 'qinchuan') return 155   // 固定 155pt，超宽自动 scaleX 横向压缩，不换行
  if (mode === 'table200x120') return 96
  if (mode === 'seatcard') return Math.min(130, Math.round(567 / Math.max(len, 1)))   // 竖排：≤4 字 130pt，字多按 200mm 可用高度均分
  if (mode === 'fold') return len <= 2 ? 250 : len === 3 ? 220 : len === 4 ? 180 : len === 5 ? 150 : len === 6 ? 125 : 105
  const stripH = 297 / perPage                       // mm
  const base = Math.round(stripH * 0.42 * 2.835)     // mm→pt（1mm=2.835pt）
  const k = len <= 2 ? 1 : len === 3 ? .88 : len === 4 ? .74 : len === 5 ? .6 : .5
  return Math.round(base * k)
}

/* 生成打印/预览 HTML（与 v0.2.20 输出逐类名一致） */
export function buildSignHTML(cfg: SignConfig, people: Person[]): string {
  const font = signFont(cfg)
  const ppl = people.filter(p => !cfg.excluded.includes(p.id))
  const mk = (p: Person) => {
    // 2 字名中间加全角空格（座位签竖排不加）
    const label = cfg.mode === 'seatcard' ? p.name : (p.name.length === 2 ? p.name[0] + '　' + p.name[1] : p.name)
    const size = cfg.size > 0 ? cfg.size : autoFontSize(label.length, cfg.mode, cfg.perPage)
    if (cfg.mode === 'seatcard')
      return `<div class="seat-col"><div class="sign-name" style="font-family:${font};font-size:${size}pt;font-weight:${cfg.bold ? 700 : 400}">${[...p.name].map(c => esc(c)).join('<br>')}</div></div>`
    const titleSize = cfg.mode === 'standard' ? Math.round(size * .22) + 'pt' : ''
    const inner = `<div class="inner">${cfg.showTitle && p.title ? `<div class="sign-title"${titleSize ? ` style="font-size:${titleSize}"` : ''}>${esc(p.title)}</div>` : ''}<div class="sign-name" style="font-family:${font};font-size:${size}pt;font-weight:${cfg.bold ? 700 : 400}">${esc(label)}</div></div>`
    if (cfg.mode === 'standard') return `<div class="sheet"><div class="std-frame"><div class="std-half rev">${inner}</div><div class="std-half">${inner}</div></div></div>`
    if (cfg.mode === 'paper190') return `<div class="sheet" style="width:190mm;height:178mm"><div class="std-frame nofold" style="width:100%;height:100%"><div class="std-half rev">${inner}</div><div class="std-half">${inner}</div></div></div>`
    if (cfg.mode === 'qinchuan') return `<div class="sheet" style="width:195mm;height:175mm"><div class="std-frame nofold" style="width:100%;height:100%"><div class="std-half rev">${inner}</div><div class="std-half">${inner}</div></div></div>`
    if (cfg.mode === 'table200x120') return `<div class="sheet t200-card" style="width:120mm;height:200mm"><div class="t200-blank"></div><div class="t200-name rev">${inner}</div><div class="t200-name">${inner}</div><div class="t200-blank"></div></div>`
    if (cfg.mode === 'fold') return `<div class="sheet"><div class="fold-half rev">${inner}</div><div class="fold-half">${inner}</div></div>`
    const rowH = (296 / cfg.perPage).toFixed(2), halfH = (148 / cfg.perPage).toFixed(2)
    return `<div class="strip-row" style="height:${rowH}mm"><div class="strip-half rev" style="height:${halfH}mm">${inner}</div><div class="strip-half" style="height:${halfH}mm">${inner}</div></div>`
  }
  if (cfg.mode !== 'seatcard' && cfg.mode !== 'strip') return ppl.map(mk).join('')
  if (cfg.mode === 'seatcard') {   // 座位签：每页 1 行 5 列，不足 5 人后几列留空
    const pages = Math.ceil(ppl.length / 5)
    let out = ''
    for (let i = 0; i < pages; i++) {
      let inner = ''
      for (let j = 0; j < 5; j++) { const p = ppl[i * 5 + j]; if (p) inner += mk(p) }
      out += `<div class="sheet seat-sheet" style="width:297mm;height:209mm">${inner}</div>`
    }
    return out
  }
  const pages = Math.ceil(ppl.length / cfg.perPage)
  let out = ''
  for (let i = 0; i < pages; i++) {
    let inner = ''
    for (let j = 0; j < cfg.perPage; j++) {
      const p = ppl[i * cfg.perPage + j]
      if (p) inner += mk(p)
    }
    out += `<div class="sheet">${inner}</div>`
  }
  return out
}

/* 横向压缩：名字超宽时不换行，scaleX 压扁到框内（同 Word 艺术字横向缩放，字高不变） */
export function applySquash(root: HTMLElement | null) {
  if (!root) return
  const t200 = root.querySelector('.t200-card') as HTMLElement | null
  if (t200) squashNames(root, '.t200-name .sign-name', t200.offsetWidth - 15.1)  // 左右各缩进约 2mm
  const seatCol = root.querySelector('.seat-col') as HTMLElement | null
  if (seatCol) squashNames(root, '.seat-col .sign-name', seatCol.offsetWidth - 15.1)
  const frame = root.querySelector('.std-frame') as HTMLElement | null
  if (!frame) return
  squashNames(root, '.std-half .sign-name', frame.offsetWidth - 75.59)   // 左右各缩进 10mm（10mm=37.795px @96dpi）
}

function squashNames(root: HTMLElement, sel: string, avail: number) {
  root.querySelectorAll(sel).forEach(el => {
    const e = el as HTMLElement
    e.style.transform = ''
    e.style.transformOrigin = 'center center'
    const w = e.offsetWidth          // nowrap 下即单行自然宽（布局尺寸，不受祖先 transform 影响）
    if (w > avail) e.style.transform = `scaleX(${(avail / w).toFixed(4)})`
  })
}
