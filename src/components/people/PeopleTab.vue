<script setup lang="ts">
import { nextTick, onUnmounted, ref } from 'vue'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { IMPORT_AUTO_KEY } from '@/constants'
import { useAppStore } from '@/store'
import { confirmDialog } from '@/composables/useConfirm'
import { importLines } from '@/utils/people'

const store = useAppStore()

/* ---- 批量导入 ---- */
const importText = ref('')
const importAuto = ref(true)
try { const v = localStorage.getItem(IMPORT_AUTO_KEY); if (v !== null) importAuto.value = v === '1' } catch { /* 忽略 */ }
function persistAuto() {
  try { localStorage.setItem(IMPORT_AUTO_KEY, importAuto.value ? '1' : '0') } catch { /* 忽略 */ }
}

function importPeople(replace: boolean) {
  const np = importLines(importText.value, importAuto.value, () => store.uid())
  if (!np.length) { toast.warning('请先输入名单'); return }
  store.people = replace ? np : store.people.concat(np)
  importText.value = ''
  store.save()
}

async function clearPeople() {
  const ok = await confirmDialog('清空名单', '确定清空全部名单？', { danger: true })
  if (!ok) return
  store.people = []
  store.venue.assign = {}
  store.save()
}

/* ---- 行内改名：双击姓名 → 输入框（Enter/失焦保存，Esc 取消，留空保持原名） ---- */
const editingId = ref<string | null>(null)
const editingVal = ref('')
function startEdit(id: string, name: string) {
  editingId.value = id
  editingVal.value = name
  nextTick(() => {
    const inp = document.querySelector('#people-table td.pname input') as HTMLInputElement | null
    inp?.focus(); inp?.select()
  })
}
function commitEdit(ok: boolean) {
  const id = editingId.value
  if (!id) return
  const p = store.people.find(x => x.id === id)
  editingId.value = null
  if (!p) return
  const v = editingVal.value.trim()
  if (ok && v && v !== p.name) { p.name = v; store.save() }
}

/* ---- 表格操作：↑ ↓ 删 ---- */
function onRowAction(act: string, id: string) {
  const i = store.people.findIndex(p => p.id === id)
  if (i < 0) return
  const ps = store.people
  if (act === 'up' && i > 0) { const a = ps[i - 1]!; ps[i - 1] = ps[i]!; ps[i] = a }
  if (act === 'down' && i < ps.length - 1) { const b = ps[i + 1]!; ps[i + 1] = ps[i]!; ps[i] = b }
  if (act === 'del') {
    ps.splice(i, 1)
    for (const k in store.venue.assign) if (store.venue.assign[k] === id) delete store.venue.assign[k]
  }
  store.save()
}

/* ---- 按住行拖拽排序（pointer 事件，桌面 + 触屏通用；移动超过 6px 才视为拖拽） ---- */
let drag: { id: string; startY: number; started: boolean; tr: HTMLElement } | null = null
let dropTarget: { id: string; pos: 'before' | 'after' } | null = null
const dropHint = ref<{ id: string; pos: string } | null>(null)

function movePerson(dragId: string, targetId: string, pos: 'before' | 'after') {
  const ps = store.people
  const from = ps.findIndex(p => p.id === dragId)
  if (from < 0) return
  const [item] = ps.splice(from, 1)
  if (!item) return
  let to = ps.findIndex(p => p.id === targetId)
  if (to < 0) { ps.splice(from, 0, item); return }
  if (pos === 'after') to++
  ps.splice(to, 0, item)
}

function onPointerDown(e: PointerEvent) {
  if ((e.target as HTMLElement).closest('button')) return   // 按钮列正常点击
  const tr = (e.target as HTMLElement).closest('tr[data-id]') as HTMLElement | null
  if (!tr) return
  drag = { id: tr.dataset.id!, startY: e.clientY, started: false, tr }
  e.preventDefault()   // 防止拖出选中文本
  document.addEventListener('pointermove', onPointerMove)
  document.addEventListener('pointerup', onPointerUp)
  document.addEventListener('pointercancel', onPointerCancel)
}
function onPointerMove(e: PointerEvent) {
  if (!drag) return
  if (!drag.started) {
    if (Math.abs(e.clientY - drag.startY) < 6) return
    drag.started = true
    drag.tr.classList.add('dragging')
    document.body.classList.add('drag-active')
    if (navigator.vibrate) try { navigator.vibrate(10) } catch { /* 忽略 */ }
  }
  e.preventDefault()
  const el = document.elementFromPoint(e.clientX, e.clientY) as HTMLElement | null
  const tr = el?.closest?.('#people-table tbody tr[data-id]') as HTMLElement | null
  dropHint.value = null
  if (tr && tr.dataset.id !== drag.id) {
    const rect = tr.getBoundingClientRect()
    const below = e.clientY > rect.top + rect.height / 2
    dropHint.value = { id: tr.dataset.id!, pos: below ? 'below' : 'above' }
    dropTarget = { id: tr.dataset.id!, pos: below ? 'after' : 'before' }
  } else dropTarget = null
}
function endDrag() {
  if (drag) drag.tr.classList.remove('dragging')
  document.body.classList.remove('drag-active')
  dropHint.value = null
  drag = null
  dropTarget = null
  document.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerup', onPointerUp)
  document.removeEventListener('pointercancel', onPointerCancel)
}
function onPointerUp() {
  if (drag && drag.started && dropTarget) {
    movePerson(drag.id, dropTarget.id, dropTarget.pos)
    store.save()
  }
  endDrag()
}
function onPointerCancel() { endDrag() }
onUnmounted(endDrag)
</script>

<template>
  <div class="mx-auto flex max-w-4xl flex-col gap-4">
    <Card>
      <CardHeader class="pb-3"><CardTitle class="text-base">批量导入名单</CardTitle></CardHeader>
      <CardContent class="space-y-3">
        <p class="text-[13px] leading-relaxed text-muted-foreground">
          每行一人；「自动替换」开启时「,」「，」「、」「\」自动分行、空格自动去除，关闭时按原文导入（姓名与职务用「｜」：姓名｜职务）。<br>
          例：<code class="rounded bg-muted px-1">张三、李四、王五</code> 或 <code class="rounded bg-muted px-1">张三｜书记</code>
        </p>
        <Textarea id="import-text" v-model="importText" :rows="5" placeholder="张三、李四、王五&#10;赵六｜主任" />
        <div class="flex flex-wrap items-center gap-2">
          <Label class="mr-auto flex items-center gap-1.5 text-[13px] font-normal">
            <input type="checkbox" id="import-auto" v-model="importAuto" class="size-4 accent-zinc-900" @change="persistAuto">
            自动替换（分行 / 去空格）
          </Label>
          <Button id="btn-import-append" size="sm" @click="importPeople(false)">追加导入</Button>
          <Button id="btn-import-replace" size="sm" variant="outline" @click="importPeople(true)">替换全部</Button>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader class="pb-3"><CardTitle class="text-base">名单（从上到下即礼宾次序，请按序排列）</CardTitle></CardHeader>
      <CardContent class="space-y-3">
        <div class="overflow-x-auto rounded-md border">
          <table id="people-table" class="w-full text-sm">
            <thead>
              <tr class="border-b bg-muted/50 text-left text-[13px] text-muted-foreground">
                <th class="w-[50px] px-3 py-2 font-medium">次序</th>
                <th class="w-[120px] px-3 py-2 font-medium">姓名</th>
                <th class="px-3 py-2 font-medium">职务</th>
                <th class="w-[170px] px-3 py-2 font-medium">操作</th>
              </tr>
            </thead>
            <tbody @pointerdown="onPointerDown">
              <tr v-for="(p, i) in store.people" :key="p.id" :data-id="p.id"
                class="border-b last:border-b-0 hover:bg-muted/30 select-none"
                :class="dropHint && dropHint.id === p.id ? (dropHint.pos === 'above' ? 'drop-above' : 'drop-below') : ''">
                <td class="px-3 py-1.5 text-muted-foreground">{{ i + 1 }}</td>
                <td class="pname px-3 py-1.5" title="双击修改姓名" @dblclick="startEdit(p.id, p.name)">
                  <input v-if="editingId === p.id" v-model="editingVal" type="text"
                    class="w-full rounded border border-zinc-400 px-1 py-0.5 outline-none"
                    @keydown.enter.prevent="commitEdit(true)" @keydown.escape.prevent="commitEdit(false)"
                    @blur="commitEdit(true)">
                  <template v-else>{{ p.name }}</template>
                </td>
                <td class="px-3 py-1.5">{{ p.title || '' }}</td>
                <td class="px-3 py-1.5">
                  <Button variant="outline" size="sm" class="h-7 px-2" :disabled="i === 0"
                    @click="onRowAction('up', p.id)">↑</Button>
                  <Button variant="outline" size="sm" class="ml-1 h-7 px-2" :disabled="i === store.people.length - 1"
                    @click="onRowAction('down', p.id)">↓</Button>
                  <Button variant="destructive" size="sm" class="ml-1 h-7 px-2" @click="onRowAction('del', p.id)">删</Button>
                </td>
              </tr>
              <tr v-if="!store.people.length">
                <td colspan="4" class="px-3 py-3 text-center text-muted-foreground">（暂无名单，请先导入）</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="flex items-center gap-3">
          <Button id="btn-clear-people" variant="outline" size="sm" @click="clearPeople">清空名单</Button>
          <span class="text-[13px] text-muted-foreground">按住行上下拖拽调整顺序（也可用 ↑↓）；台签打印顺序、座位自动排位都以此顺序为准。</span>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
