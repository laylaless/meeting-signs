export function clamp(v: number, a: number, b: number) { return Math.min(b, Math.max(a, v)) }

export function esc(s: unknown) {
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string))
}
