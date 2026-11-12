# Happy Colors — 原图模板 / Colorful P1

本次只替换内置五个图片模板的加载方式。基线为 GitHub main 的
`64b3732c61dc24dcb20ed221d0ba171fb186e24a`（Colorful、七语言、Save 修复已合并）。
这不是早期 V4/V9 的重建，也没有写入 GitHub 或 main。

## 先试玩，不要覆盖线上仓库

完整测试包解压到一个新的预览目录。文件保持在原来的相对位置。
在该目录启动：

```powershell
py -m http.server 8000 --bind 0.0.0.0
```

同一家庭网络的 iPhone / iPad Safari 打开电脑的局域网 IP，例如
`http://192.168.1.23:8000/`（请替换为电脑真实 IP）。不要使用路由器端口转发。
测试结束 Ctrl+C。请使用 HTTP/HTTPS 预览，不推荐双击 file:// 页面来测试 Canvas 像素读取。

桌面/平板顶部版本标记是 Colorful P1。手机窄屏会隐藏该标记。
原生 Share 功能仍须可信 HTTPS；本地 HTTP 请使用 Download PNG。

## 使用方式

Unicorn / Princess / Cat / Butterfly / Dinosaur 按钮直接加载对应附件原图；
Upload Picture 仍打开系统文件选择器。两者都调用同一个 `loadPictureSource()`。
模板按钮不会自动打开或伪造系统文件选择器。原来的单画布和 Fill 算法不变。

选择一张图后再点 Fill，并选择颜色、点击闭合白色区域。
加载成功是一次 Undo 操作；失败不会清空原画；连续换图只保留最后一次选择。
绘画过程中如果又开始画、Undo 或 New，尚未完成的旧图片请求不会覆盖新操作。
同一张本地图片可以重复上传。PNG 保存仍包含整幅作品，不只是放大的可见部分。
本次不新增自动保存；刷新或离开前请保存画作。

## 图片文件（原样保留，未重绘、裁剪、二值化或改背景）

| 按钮键 | 文件 | 用户附件 |
|---|---|---|
| unicorn | assets/coloring-pages/unicorn.png | unicorn-simple.png |
| princess | assets/coloring-pages/princess.png | Smiling crowned princess coloring page-2.png |
| cat | assets/coloring-pages/cat.png | Cute Seated Kitten Coloring Page-4.png |
| butterfly | assets/coloring-pages/butterfly.png | Cute Butterfly Coloring Page-1.png |
| dino | assets/coloring-pages/dinosaur.png | Baby Sauropod Coloring Page-3.png |

五张图都是 1254 × 1254 RGBA PNG，逐文件 SHA-256 与附件一致。

## 变更范围

运行文件仅修改 app.js、index.html、i18n.js；新增上面的五张 PNG。
- app.js：用共享图片导入函数替代旧的程序线稿函数及旧上传处理块。
- index.html：新版本标记与 app.js/i18n.js 的缓存版本号。
- i18n.js：七种语言各新增一条图片加载失败提示。

canvas-zoom.js、mobile-ui.js、save-picture.js，以及四个 CSS 文件均与 main 完全相同。
Fill、Brush、Sparkle、Eraser、Save 的原有处理、触控、缩放代码没有改写。
中转 Canvas 仅用于在替换画作前检查图片是否可读，随后 1:1 复制到原画布；
不是额外可见的图层，也不是只设置 CSS 背景。

## 更新仓库：只能覆盖合并，不要先删除文件

真机测试通过后，使用 `happy-coloring-template-update-files.zip`。
它是增量覆盖包，不是独立网站；完整试玩请用 tested.zip。

1. 保存当前未提交工作，确认 `git status` 干净。不要清理 stashes。
2. 从最新 main 建立 `picture-templates-upload` 功能分支。
3. 把增量包内容复制到仓库根目录，替换同名文件、合并文件夹。
   **不要先清空 Happy-Coloring；不要删 .git、README、旧 docs/evidence。**
4. 不需要再应用任何旧 `.patch` 文件。
5. `git ls-files --deleted` 应无输出。审查差异、重跑测试后才 commit/push/PR。

```powershell
git switch main
git pull --ff-only origin main
git switch -c picture-templates-upload
```

如果新 main 不再是本次基线，需要先核对差异；不要强行覆盖他人的后续修改。
旧版本的 MANIFEST-* 是历史记录；当前运行文件使用 MANIFEST-TEMPLATES-SHA256.json。

## 重跑测试

```powershell
npm test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
npm run test:ui
npm run test:templates
py tests/check_template_resources.py
```

`test:ui` 包含旧功能回归和新增原图模板用例，`test:templates` 只跑新模板用例。
Windows CRLF 与 LF 的源码校验仅忽略换行转换，仍然检测其他源码变化。
图片始终进行原始字节校验。

完整测试边界与结果见 docs/TEMPLATES-TEST-REPORT.zh-CN.md；真机清单见
 docs/TEMPLATES-DEVICE-CHECKLIST.zh-CN.md。
