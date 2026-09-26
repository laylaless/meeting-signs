<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { clamp } from '@/utils/misc'
import { bnRenderStage, dateToISO, hexNorm } from '@/utils/banner'
import { useAppStore } from '@/store'
import { requestBannerFullscreen } from './bn-full'

const store = useAppStore()
const previewEl = ref<HTMLElement>()
const tipVisible = ref(false)
const tipText = ref('')

const cur = computed(() => store.banners.list[Math.min(store.banners.sel, store.banners.list.length - 1)]!)
const r43 = computed(() => store.banners.ratio === '4-3')

/* ---- 预览渲染（bnRenderStage 为命令式 DOM，需显式重绘） ---- */
function renderPreview() {
  if (!previewEl.value || !previewEl.value.clientWidth) return
  bnRenderStage(previewEl.value, cur.value)
}
watch(() => [store.banners, store.banners.ratio], () => nextTick(renderPreview), { deep: true })
watch(() => store.activeTab, t => { if (t === 'banner') nextTick(() => requestAnimationFrame(renderPreview)) })

let ro: ResizeObserver | null = null
onMounted(() => {
  // 旧中文日期迁移为 ISO
  const b = cur.value
  const iso = dateToISO(b.date)
  if (iso && iso !== b.date) b.date = iso
  ro = new ResizeObserver(() => renderPreview())
  if (previewEl.value) ro.observe(previewEl.value)
  nextTick(renderPreview)
})
onUnmounted(() => ro?.disconnect())

/* ---- 列表 ---- */
function selectBanner(i: number) { store.banners.sel = i; store.save() }
async function delBanner(i: number) {
  if (store.banners.list.length <= 1) { toast.warning('至少保留一个会标'); return }
  store.banners.list.splice(i, 1)
  if (store.banners.sel >= store.banners.list.length) store.banners.sel = store.banners.list.length - 1
  store.save()
}
function addBanner() {
  // 新增会标 = 复制当前会标的全部配置（内容、样式、字号、偏移）
  const b = JSON.parse(JSON.stringify(cur.value))
  b.id = 'b' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
  store.banners.list.push(b)
  store.banners.sel = store.banners.list.length - 1
  store.save()
}

/* ---- 编辑器提交（clamp 后保存；预览由 watcher 重绘） ---- */
function commit() { store.save() }
function clampNum(key: 'titleSize' | 'dateSize' | 'spacing' | 'lineH', min: number, max: number, fb: number) {
  cur.value[key] = clamp(Number(cur.value[key]) || fb, min, max)
  store.save()
}
function setBg(hex: string) { cur.value.bg = hexNorm(hex, cur.value.bg); store.save() }
function setFg(hex: string) { cur.value.fg = hexNorm(hex, cur.value.fg); store.save() }

/* ---- 预览画面里：名称 / 日期支持上下拖动（左右锁定），双击复位；拖动时显示距上/下边缘的百分比 ---- */
let drag: { key: 'titleOff' | 'dateOff'; startY: number; start: number } | null = null
let lastTap = { t: 0, key: '' }

function updateTip() {
  const el = previewEl.value
  if (!el || !drag) return
  const t = el.querySelector(drag.key === 'titleOff' ? '.bn-title' : '.bn-date')
  if (!t) return
  const sr = el.getBoundingClientRect(), er = t.getBoundingClientRect()
  const top = Math.max(0, (er.top - sr.top) / sr.height * 100)
  const bot = Math.max(0, (sr.bottom - er.bottom) / sr.height * 100)
  tipText.value = `上 ${top.toFixed(0)}% ｜ 下 ${bot.toFixed(0)}%`
}
function onPreviewPointerdown(e: PointerEvent) {
  const el = previewEl.value!
  const t = (e.target as HTMLElement).closest('.bn-title,.bn-date') as HTMLElement | null
  if (!t) return
  e.preventDefault()
  const isTitle = t.classList.contains('bn-title')
  const key: 'titleOff' | 'dateOff' = isTitle ? 'titleOff' : 'dateOff'
  drag = { key, startY: e.clientY, start: cur.value[key] || 0 }
  try { el.setPointerCapture(e.pointerId) } catch { /* 忽略 */ }
  tipVisible.value = true
  updateTip()
}
function onPreviewPointermove(e: PointerEvent) {
  const el = previewEl.value
  if (!el || !drag) return
  const k = el.clientHeight / 1080                     // 与渲染同一比例基准（画面高/1080）
  const dyPt = (e.clientY - drag.startY) / (4 / 3 * k) // 屏幕 px 换算回 pt 存储
  cur.value[drag.key] = Math.round(drag.start + dyPt)
  renderPreview()
  updateTip()
}
function onPreviewPointerup(e: PointerEvent) {
  tipVisible.value = false
  if (!drag) return
  const moved = Math.abs(e.clientY - drag.startY)
  if (moved < 4) {   // 几乎没动 = 点击：自行判定双击复位（元素每次重渲染，浏览器 dblclick 不可靠）
    const now = Date.now()
    if (lastTap.key === drag.key && now - lastTap.t < 400) {
      cur.value[drag.key] = 0
      drag = null
      lastTap = { t: 0, key: '' }
      store.save(); renderPreview()
      return
    }
    lastTap = { t: now, key: drag.key }
  }
  drag = null
  store.save()
}
function onPreviewPointercancel() { drag = null; tipVisible.value = false }
</script>

<template>
  <div class="bn-layout flex items-start gap-3">
    <div class="flex w-[330px] flex-shrink-0 flex-col gap-3">
      <Card>
        <CardHeader class="pb-3"><CardTitle class="text-base">会标列表</CardTitle></CardHeader>
        <CardContent class="space-y-2">
          <div class="blist flex flex-col gap-1.5">
            <div v-for="(b, i) in store.banners.list" :key="b.id"
              class="flex cursor-pointer items-center gap-2 rounded-md border px-2 py-1.5"
              :class="i === store.banners.sel ? 'border-primary shadow-[0_0_0_1px_var(--primary)_inset]' : 'bg-background'"
              @click="selectBanner(i)">
              <span class="bswatch h-3.5 w-[22px] flex-shrink-0 rounded border border-black/25" :style="{ background: b.bg }"></span>
              <span class="bname flex-1 min-w-0 overflow-hidden text-ellipsis whitespace-nowrap text-[13px]">{{ i + 1 }}. {{ (b.title || '（未命名）').split('\n')[0] }}</span>
              <button class="bdel px-1 text-sm text-red-500 hover:text-red-600" title="删除"
                @click.stop="delBanner(i)">✕</button>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <Button id="btn-bn-add" size="sm" @click="addBanner">＋ 新增会标</Button>
            <span class="text-[13px] text-muted-foreground">列表顺序即 ↑↓ 切换顺序</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="pb-3"><CardTitle class="text-base">会标内容与样式</CardTitle></CardHeader>
        <CardContent class="space-y-2 text-[13px]">
          <Label class="block">会议名称（手动换行生效）
            <Textarea id="bn-title" :rows="3" v-model="cur.title" placeholder="XX街道工作会议" class="mt-1" @input="commit" /></Label>
          <Label class="mt-1 block">日期
            <Input id="bn-date" type="date" :model-value="dateToISO(cur.date)" class="mt-1 w-40"
              @update:model-value="(v: string | number) => { const s = String(v); if (s) { cur.date = s; commit() } }" /></Label>
          <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
            <Label class="flex items-center gap-1">名称字号
              <Input id="bn-size-title" type="number" min="8" max="300" v-model.number="cur.titleSize" class="h-8 w-[60px]"
                @change="clampNum('titleSize', 8, 300, 32)" /> 号</Label>
            <Label class="flex items-center gap-1">日期字号
              <Input id="bn-size-date" type="number" min="8" max="300" v-model.number="cur.dateSize" class="h-8 w-[60px]"
                @change="clampNum('dateSize', 8, 300, 24)" /> 号</Label>
            <Label class="flex items-center gap-1">字间距
              <Input id="bn-spacing" type="number" min="0" max="100" step="0.5" v-model.number="cur.spacing" class="h-8 w-[60px]"
                @change="clampNum('spacing', 0, 100, 3)" /> pt</Label>
            <Label class="flex items-center gap-1">行距
              <Input id="bn-lineh" type="number" min="0.5" max="5" step="0.1" v-model.number="cur.lineH" class="h-8 w-[60px]"
                @change="clampNum('lineH', 0.5, 5, 1.5)" /> 倍</Label>
          </div>
          <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
            <Label class="flex items-center gap-1">名称字体
              <select id="bn-font" v-model="cur.font" class="h-8 rounded-md border border-input bg-background px-2" @change="commit">
                <option value="zhongsong">华文中宋</option>
                <option value="hei">黑体</option>
                <option value="song">宋体</option>
                <option value="kai">楷体</option>
                <option value="xinwei">华文新魏</option>
                <option value="stkai">华文楷体</option>
                <option value="custom">自定义字体…</option>
              </select></Label>
            <Label v-show="cur.font === 'custom'" class="flex items-center gap-1">字体名
              <Input id="bn-customfont" type="text" v-model="cur.customFont" placeholder="如：方正小标宋简体" class="h-8 w-[130px]" @input="commit" /></Label>
          </div>

          <div class="mt-2">
            <b class="text-[13px]">背景色</b>
            <div class="mt-1 flex items-center gap-2">
              <button id="sw-bg-1" class="sw" title="政务红 rgb(165,38,21)" style="background:#A52615" @click="setBg('#A52615')"></button>
              <button id="sw-bg-2" class="sw" title="红 rgb(193,0,0)" style="background:#C10000" @click="setBg('#C10000')"></button>
              <input type="color" id="bn-bg-picker" title="拾色器" :value="hexNorm(cur.bg, '#A52615')" @input="setBg(($event.target as HTMLInputElement).value)">
              <Input id="bn-bg-hex" type="text" placeholder="#A52615" class="h-8 w-20" spellcheck="false"
                :value="cur.bg" @change="setBg(($event.target as HTMLInputElement).value)" />
            </div>
          </div>
          <div class="mt-2">
            <b class="text-[13px]">文字颜色</b>
            <div class="mt-1 flex items-center gap-2">
              <button id="sw-fg-1" class="sw" title="黄" style="background:#FFFF00" @click="setFg('#FFFF00')"></button>
              <button id="sw-fg-2" class="sw" title="金黄" style="background:#FFD700" @click="setFg('#FFD700')"></button>
              <button id="sw-fg-3" class="sw" title="白" style="background:#FFFFFF" @click="setFg('#FFFFFF')"></button>
              <input type="color" id="bn-fg-picker" title="拾色器" :value="hexNorm(cur.fg, '#FFFF00')" @input="setFg(($event.target as HTMLInputElement).value)">
              <Input id="bn-fg-hex" type="text" placeholder="#FFFF00" class="h-8 w-20" spellcheck="false"
                :value="cur.fg" @change="setFg(($event.target as HTMLInputElement).value)" />
            </div>
          </div>
          <div class="mt-2">
            <b class="text-[13px]">文字阴影（名称与日期共用：颜色 / 透明度 / 角度 / 距离 / 模糊）</b>
            <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
              <input type="color" id="bn-sh-color" title="阴影颜色" :value="hexNorm(cur.shadow.color, '#000000')"
                @input="cur.shadow.color = hexNorm(($event.target as HTMLInputElement).value, '#000000'); commit()">
              <Label class="flex items-center gap-1">透明
                <Input id="bn-sh-opacity" type="number" min="0" max="100" v-model.number="cur.shadow.opacity" class="h-8 w-[52px]"
                  @change="cur.shadow.opacity = clamp(cur.shadow.opacity || 0, 0, 100); commit()" />%</Label>
              <Label class="flex items-center gap-1">角度
                <Input id="bn-sh-angle" type="number" min="0" max="360" v-model.number="cur.shadow.angle" class="h-8 w-[58px]"
                  @change="cur.shadow.angle = clamp(cur.shadow.angle || 0, 0, 360); commit()" />°</Label>
              <Label class="flex items-center gap-1">距离
                <Input id="bn-sh-dist" type="number" min="0" max="100" step="0.5" v-model.number="cur.shadow.dist" class="h-8 w-[58px]"
                  @change="cur.shadow.dist = clamp(cur.shadow.dist || 0, 0, 100); commit()" />pt</Label>
              <Label class="flex items-center gap-1">模糊
                <Input id="bn-sh-blur" type="number" min="0" max="200" step="0.5" v-model.number="cur.shadow.blur" class="h-8 w-[58px]"
                  @change="cur.shadow.blur = clamp(cur.shadow.blur || 0, 0, 200); commit()" />pt</Label>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <div class="bn-main min-w-0 flex-1">
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="text-base">预览（{{ r43 ? '4:3' : '16:9' }}，与全屏画面一致）</CardTitle>
        </CardHeader>
        <CardContent class="space-y-2.5">
          <div class="relative mx-auto">
            <div id="bn-preview" ref="previewEl" class="bn-stage mx-auto max-h-[72vh] border cursor-default"
              :style="{ aspectRatio: r43 ? '4 / 3' : '16 / 9', maxWidth: r43 ? 'calc(72vh * 4 / 3)' : 'calc(72vh * 16 / 9)' }"
              @pointerdown="onPreviewPointerdown" @pointermove="onPreviewPointermove" @pointerup="onPreviewPointerup"
              @pointercancel="onPreviewPointercancel"></div>
            <div class="bn-drag-tip" :style="{ display: tipVisible ? 'block' : 'none' }">{{ tipText }}</div>
          </div>
          <div class="flex flex-wrap items-center gap-2 text-[13px]">
            <Button id="btn-bn-full" @click="requestBannerFullscreen()">⛶ 全屏显示</Button>
            <span class="flex items-center gap-1">画面比例
              <button id="bn-r169" class="bn-ratio" :class="{ active: !r43 }" title="宽高比 16:9"
                @click="store.banners.ratio = '16-9'; store.save()">16:9</button>
              <button id="bn-r43" class="bn-ratio" :class="{ active: r43 }" title="宽高比 4:3"
                @click="store.banners.ratio = '4-3'; store.save()">4:3</button>
            </span>
            <span class="text-[13px] text-muted-foreground">全屏时 ↑↓ / 滚轮 / PgUp PgDn 切换会标，ESC 退出；字号单位为 PPT 字号（pt）</span>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
