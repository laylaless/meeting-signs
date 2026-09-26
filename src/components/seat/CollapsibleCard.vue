<script setup lang="ts">
import { ref } from 'vue'
import { ChevronDown } from '@lucide/vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { COLLAPSED_KEY } from '@/constants'

const props = defineProps<{ col: string; title: string }>()

function loadCollapsed(): string[] {
  try { return JSON.parse(localStorage.getItem(COLLAPSED_KEY) || '') || [] } catch { return [] }
}
const open = ref(!loadCollapsed().includes(props.col))

function toggle() {
  open.value = !open.value
  const cur = loadCollapsed()
  try {
    localStorage.setItem(COLLAPSED_KEY, JSON.stringify(open.value ? cur.filter(x => x !== props.col) : [...new Set([...cur, props.col])]))
  } catch { /* 忽略 */ }
}
</script>

<template>
  <Card class="collapsible" :data-col="col">
    <CardHeader class="cursor-pointer select-none py-3" @click="toggle">
      <CardTitle class="flex items-center gap-1 text-sm">
        <span class="flex-1">{{ title }}</span>
        <slot name="title-right" />
        <ChevronDown :size="15" class="text-muted-foreground transition-transform" :class="{ '-rotate-90': !open }" />
      </CardTitle>
    </CardHeader>
    <CardContent v-show="open" class="pt-0">
      <slot />
    </CardContent>
  </Card>
</template>
