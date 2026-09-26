import { V } from '../constants'
import type { Person, VTable, VenueState } from '../types'

/* 全场礼宾序核心：返回位置索引数组，第 0 个 = 1 号位；mirror=true：1 号位不变，2 号换到另一侧 */
export function courtesyOrder(n: number, mirror: boolean) {
  const res: number[] = []
  if (n % 2 === 1) {
    const c = (n - 1) / 2
    for (let k = 0; k < n; k++) {
      if (k === 0) res.push(c)
      else if (k % 2 === 1) res.push(mirror ? c - (k + 1) / 2 : c + (k + 1) / 2)
      else res.push(mirror ? c + k / 2 : c - k / 2)
    }
  } else {
    const a = n / 2 - 1, b = n / 2
    if (!mirror) { for (let k = 0; k < n; k++) { if (k % 2 === 0) res.push(a - k / 2); else res.push(b + (k - 1) / 2) } }
    else {
      res.push(a); let left = a - 1, right = b, useLeft = true
      for (let k = 1; k < n; k++) {
        if (useLeft && left >= 0) res.push(left--)
        else res.push(right++)
        useLeft = !useLeft
      }
    }
  }
  return res
}

/* 圆桌：0=主位(底部中央)，2号=主位右手侧(画面右下)，再左右交替 */
export function ringOrder(n: number, mirror: boolean) {
  const res = [0]; let r = n - 1, l = 1
  while (res.length < n) { res.push(r--); if (res.length < n) res.push(l++) }
  return mirror ? res.map(p => (n - p) % n) : res
}

export interface SeatBox { key: string; i: number; side: string; x: number; y: number; w: number; h: number; ang?: number }
export interface TableGeom { seats: SeatBox[]; desk: { w?: number; h?: number; r?: number } }

/* 桌子局部坐标（中心原点，未旋转，mm） */
export function tableGeom(t: VTable): TableGeom {
  const seats: SeatBox[] = [], fx = (x: number) => t.flip ? -x : x
  if (t.kind === 'round') {
    const n = t.seatsA, R = 14 + 4 * n
    const cw = Math.min(V.SEAT_W, 2 * Math.PI * (R + 15) / n - 3)
    for (let i = 0; i < n; i++) {
      const ang = (90 + i * 360 / n) * Math.PI / 180
      seats.push({ key: t.id + ':r:' + i, i, side: 'r', x: fx((R + 15) * Math.cos(ang)), y: (R + 15) * Math.sin(ang), w: cw, h: V.SEAT_H, ang: 90 + i * 360 / n })
    }
    return { seats, desk: { r: R } }
  }
  if (t.kind === 'podium') {
    const n = t.seatsA, w = n * (V.SEAT_W + V.GAP) - V.GAP + 16, dw = w, dh = V.DESK_PODIUM_H
    for (let i = 0; i < n; i++) seats.push({ key: t.id + ':p:' + i, i, side: 'p', x: fx(-(w - 16) / 2 + V.SEAT_W / 2 + i * (V.SEAT_W + V.GAP)), y: -(dh / 2 + 15), w: V.SEAT_W, h: V.SEAT_H })
    return { seats, desk: { w: dw, h: dh } }
  }
  // long：上侧 seatsA / 下侧 seatsB 对坐 + 左右端面 seatsL/seatsR（各 0~50，单独控制）；桌高随端面座位数加长
  const n = Math.max(t.seatsA, t.seatsB), w = n * (V.SEAT_W + V.GAP) - V.GAP + 16, dw = w
  const nL = t.seatsL != null ? t.seatsL : (t.seatsE || 0), nR = t.seatsR != null ? t.seatsR : (t.seatsE || 0)
  const dh = Math.max(V.DESK_LONG_H, (Math.max(nL, nR) - 1) * (V.SEAT_H + V.GAP) + V.SEAT_H)
  for (let i = 0; i < t.seatsA; i++) seats.push({ key: t.id + ':a:' + i, i, side: 'a', x: fx(-(w - 16) / 2 + V.SEAT_W / 2 + i * (V.SEAT_W + V.GAP)), y: -(dh / 2 + 15), w: V.SEAT_W, h: V.SEAT_H })
  for (let i = 0; i < t.seatsB; i++) seats.push({ key: t.id + ':b:' + i, i, side: 'b', x: fx(-(w - 16) / 2 + V.SEAT_W / 2 + i * (V.SEAT_W + V.GAP)), y: (dh / 2 + 15), w: V.SEAT_W, h: V.SEAT_H })
  const mkEnds = (n: number, tag: string, sgn: number) => {
    for (let i = 0; i < n; i++)   // 竖排；1 个居桌侧中线，2 个上下错开
      seats.push({ key: t.id + ':' + tag + ':' + i, i, side: 'e', x: fx(sgn * (w / 2 + V.SEAT_W / 2 + V.GAP)), y: (i - (n - 1) / 2) * (V.SEAT_H + V.GAP), w: V.SEAT_W, h: V.SEAT_H })
  }
  mkEnds(nR, 'er', 1); mkEnds(nL, 'el', -1)
  return { seats, desk: { w: dw, h: dh } }
}

/* 全场礼宾序：桌按编号升序；桌内 courtesyOrder/ringOrder；返回 [{key,no}]（跳过禁用座） */
export function venueOrder(venue: VenueState) {
  const out: { key: string; no: number }[] = []
  let off = 0
  const tables = [...venue.tables].sort((a, b) => a.no - b.no)
  for (const t of tables) {
    const g = tableGeom(t)
    let idx: SeatBox[] = []
    if (t.kind === 'round') idx = ringOrder(t.seatsA, t.flip).map(p => g.seats.find(s => s.side === 'r' && s.i === p)!)
    else if (t.kind === 'podium') idx = courtesyOrder(t.seatsA, t.flip).map(p => g.seats.find(s => s.i === p)!)
    else {   // long：对坐礼宾——1 号正对对面最高位次，2 对对面第 3、3 对对面第 2（4v4 = 上3124/下6578）；端位排最后（视觉右端先、每端从上到下）
      const A = g.seats.filter(s => s.side === 'a'), B = g.seats.filter(s => s.side === 'b')
      idx = courtesyOrder(A.length, false).map(p => A[p]!)
      idx = idx.concat(courtesyOrder(B.length, true).map(p => B[p]!))
      idx = idx.concat(g.seats.filter(s => s.side === 'e').sort((p, q) => q.x - p.x || p.y - q.y))
    }
    const D = venue.disabled || []
    for (const s of idx) if (s && !D.includes(s.key)) out.push({ key: s.key, no: ++off })
  }
  return out
}

export function hitTable(tables: VTable[], wx: number, wy: number): VTable | null {
  for (const t of [...tables].sort((a, b) => b.no - a.no)) {
    const a = -t.rot * Math.PI / 180, dx = wx - t.x, dy = wy - t.y
    const lx = dx * Math.cos(a) - dy * Math.sin(a), ly = dx * Math.sin(a) + dy * Math.cos(a)
    const g = tableGeom(t)
    if (t.kind === 'round') { if (lx * lx + ly * ly <= (g.desk.r! + 4) ** 2) return t }
    else if (Math.abs(lx) <= g.desk.w! / 2 + 3 && Math.abs(ly) <= g.desk.h! / 2 + 3) return t
  }
  return null
}

export function hitSeat(tables: VTable[], wx: number, wy: number): { t: VTable; s: SeatBox } | null {
  for (const t of tables) {
    const a = -t.rot * Math.PI / 180, dx = wx - t.x, dy = wy - t.y
    const lx = dx * Math.cos(a) - dy * Math.sin(a), ly = dx * Math.sin(a) + dy * Math.cos(a)
    for (const s of tableGeom(t).seats)
      if (Math.abs(lx - s.x) <= s.w / 2 + 3 && Math.abs(ly - s.y) <= s.h / 2 + 3) return { t, s }
  }
  return null
}

export function seatPerson(assign: Record<string, string>, people: Person[], key: string) {
  const pid = assign[key]
  return pid ? people.find(p => p.id === pid) : null
}
