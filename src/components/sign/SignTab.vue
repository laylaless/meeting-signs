<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PAGESIZE } from '@/constants'
import { useAppStore } from '@/store'
import { applySquash, buildSignHTML } from '@/utils/sign'
import { clamp } from '@/utils/misc'
import { setPageStyle } from '@/utils/page-style'

const store = useAppStore()
const previewRef = ref<HTMLElement>()

const selected = computed(() => store.people.filter(p => !store.sign.excluded.includes(p.id)))

const previewHTML = computed(() => {
  if (!store.people.length) return '<p class="p-5 text-[13px] text-muted-foreground">请先在「名单」页导入人员。</p>'
  if (!selected.value.length) return '<p class="p-5 text-[13px] text-muted-foreground">未勾选任何打印人员，请在上方「打印人员」中勾选。</p>'
  return `<div class="preview-scale">${buildSignHTML(store.sign, store.people)}</div>`
})

/* 渲染后按容器可用宽重测并 scaleX 压缩（需要真实布局，故在 nextTick + 可见时执行） */
async function refreshMeasure() {
  await nextTick()
  const holder = previewRef.value
  if (!holder || !holder.offsetWidth) return   // 隐藏时 offsetWidth=0，跳过（tab 切换可见后会重测）
  const sc = holder.firstElementChild as HTMLElement | null
  if (sc?.classList.contains('preview-scale')) {
    if (store.sign.mode === 'seatcard') { sc.style.width = '297mm'; sc.style.height = '210mm'; sc.style.transform = 'scale(.22)' }
    else sc.removeAttribute('style')
  }
  applySquash(holder)
}

watch(previewHTML, refreshMeasure)
watch(() => store.activeTab, t => { if (t === 'sign') nextTick(() => requestAnimationFrame(refreshMeasure)) })
onMounted(() => {
  refreshMeasure()
  document.fonts.ready.then(refreshMeasure)   // 字体就绪后首测可能不准，重测一次
})

/* ---- 设置变更（全部即时保存 + 刷新预览） ---- */
function commitSetting() {
  store.sign.perPage = clamp(+store.sign.perPage || 4, 2, 8)
  store.sign.size = clamp(+store.sign.size || 0, 0, 400)
  store.save()
}

/* ---- 打印人员勾选 ---- */
function togglePerson(pid: string, checked: boolean) {
  if (checked) store.sign.excluded = store.sign.excluded.filter(x => x !== pid)
  else if (!store.sign.excluded.includes(pid)) store.sign.excluded.push(pid)
  store.save()
}

function printSigns() {
  if (!store.people.length) { toast.warning('名单为空'); return }
  if (!selected.value.length) { toast.warning('未勾选打印人员'); return }
  const pa = document.getElementById('print-area')!
  pa.innerHTML = buildSignHTML(store.sign, store.people)
  applySquash(pa)
  setPageStyle(PAGESIZE[store.sign.mode]
    ? `@page{size:${PAGESIZE[store.sign.mode]};margin:0}`   // 台签纸/座位签模版直接装对应纸
    : '@page{size:A4 portrait;margin:0}')
  document.body.classList.remove('print-seat')
  document.body.classList.add('print-sign')
  window.print()
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <Card>
      <CardHeader class="pb-3"><CardTitle class="text-base">台签设置</CardTitle></CardHeader>
      <CardContent class="space-y-3">
        <div class="flex flex-wrap items-center gap-x-4 gap-y-3 text-[13px]">
          <Label class="flex items-center gap-1.5">样式
            <select id="sign-mode" v-model="store.sign.mode" class="h-8 rounded-md border border-input bg-background px-2"
              @change="commitSetting">
              <option value="standard">标准模版（190×178mm 方框，上下布局）</option>
              <option value="paper190">190×178mm 台签纸（1 人 / 页，纸张即台签）</option>
              <option value="qinchuan">琴川 195×175mm 台签纸（1 人 / 页，纸张即台签）</option>
              <option value="table200x120">200×120 桌签（1 人 / 页，120mm 宽×200mm 高）</option>
              <option value="seatcard">座位签（A4 横向，1 行 5 列，名字竖排）</option>
              <option value="fold">对折大台签（1 人 / 页，A4 纵向对折）</option>
              <option value="strip">紧凑小台签（裁切条，对折立放）</option>
            </select>
          </Label>
          <Label v-show="store.sign.mode === 'strip'" class="flex items-center gap-1.5">每页条数
            <Input id="sign-perpage" type="number" min="2" max="8" v-model.number="store.sign.perPage"
              class="h-8 w-[60px]" @change="commitSetting" />
          </Label>
          <Label class="flex items-center gap-1.5">字体
            <select id="sign-font" v-model="store.sign.font" class="h-8 rounded-md border border-input bg-background px-2"
              @change="commitSetting">
              <option value="xinwei">华文新魏</option>
              <option value="fzqiu">曾柏求新魏碑简体</option>
              <option value="stkai">华文楷体</option>
              <option value="hei">黑体</option>
              <option value="song">宋体</option>
              <option value="kai">楷体</option>
              <option value="custom">自定义字体…</option>
            </select>
          </Label>
          <Label v-show="store.sign.font === 'custom'" class="flex items-center gap-1.5">字体名
            <Input id="sign-customfont" type="text" v-model="store.sign.customFont" placeholder="如 楷体、LXGW WenKai"
              class="h-8 w-[150px]" @input="commitSetting" />
          </Label>
          <Label class="flex items-center gap-1.5">字号(pt)
            <Input id="sign-size" type="number" min="0" max="400" v-model.number="store.sign.size" class="h-8 w-[70px]"
              @change="commitSetting" />
          </Label>
          <Label class="flex items-center gap-1 font-normal">
            <input type="checkbox" v-model="store.sign.showTitle" class="size-4 accent-zinc-900" @change="commitSetting">
            名字上方显示职务小字
          </Label>
          <Label class="flex items-center gap-1 font-normal">
            <input type="checkbox" v-model="store.sign.bold" class="size-4 accent-zinc-900" @change="commitSetting">
            加粗
          </Label>
        </div>
        <p class="text-[13px] leading-relaxed text-muted-foreground">
          标准模版：内容限制在 190×178mm 方框内（A4 居中），上半倒转 + 下半正向（对折立放后两面均正向），默认华文新魏
          <b>155 号</b>（所有名字字号统一，超宽自动横向压缩不换行），沿方框上下对折立放。字体可选华文新魏 / 曾柏求新魏碑简体（自托管，无需安装）/
          黑体 / 宋体 / 楷体 / 华文楷体，或选「自定义字体…」输入本机已安装的任意字体名。<br>
          对折大台签：A4 纵向打印后沿中线对折，立放于桌面，正反两面均可读。<b>190×178mm / 琴川195×175mm
            台签纸</b>：打印机直接装对应尺寸的纸，页面即台签（打印对话框纸张选「默认/由打印机决定」）。<b>200×120
              桌签</b>：装 120mm 宽×200mm 高桌签纸，1 列 4 行——1、4 行空白各 40mm，2、3 行名字行各 60mm，名字默认华文新魏
          <b>96 号</b>居中，上倒下正（对折立放两面均正向）。<b>座位签</b>：A4 <b>横向</b>打印，每页 1 行 5
          列、每列 5.5cm 宽（列间虚线，裁切后插座位牌卡座），名字<b>竖排</b>逐字居中（仅姓名、不带职务小字），字号按字数自动（≤4 字 130
          号），页宽剩余约 2.2cm 空白。紧凑小台签：按虚线裁切后逐条对折。字号填 0 时按模版默认（标准 155pt / 200×120 桌签
          96pt），也可手动指定。
        </p>
      </CardContent>
    </Card>

    <Card>
      <CardHeader class="pb-3"><CardTitle class="text-base">打印人员</CardTitle></CardHeader>
      <CardContent class="space-y-2">
        <div class="flex items-center gap-2">
          <Button variant="outline" size="sm" @click="store.sign.excluded = []; store.save()">全选</Button>
          <Button variant="outline" size="sm" @click="store.sign.excluded = store.people.map(p => p.id); store.save()">全不选</Button>
          <span class="text-[13px] text-muted-foreground">已选 {{ store.people.length - store.sign.excluded.length }}/{{ store.people.length }} 人</span>
        </div>
        <div id="sign-person-chips" class="flex flex-wrap gap-1.5">
          <label v-for="p in store.people" :key="p.id" class="person-chip"
            :class="{ on: !store.sign.excluded.includes(p.id) }">
            <input type="checkbox" :data-pid="p.id" :checked="!store.sign.excluded.includes(p.id)"
              @change="togglePerson(p.id, ($event.target as HTMLInputElement).checked)">
            {{ p.name }}
          </label>
          <span v-if="!store.people.length" class="text-[13px] text-muted-foreground">名单为空</span>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader class="pb-3"><CardTitle class="text-base">首页预览</CardTitle></CardHeader>
      <CardContent>
        <div class="preview-wrap">
          <div class="preview-holder">
            <div id="sign-preview" ref="previewRef" v-html="previewHTML"></div>
          </div>
        </div>
      </CardContent>
    </Card>

    <div>
      <Button id="btn-print-sign" @click="printSigns">🖨 打印台签（已选人员）</Button>
    </div>
  </div>
</template>
