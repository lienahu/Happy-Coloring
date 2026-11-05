# Happy Colors · Apple Colorful 固定界面候选版

本次选择的是设计对比图中的 B「Apple Colorful」。这是一个固定产品界面，而不是给儿童切换的主题集合。页面中没有 Style 按钮、主题弹窗、主题链接或主题偏好读取。

## 设计

淡紫、浅蓝、粉色的低饱和渐变工作区；半透明白色工具面板；紫色主要操作按钮；统一 SVG 工具图标、圆角和选中状态。画纸及画笔颜色与界面配色分离。系统字体由设备提供，包内不包含任何字体文件、Apple 图标资源或 Apple 品牌标志。「Apple Colorful」是设计方向名称，应用品牌仍是 Happy Colors。

## 保留的功能

- 单指绘画、Sparkle、橡皮、填色、上传、自画、内置模板、贴纸、背景、Undo/Redo、完整 PNG 保存。
- 双指只缩放和移动画布，100%–400%；菜单和上方按钮不缩放。
- iPhone 横屏使用窄快捷栏，竖屏使用底部快捷入口。工具面板可展开/关闭。
- Large / Fit 保持等比例；Large 仅放大视图，不改变保存的图像范围。

## 六个必需运行文件

```
index.html
style.css
apple-colorful.css  # 新增：唯一固定外观
app.js
canvas-zoom.js
mobile-ui.js        # 新增：手机抽屉/布局；没有主题切换代码
```

`app.js`、`canvas-zoom.js`、`style.css` 与 `main@7cbbeff631c9ae9b0e519cb824f6917c4a3afd17` 的绘画版本保持字节相同。本次未重写绘画或缩放引擎，也没有加入 AI 接口。

## 先独立预览，不直接覆盖 main

解压到一个新的目录。可在电脑直接打开 `index.html`。iPhone / iPad 在同一家庭网络内使用上次的测试方式：

```powershell
cd C:\project\happycolor\colorful-preview
py -m http.server 8000 --bind 0.0.0.0
```

手机打开 `http://电脑局域网IP:8000/`。确认电脑防火墙只为可信家庭私有网络放行，不开放路由器公网端口。完成后在 PowerShell 按 Ctrl+C 停止。

页面桌面/平板标题处标记 `Colorful 1`；窄屏会隐藏标题以节省画布空间，可用右上角紫色保存按钮和无 Style 按钮辅助确认。

截图中的猫是通过 Upload 载入的既有示例，存于 `preview/example-cat.png`；它不表示内置模板已被更换。

## 安装到开发分支

在真实 iPhone/iPad 上完成 `docs/COLORFUL-DEVICE-CHECKLIST.md` 后，工作区干净时：

```powershell
cd C:\project\happycolor\code\Happy-Coloring
git status
git switch main
git pull --ff-only origin main
git switch -c apple-colorful-ui
```

把包里的六个运行文件以及相关测试/说明文件复制到仓库。保留已有 `.git` 和其他项目文件。不要恢复以前的实验 stash。若之前拷过四主题预览，旧 `ui-themes.css`、`themes.html` 已不再被此 `index.html` 引用；这两个旧文件可另行备份，不应作为应用入口继续使用。

也可选择应用随附的 `apple-colorful-ui.patch`（针对以上 main 基线）。完整复制和应用 patch 二选一，不要同时做：

```powershell
git apply --check .\apple-colorful-ui.patch
git apply .\apple-colorful-ui.patch
```

测试无误再 commit → push 功能分支 → 创建 PR → 检查 → 合并。此交付没有推送或合并任何远端分支。

## 重跑自动化测试

Node.js 20 或以上运行单元测试，不需要 npm 安装依赖：

```powershell
npm test
```

浏览器测试需要 Python 测试依赖和 Playwright 浏览器：

```powershell
py -m pip install -r requirements-test.txt
py -m playwright install chromium
py tests/browser/run_colorful_tests.py --profiles desktop tablet_landscape phone_landscape phone_portrait
```

默认测试通过本地 HTTP 加载实际文件；`--inline` 是浏览器导航受限时才使用的源码注入选项，不测试 HTTP、缓存或部署。当前交付的实际执行方式与结果见测试报告。真实设备照片选择器、Safari 地址栏/刘海安全区、Apple Pencil 仍需人工确认。

这是网页测试候选版，不是已打包或已提交审核的 iOS 安装包。
