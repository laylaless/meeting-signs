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
        // 旧版单文件应用与其依赖，原样随产物发布：根 URL 仍是旧版，/index3.html 是新版
        { src: 'index.html', dest: '.' },
        { src: 'index_v1.html', dest: '.' },
        { src: 'fonts', dest: '.' },
        { src: 'UPDATE.md', dest: '.' },
      ],
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // 入口显式只指向 index3.html，避免把根目录旧版 index.html 识别为待打包入口；
  // 输出 IIFE 单脚本（经典 <script>，无 CORS 限制）：file:// 双击离线打开 dist 也能用
  build: {
    rollupOptions: {
      input: {
        index3: fileURLToPath(new URL('./index3.html', import.meta.url)),
      },
      output: {
        format: 'iife',
        inlineDynamicImports: true,
      },
    },
  },
})
