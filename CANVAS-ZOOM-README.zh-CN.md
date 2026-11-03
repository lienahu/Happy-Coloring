# Happy Coloring：只缩放画布（Canvas zoom 1）

基线：`lienahu/Happy-Coloring` 的 `main@0a6ae02c5895f3d77466bb3ec43090bb31b746c1`。
这是已经合并了 iPad viewport fix 的版本；不是以前的 V5–V9。

## 孩子怎样操作

- 一个手指／Apple Pencil：画画。单指点一下进行填色、放贴纸。
- 两个手指张开／合拢：仅放大／缩小画布，100%–400%。100% 代表适合当前画板窗口，不是图片像素的 1:1。
- 两个手指一起拖动：移动当前查看的位置。松开其中一根手指后，另一根不会突然开始画线；全部抬起后，再用一根手指画画。
- 右侧、底部的紫色滚动滑条：拖动以查看画布不同位置。仅在对应方向存在超出范围的画布时显示；它们是 App 自己的滚动控制，不依赖系统滚动条是否自动隐藏。
- `−`／`+`：改变倍率；`Fit`：恢复显示整幅画。也适用于鼠标、键盘操作。
- 保存仍导出整幅画作，而不是屏幕上放大的局部。缩放、滚动都不会消耗撤销步数。

菜单、Undo／Redo／New／Save 不跟随画布缩放。工具栏仍可独立纵向滚动。
第二根手指落下时，尚未结束的单指笔画会回滚，以免双指操作留下误画痕迹；已完成的笔画不会被撤销。

## 文件

必须一起替换／新增的运行文件只有：

```text
index.html
style.css
app.js
canvas-zoom.js       ← 新文件，不能遗漏
```

`canvas-zoom.js` 负责视图几何、倍率、滚动控制和手势状态机。
`app.js` 仍负责实际画图、填色、图片上传、撤销和保存。
画布像素宽高只在初始化时设置；本次没有引入新图片生成、AI、画作分层或新 flood-fill 算法。
当前 main 的模板仍保留不变。

## 安全试用，不修改线上 main

先把压缩包解压到一个新的预览目录，例如：

```text
C:\project\happycolor\canvas-zoom-preview
```

在这个目录打开 PowerShell：

```powershell
py -m http.server 8000 --bind 0.0.0.0
```

电脑打开 `http://localhost:8000/`。iPad 与电脑连接同一家庭网络，使用电脑的实际局域网 IPv4 地址，例如 `http://192.168.1.23:8000/`（仅为示例，需用 `ipconfig` 查看实际地址）。Windows 防火墙只允许私人网络，不开放路由器端口。完成后 Ctrl+C 停止服务器。

确认顶部显示 `Canvas zoom 1`。先保存当前未完成的画，再切换到测试页面。

## 放入新 Git 分支

先检查 `git status`。若有未提交修改，先备份，不要覆盖或执行 `git clean`。
工作区干净时：

```powershell
git switch main
git pull --ff-only origin main
git switch -c canvas-pinch-zoom
```

把上面四个运行文件复制到仓库根目录。测试和文档也可以保留，便于以后回归；不必重新应用之前的 iPad patch。
也可以在上述基线的干净分支使用本包的 `canvas-pinch-zoom.patch`，不要同时使用“复制文件”和“应用 patch”两种方式：

```powershell
git apply --check .\canvas-pinch-zoom.patch
git apply .\canvas-pinch-zoom.patch
```

不要恢复旧的 stash，也不要直接合并 main。先按 `docs/CANVAS-ZOOM-IPAD-CHECKLIST.md` 真机测试。

## 运行测试

单元测试仅需 Node.js 20 或更高，无须安装 NPM 依赖：

```powershell
npm test
```

浏览器测试使用 Python Playwright：

```powershell
py -m pip install -r requirements-test.txt
py -m playwright install chromium
py tests/browser/run_browser_tests.py --evidence test-results\zoom
```

测试程序在运行时自己开启本地 HTTP 服务器并关闭。受限环境可以用下面的等价源码注入模式（不测试 HTTP/缓存/部署）：

```powershell
py tests/browser/run_browser_tests.py --inline --evidence test-results\zoom-inline
```

本次实际执行方式、测试数量、跳过项和限制见 `docs/CANVAS-ZOOM-TEST-REPORT.zh-CN.md`。可查看 `evidence/zoom/` 下的完整运行记录。

## 回退

本功能和旧 viewport 修复分开提交。上线后有问题，使用本功能 PR 的 Revert 生成回退 PR，或在修复分支中回退本功能 commit。不要用 `reset --hard`／强推 main，也不要删除之前的 stash。
