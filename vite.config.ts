import { copyFileSync } from 'node:fs'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { viteStaticCopy } from 'vite-plugin-static-copy'

// base 用相对路径：同一份构建产物在 GitHub Pages 子路径（/meeting-signs/）
// 与 file:// 离线分发（拷走 dist 双击打开）下都能正常加载资源。
export default defineConfig({
  base: './',
  plugins: [
    vue(),
    tailwindcss(),
    // file:// 离线分发：模块脚本（type=module）在 file:// 下被 CORS 拦截，
    // 配合 IIFE 输出把入口改写成经典 defer 脚本（行为等价，双击 dist 即可用）
    {
      name: 'classic-script-for-file-protocol',
      apply: 'build',
      transformIndexHtml: {
        order: 'post',
        handler(html: string) {
          return html.replace(/<script type="module" crossorigin/g, '<script defer')
        },
      },
    },
    viteStaticCopy({
      targets: [
        // 旧版单文件应用（v2 / v1 存档）与其依赖，原样随产物发布：根 URL 是新版，/index_v2.html、/index_v1.html 是存档
        { src: 'index_v2.html', dest: '.' },
        { src: 'index_v1.html', dest: '.' },
        { src: 'fonts', dest: '.' },
        { src: 'UPDATE.md', dest: '.' },
      ],
    }),
    // v0.3.0~0.3.5 期间新版入口是 /index3.html，对外分享过的链接不能断：
    // 构建完成后把入口复制一份作别名，/index3.html 与根路径打开的都是新版
    {
      name: 'index3-alias-backcompat',
      apply: 'build',
      closeBundle() {
        copyFileSync(
          fileURLToPath(new URL('./dist/index.html', import.meta.url)),
          fileURLToPath(new URL('./dist/index3.html', import.meta.url)),
        )
      },
    },
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // 入口即根目录 index.html（自 v0.3.6 起新版为主入口；旧版存档 index_v2.html 不参与打包）；
  // 输出 IIFE 单脚本（经典 <script>，无 CORS 限制）：file:// 双击离线打开 dist 也能用
  build: {
    rollupOptions: {
      input: {
        index: fileURLToPath(new URL('./index.html', import.meta.url)),
      },
      output: {
        format: 'iife',
        inlineDynamicImports: true,
      },
    },
  },
})
