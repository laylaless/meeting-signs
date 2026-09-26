/* 动态 @page 打印纸张规则：运行时注入 <style id="page-style">（不进 Vite 处理链），
   按台签模版改写纸张尺寸。旧版测试会读取该元素的 textContent 断言纸张设置。 */
export function ensurePageStyle() {
  let el = document.getElementById('page-style') as HTMLStyleElement | null
  if (!el) {
    el = document.createElement('style')
    el.id = 'page-style'
    el.textContent = '@page{size:A4 portrait;margin:0}'
    document.head.appendChild(el)
  }
  return el
}

export function setPageStyle(text: string) {
  ensurePageStyle().textContent = text
}
