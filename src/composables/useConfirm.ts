import { ref } from 'vue'

/* 全局确认弹窗：替代原生 confirm()（阻塞式）改为 AlertDialog + Promise */
const state = ref({ open: false, title: '', desc: '', danger: false, confirmText: '确定' })
let resolver: ((v: boolean) => void) | null = null

export function confirmDialog(title: string, desc = '', opts: { danger?: boolean; confirmText?: string } = {}) {
  state.value = { open: true, title, desc, danger: !!opts.danger, confirmText: opts.confirmText || '确定' }
  return new Promise<boolean>(res => { resolver = res })
}

export function useConfirmState() { return state }

export function settleConfirm(v: boolean) {
  state.value.open = false
  resolver?.(v)
  resolver = null
}
