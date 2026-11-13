# Happy Colors — Colorful E1 测试报告

## 基线与交付范围

GitHub main: `497b49e8d94fa666f2b524b9082fbb406b00e94e`（原图模板 merge #5）。
本地基线关键运行文件 Git blob SHA 与读取的 main tree 一致。
没有创建或修改任何远端分支、PR、main、发布网站或用户电脑。

新增矩形选区内容缩放、Brush 等工具的展开式笔宽菜单、XS=2 px，
手机 Tools / Colors / Pages / Stickers 各自显示相关功能。
新文字在原有七语言字典中都有对应翻译，固定 Colorful 外观不变。

矩形内容在固定框内缩放（25%–300%），框外像素不写入，超框部分裁切，
缩小空出的地方显示画纸背景。预览不是正式画布；Apply 一次产生一个 Undo，
Cancel 不产生历史，100% 原样应用不产生历史。不是智能抠图或查看放大镜。

## 实际执行结果

| 检查 | 结果 |
|---|---|
| Node 单元测试 | **304 通过，0 失败** |
| 浏览器最终用例/设备组合 | **572 执行：561 通过，11 跳过，0 失败/错误** |
| JS 语法检查 | 6 个运行脚本通过 |
| HTTP 子路径资源读取 | 首页与 JS/CSS/PNG 共 17 个资源状态 200，字节一致 |
| 最终运行源码冻结检查 | 12 个文件 SHA-256 与最终测试前记录一致 |

完整 125 项用例分别运行于 desktop、tablet_landscape、phone_portrait、
phone_landscape，共 500 次。24 个新增用例另外在 320×568 mini 手机竖屏、
568×320 极小手机横屏、820×1180 平板竖屏运行，共 72 次。
11 项跳过全部在无触屏 desktop；其中旧的触控用例 9 项，新增选区真实触控管线
用例 2 项。对应触屏配置均执行。七语言循环算一个测试，不按循环次数膨胀数字。
初始手机横屏的 24 项试跑也全部通过，但没有重复计入最终数量。

## 像素与交互断言

- 实际点击 Brush 打开唯一的 XS/S/M/L/XL 控件；选择后自动关闭。
- XS 状态为 2，画出的中心像素存在，线外像素透明；五种笔宽各产生一次绘画历史。
- Sparkle/Outline/Eraser 选择笔宽后不被错误切换成 Brush。
- 手机按真实 DOM 可见性检查：工具、颜色/背景、模板/上传、贴纸相互隔离。
- 全部新文字覆盖七语言；小屏操作按钮可见且触控高度至少 44px。
- 矩形预览期间原画布像素与历史完全不变，Save 暂时禁用。
- 放大与缩小后逐像素比较：框内发生变化，框外差异严格为 0。
- Apply/Undo/Redo 的全画布像素哈希精确恢复；Cancel 和原样 100% 不新增历史。
- 通过 Chromium CDP 输入管线拖出选框、双指缩放选区；全画布 zoom 不变。
- 已放大全画布并移动后仍能在正确坐标编辑选区；横竖屏切换保留选区与画作。
- 小框被拒绝、重新框选不改原图、旧预览不能覆盖后来变更过的画作。
- 应用后 Fill 正常；Save 下载整个已应用的画作，不包含 DOM 中的选框边线。
- 原有五张模板/Upload 的像素一致性、填色、Brush/Sparkle/Eraser、Undo/Redo、
  语言、手势、背景、原生浏览器 filechooser 事件、完整 PNG 保存回归一并执行。

## 本次测试适配记录

最初沿用的单元套件有 1 项失败：它要求 `mobile-ui.js` 与旧 main 字节不变，
而本次需求正是修改这个文件的菜单行为。这条旧字节约束被新的菜单内容隔离、
笔宽展开/关闭、键盘和七语言行为测试取代；原日志保留 `unit-initial.log`。
原有 app.js、canvas-zoom.js、Save 模块、基础样式的完整性断言仍保留并通过。
本次 304 项为旧 247 项去掉该不再适用的 1 项、加入 58 项后得到。

原浏览器辅助函数假定手机侧栏显示所有功能。现在 helper 会先点击对应菜单，
再操作原控件。旧上传/侧栏滚动用例改为：面板溢出时验证可以滚动，然后实际
触发 filechooser；不溢出时验证无错误滚动及控件可达。文件内容/填色断言未删除。
这些行为变化是新需求造成，不是把产品故障改成通过。
最终全部浏览器运行无失败，无重试覆盖失败结果。

## 运行文件边界

保持相同：`app.js`、`canvas-zoom.js`、`save-picture.js`、`style.css`、
`apple-colorful.css`、`languages.css`、`save-picture.css`，以及五张原 PNG。
更新：`index.html`、`i18n.js`、`mobile-ui.js`。
新增：`selection-resize.js`、`context-tools.css`。
`package.json` 的默认浏览器入口更新到新回归套件。

## 环境及测试边界

Node.js v22.16.0，Python 3.13.5，Playwright，Chromium 144.0.7559.96（Linux）。
浏览器访问本地 HTTP 被环境策略以 `ERR_BLOCKED_BY_ADMINISTRATOR` 拦截。
因此浏览器通过 `--inline` 注入最终 HTML/CSS/JS；模板 URL 使用附件原 PNG
字节的 data URL 适配层。此方式测试真实 Chromium DOM、canvas 和输入管线，
但不验证实际 GitHub Pages 网络、缓存、原生 iOS 或 Safari。

额外使用 Python urllib 从实际本地 HTTP `/Happy-Coloring/` 子路径读取资源，
17 个资源均成功并字节匹配。这不是 Safari 网络测试。
没有连接真实 iPhone/iPad，没有运行 WebKit，也没有验证 Apple Pencil 真机。
旧分享用例仍使用明确模拟的 canShare/share API；没有声称打开苹果系统分享面板。
语言持久化测试仍保留前版注明的模拟 storage 模式。

请先完成 `docs/CONTEXT-TOOLS-DEVICE-CHECKLIST.zh-CN.md`，再合并功能分支。

## 复跑

```powershell
npm.cmd test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
npm.cmd run test:ui
npm.cmd run test:context
```

正常用户电脑默认 HTTP。当前受限环境执行：

```powershell
py tests/browser/run_context_tests.py --inline --profiles desktop tablet_landscape phone_portrait phone_landscape
py tests/browser/run_context_tests.py --inline --new-only --profiles phone_mini_portrait phone_tiny_landscape tablet_portrait
```

日志和逐用例结果位于 `evidence/context/`；`integrity.json`、`syntax.json`、
`http-resources.json` 提供对应检查记录。截图是实际应用渲染。

## 技术参考

- MDN Canvas drawImage: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/drawImage
- MDN Canvas putImageData（按位图坐标写入，不受变换矩阵影响）: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/putImageData
- MDN Pointer capture: https://developer.mozilla.org/en-US/docs/Web/API/Element/setPointerCapture
