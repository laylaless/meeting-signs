import type { Person } from '../types'

/* 姓名与职务用全角｜（半角 | 同样支持）分隔：姓名｜职务 */
export function parseLine(line: string, uid: () => string): Person | null {
  line = line.trim()
  if (!line) return null
  const m = line.match(/^([^｜|]+)(?:[｜|]+(.*))?$/)
  const name = (m?.[1] || '').trim()
  const title = (m?.[2] || '').trim()
  return { id: uid(), name, title }
}

/* 「自动替换」开启时：去除行内所有空白（半角/全角/tab，保留换行），「,」「，」「、」「\」自动分行 */
export function preprocessImport(raw: string, auto: boolean) {
  if (auto) raw = raw.replace(/[^\S\n]+/g, '').replace(/[、，,\\]/g, '\n')
  return raw.split(/\n+/).map(s => s.trim()).filter(Boolean)
}

export function importLines(raw: string, auto: boolean, uid: () => string): Person[] {
  return preprocessImport(raw, auto).map(l => parseLine(l, uid)).filter((p): p is Person => !!p)
}
