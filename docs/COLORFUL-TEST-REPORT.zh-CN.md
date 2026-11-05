# Apple Colorful 固定界面测试报告

## 范围与基线

- GitHub main 基线：`7cbbeff631c9ae9b0e519cb824f6917c4a3afd17`。
- 选择 B「Apple Colorful」作为唯一固定界面。没有儿童 Style 按钮、主题弹窗、主题链接、localStorage 主题偏好读取或 URL 切换。
- 新增固定外观 `apple-colorful.css`，沿用 iPhone 横屏大画板/抽屉布局并精简 `mobile-ui.js`。
- 运行文件 `app.js`、`canvas-zoom.js`、`style.css` 与基线字节相同；校验见 `evidence/base-and-engine-integrity.json`。
- 没有提交/推送 GitHub，没有修改 main，也没有发布线上网站。

## 实际执行结果

| 检查 | 结果 |
|---|---|
| Node.js 单元测试 | 95 通过，0 失败 |
| 浏览器测试去重后的设备/用例组合，含复测 | 268 组合：259 通过，9 跳过，0 最终失败 |
| JavaScript 语法检查 | app.js、canvas-zoom.js、mobile-ui.js 全部通过 |
| unified patch 应用 | `git apply --check` 通过；应用后文件与测试副本相同 |

执行环境：Node.js v22.16.0，Python 3.13.5，Playwright 1.57.0，Chromium 144.0.7559.96（Linux）。

### 浏览器覆盖

完整 52 项用例分别运行于 desktop、tablet_landscape、phone_landscape、phone_portrait，共 208 次。新增固定界面/布局的 12 项用例另外在 tablet_portrait、tablet_split_view、phone_small_landscape、phone_mini_portrait、phone_large_landscape 上运行，共 60 次。

覆盖绘画像素、Sparkle 高亮、橡皮、Undo/Redo、自画闭合区域填色、当前内置模板填色、上传 PNG 填色、真实浏览器 filechooser 事件、重复上传、旋转、双指缩放/移动、滚动滑条、缩放后落笔、完整 PNG 导出、界面/画纸颜色分离、抽屉焦点、阻止存储时的可用性、模拟安全区、减少动态效果和无主题入口。

9 项跳过均为无触屏桌面配置下的触控专用用例，在平板和手机触控配置中已执行。

### 首轮发现的测试用例假设问题与复测

首轮完整运行结果为 208 次、3 次断言失败、1 次用例错误、9 次跳过，未将其隐去：

1. 上传入口从旧侧栏底部上移后，桌面/平板/手机竖屏上的旧用例假定「滚动到 Upload 必然使 scrollTop > 0」不再成立。修正用例为先把侧栏滚到底部，再返回 Upload。仍然验证 scrollTop > 0、实际 filechooser 事件、上传图像填色及同一文件重复上传，不是删除功能断言。四种主要设备复测均通过。
2. desktop 配置在安全区用例里变为窄窗口时，旧测试辅助函数仍强制调用 touch tap，但 desktop 配置本身不支持 touch。改为按设备配置使用真实 mouse click 或 tap。四种主要设备复测均通过。

**这两处修正仅在测试脚本，界面和绘画运行代码没有为绕过测试而修改。** 实际总测试调用为 276 次，去重后 268 个组合的最终结果如上。全部原始日志、错误截图、复测和逐用例汇总均包含在包内。

## 测试边界

此环境浏览器访问本地 HTTP 被管理员策略拦截（`net::ERR_BLOCKED_BY_ADMINISTRATOR`）。因此浏览器验证使用最终本地 HTML/CSS/JS 的精确源码注入模式 `--inline`。它测试真实 Chromium 引擎的 DOM、布局、触控事件和 canvas，但不测试 HTTP 资源下载、网站缓存、GitHub Pages 发布，也不模拟真实 iOS 操作系统。

没有连接真实 iPhone/iPad，没有运行 Safari/WebKit，没有验证 Apple Pencil、真实照片选择器、Safari 地址栏动画或 iPhone 实际刘海区域。安全区用例是 CSS inset 的模拟。真实设备仍需完成 `docs/COLORFUL-DEVICE-CHECKLIST.md`。

## 重跑

```powershell
npm test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
py tests/browser/run_colorful_tests.py --profiles desktop tablet_landscape phone_landscape phone_portrait
```

普通用户电脑默认通过本地 HTTP 运行；不需要加 `--inline`。截图里的猫是既有上传示例，不是本次新添加的内置模板。

## 交付定位

独立网页测试候选版。推荐在新的目录预览，确认喜欢的视觉效果与真机行为后，再通过 `apple-colorful-ui` 功能分支提交 PR。不是已经完成 App Store 打包或审核的 iOS 应用。
