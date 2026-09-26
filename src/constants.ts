import type { FontKey, SignMode } from './types'

export const APP_VERSION = 'v0.3.0'

export const LS_KEY = 'meeting-signs-v4'
export const VENUES_KEY = 'meeting-signs-venues'
export const IMPORT_AUTO_KEY = 'meeting-signs-import-auto'
export const COLLAPSED_KEY = 'meeting-signs-collapsed'

/* 字体回退串：每项自带引号，输出到 font-family 时不能整体再包引号（0.2.4 修过的 bug） */
export const FONTS: Record<Exclude<FontKey, 'custom'>, string> = {
  zhongsong: "'WebZhongSong','STZhongsong','华文中宋','SimSun','Songti SC',serif",
  xinwei: "'STXinwei','华文新魏','XinWei',serif",
  fzqiu: "'FZQiuXinWeiBei','FZZJ-ZBQXWBJW','方正字迹-曾柏求新魏碑简体',serif",
  hei: "'SimHei','Heiti SC','Source Han Sans SC','PingFang SC',sans-serif",
  song: "'SimSun','Songti SC',serif",
  kai: "'KaiTi','Kaiti SC','STKaiti',serif",
  stkai: "'STKaiti','华文楷体','Kaiti SC','KaiTi',serif",
}

/* 台签纸 / 座位签模版 → @page 尺寸 */
export const PAGESIZE: Partial<Record<SignMode, string>> = {
  paper190: '190mm 178mm',
  qinchuan: '195mm 175mm',
  table200x120: '120mm 200mm',
  seatcard: 'A4 landscape',
}

/* 桌子几何常量（世界坐标单位 mm） */
export const V = { SEAT_W: 36, SEAT_H: 15, GAP: 4.2, DESK_LONG_H: 45, DESK_PODIUM_H: 30, PXM: 3.7795 }

export const KIND_NAME: Record<string, string> = { long: '长条桌', round: '圆桌', podium: '主席台' }
