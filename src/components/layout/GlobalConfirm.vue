<script setup lang="ts">
import {
  AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { settleConfirm, useConfirmState } from '@/composables/useConfirm'

const state = useConfirmState()
</script>

<template>
  <!-- 关闭只经 settleConfirm 单一来源：确认/取消均为普通按钮，
       避免 AlertDialogAction 自带的关闭回调整早触发 update:open(false) 把结果错误置为 false -->
  <AlertDialog :open="state.open" @update:open="v => { if (!v) settleConfirm(false) }">
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>{{ state.title }}</AlertDialogTitle>
        <AlertDialogDescription class="whitespace-pre-line">{{ state.desc }}</AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <Button variant="outline" @click="settleConfirm(false)">取消</Button>
        <Button id="confirm-yes" :variant="state.danger ? 'destructive' : 'default'" @click="settleConfirm(true)">
          {{ state.confirmText }}
        </Button>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>
