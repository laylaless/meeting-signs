/* 数据结构与旧版 v0.2.20 完全一致（localStorage / 备份 JSON 互通） */

export interface Person {
  id: string
  name: string
  title: string
}

export type SignMode =
  | 'standard'
  | 'paper190'
  | 'qinchuan'
  | 'table200x120'
  | 'seatcard'
  | 'fold'
  | 'strip'

export type FontKey =
  | 'zhongsong'
  | 'xinwei'
  | 'fzqiu'
  | 'hei'
  | 'song'
  | 'kai'
  | 'stkai'
  | 'custom'

export interface SignConfig {
  mode: SignMode
  perPage: number
  size: number
  font: FontKey
  customFont: string
  showTitle: boolean
  bold: boolean
  excluded: string[]
}

export type TableKind = 'long' | 'round' | 'podium'

export interface VTable {
  id: string
  no: number
  kind: TableKind
  x: number
  y: number
  rot: number
  flip: boolean
  seatsA: number
  seatsB: number
  seatsL?: number
  seatsR?: number
  seatsE?: number // 旧数据：左右端面座位数
}

export interface VenueState {
  tables: VTable[]
  assign: Record<string, string> // 座位 key -> 人员 id
  disabled: string[] // 禁用座位 key
  sel: string | null
  selSeat: string | null
  showNo: boolean
  zoom: number
  view: { x: number; y: number }
}

export interface BannerShadow {
  color: string
  opacity: number
  angle: number
  dist: number
  blur: number
}

export interface Banner {
  id: string
  title: string
  date: string
  bg: string
  fg: string
  titleSize: number
  dateSize: number
  font: FontKey
  customFont: string
  titleOff: number
  dateOff: number
  spacing: number
  lineH: number
  shadow: BannerShadow
}

export interface BannersState {
  list: Banner[]
  sel: number
  ratio?: string
}

export interface VenueLibItem {
  id: string
  name: string
  tables: VTable[]
  showNo?: boolean
  savedAt?: number
}

/* 备份 JSON（format: 'venue'） */
export interface VenueBackup {
  app: string
  format: string
  version: number
  exportedAt: string
  people: Person[]
  nextPid?: number
  venue: {
    tables: VTable[]
    assign: Record<string, string>
    disabled: string[]
    showNo: boolean
    zoom: number
    view: { x: number; y: number }
  }
  banners?: BannersState
  venueLib?: VenueLibItem[]
}
