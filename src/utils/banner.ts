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

/* 逐字横向缩放（书法式瘦长）：每个字单独包 inline-block span 各自 scaleX、比例一致，
   字与字的间距（letter-spacing）不参与缩放——整行不会缩成一团聚在中间；
   默认 100% 不拆 span，保持纯文本节点（transform 仍留给元素自身的 translateY） */
function scaleChars(el: HTMLElement, text: string, sx: number) {
  if (sx === 1) { el.textContent = text; return }
  const frag = document.createDocumentFragment()
  for (const ch of text) {
    if (ch === '\n') { frag.appendChild(document.createTextNode('\n')); continue }
    const s = document.createElement('span')
    s.textContent = ch
    s.style.cssText = `display:inline-block;transform:scaleX(${sx})`
    frag.appendChild(s)
  }
  el.appendChild(frag)
}

/* 导出 PNG：用 Canvas 2D 按上面同一套参数离屏重绘（不引截图库，字体仍走系统回退串）。
   固定 2160 高（16:9=3840×2160、4:3=2880×2160），布局百分比与 bnRenderStage 一致：
   标题 top 25%（pre 加粗、行高 lh）、日期 bottom 15%，均水平居中、逐字 scaleX、字距加在每字之后 */
export function exportBannerPng(b: Banner, r43: boolean) {
  const H = 2160
  const W = Math.round(r43 ? H * 4 / 3 : H * 16 / 9)
  const cv = document.createElement('canvas')
  cv.width = W; cv.height = H
  const ctx = cv.getContext('2d')!
  const k = H / 1080

  ctx.fillStyle = hexNorm(b.bg, '#A52615')
  ctx.fillRect(0, 0, W, H)

  const fam = bnFont(b)
  const sp = (b.spacing == null ? 0 : b.spacing) * 4 / 3 * k
  const lh = b.lineH == null ? 1.5 : b.lineH
  const sx = (b.scaleX == null ? 80 : b.scaleX) / 100
  const s = b.shadow || { color: '#000000', opacity: 0, angle: 0, dist: 0, blur: 0 }
  const ang = (Number(s.angle) || 0) * Math.PI / 180
  const [r, g, bl] = hex2rgb(s.color)
  ctx.fillStyle = b.fg
  ctx.shadowColor = `rgba(${r},${g},${bl},${(1 - (Number(s.opacity) || 0) / 100).toFixed(2)})`
  // DOM 里阴影随 span 一起 scaleX，canvas 的 shadowOffset 不受变换影响，故 X 方向手动乘 sx 对齐
  ctx.shadowOffsetX = (Number(s.dist) || 0) * Math.cos(ang) * 4 / 3 * k * sx
  ctx.shadowOffsetY = (Number(s.dist) || 0) * Math.sin(ang) * 4 / 3 * k
  ctx.shadowBlur = (Number(s.blur) || 0) * 4 / 3 * k

  /* 单行逐字：每字按原字宽占位（letter-spacing 跟在字后、含末尾，与 CSS 居中一致），
     绕字身中心 scaleX；baseline 按行盒 half-leading 模型由字体度量推算 */
  function drawLine(text: string, fs: number, weight: number, lineTop: number) {
    if (!text) return
    ctx.font = `${weight} ${fs}px ${fam}`
    const chars = [...text]
    const widths = chars.map(ch => ctx.measureText(ch).width)
    const total = widths.reduce((a, w) => a + w, 0) + chars.length * sp
    let x = (W - total) / 2
    const m = ctx.measureText('国')
    const asc = m.fontBoundingBoxAscent ?? fs * 0.86
    const desc = m.fontBoundingBoxDescent ?? fs * 0.14
    const baseline = lineTop + (lh * fs - asc - desc) / 2 + asc
    for (let i = 0; i < chars.length; i++) {
      if (chars[i] !== ' ') {
        ctx.save()
        ctx.translate(x + widths[i]! / 2, baseline)
        ctx.scale(sx, 1)
        ctx.fillText(chars[i]!, -widths[i]! / 2, 0)
        ctx.restore()
      }
      x += widths[i]! + sp
    }
  }

  const tfs = b.titleSize * 4 / 3 * k
  const tTop = H * 0.25 + (b.titleOff || 0) * 4 / 3 * k
  ;(b.title || '').split('\n').forEach((ln, i) => drawLine(ln, tfs, 700, tTop + i * lh * tfs))
  const dfs = b.dateSize * 4 / 3 * k
  drawLine(isoToCN(b.date), dfs, 400, H * 0.85 - lh * dfs + (b.dateOff || 0) * 4 / 3 * k)

  const name = (b.title || '').split('\n')[0]!.replace(/[\\/:*?"<>|\s]+/g, '').slice(0, 20) || '未命名'
  cv.toBlob(blob => {
    if (!blob) return
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `会标_${name}${b.date ? '_' + b.date : ''}.png`
    a.click()
    setTimeout(() => URL.revokeObjectURL(a.href), 5000)
  })
}

/* 画面渲染：一切按画面高度/1080 等比（k = clientHeight/1080，pt→px 系数 4/3），
   字号/间距/偏移/阴影全部乘 k —— 预览、全屏、任意屏幕比例下视觉占比恒定 */
export function bnRenderStage(el: HTMLElement, b: Banner) {
  const k = (el.clientHeight || 540) / 1080
  el.style.background = b.bg
  el.innerHTML = ''
  const fam = bnFont(b)   // 完整回退串（每项自带引号），不能再整体包引号，否则会被解析成一个非法字体名
  const sp = (b.spacing == null ? 0 : b.spacing) * 4 / 3 * k
  const lh = String(b.lineH == null ? 1.5 : b.lineH)
  const sx = (b.scaleX == null ? 80 : b.scaleX) / 100   // 横向缩放百分比（竖向不变；默认 80）
  const t = document.createElement('pre')
  t.className = 'bn-title'
  t.style.cssText = `font-family:${fam};color:${b.fg};font-size:${(b.titleSize * 4 / 3 * k).toFixed(2)}px;text-shadow:${bnShadowCss(b, k)};transform:translateY(${((b.titleOff || 0) * 4 / 3 * k).toFixed(1)}px);letter-spacing:${sp.toFixed(2)}px;line-height:${lh}`
  scaleChars(t, b.title || '', sx)
  el.appendChild(t)
  const d = document.createElement('div')
  d.className = 'bn-date'
  d.style.cssText = `font-family:${fam};color:${b.fg};font-size:${(b.dateSize * 4 / 3 * k).toFixed(2)}px;text-shadow:${bnShadowCss(b, k)};transform:translateY(${((b.dateOff || 0) * 4 / 3 * k).toFixed(1)}px);letter-spacing:${sp.toFixed(2)}px;line-height:${lh}`
  scaleChars(d, isoToCN(b.date), sx)
  el.appendChild(d)
}
