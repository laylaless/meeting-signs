import type { SeatBox } from '@/utils/venue'
import type { VTable } from '@/types'

/* SeatTab provide 给侧栏子组件的画布 API */
export interface SeatApi {
  renderSeat(): void
  zoomFit(): void
  delTable(id: string): void
  moveNo(id: string, dir: number): void
  worldFromClient(clientX: number, clientY: number): { x: number; y: number }
  inCanvas(clientX: number, clientY: number): boolean
  hitSeatWorld(wx: number, wy: number): { t: VTable; s: SeatBox } | null
  setSelSeat(key: string | null): void
  setDragGhost(w: { x: number; y: number } | null): void
}
