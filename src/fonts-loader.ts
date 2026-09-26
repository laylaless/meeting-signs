// 运行时注入字体样式，而不进 Vite 打包链：
// @font-face 的 url 需要相对于页面解析（GitHub Pages 子路径与 file:// 离线分发都能用），
// 若交给打包器处理会被改写成带 hash 的资源路径并破坏相对引用。
// fonts/fonts.css 内含 WebZhongSong 与 FZQiuXinWeiBei 两条 @font-face；
// 华文新魏体积大，单独放在 fonts/xinwei.css（base64 内嵌 TTF），异步加载不阻塞首屏。
export function injectFonts() {
  for (const href of ['./fonts/fonts.css', './fonts/xinwei.css']) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = href
    document.head.appendChild(link)
  }
}
