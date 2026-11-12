# Happy Colors 原图模板 — Colorful P1 测试报告

## 基线与范围

读取并固定 GitHub `lienahu/Happy-Coloring` 的 main：
`64b3732c61dc24dcb20ed221d0ba171fb186e24a`。
当前 main 已包含 Colorful、七语言与 iPhone Save 修复。将已有 S1 包的十个运行文件
及 package.json 的 Git blob SHA 与本次读取的 main tree 对比，全部相同。
见 `evidence/templates/base-main.json`。

本次没有创建/修改远端分支、PR、main 或线上网站。

仅替换 app.js 中程序绘制模板及 Upload 的图片载入代码段，形成统一导入函数。
index.html 仅更新版本标签和两处缓存键；i18n.js 仅加七条加载失败提示。
五张用户附件按原字节复制到 assets/coloring-pages，没有图像重绘或二值化。
文件对应与 SHA-256 见 `original-assets.json`。

## 实际执行的最终结果

| 检查 | 结果 |
|---|---|
| Node 单元测试 | **247 通过，0 失败**（原有 201 + 新增 46） |
| CRLF 换行的副本上再次运行单元测试 | **247 通过，0 失败**，不重复计入上行数量 |
| 最终浏览器设备/用例组合 | **446 次：437 通过，9 跳过，0 失败或错误** |
| 最初手机横屏新模板专项试跑 | 21 通过，另存 initial-new，不重复计入最终数量 |
| 运行 JavaScript 语法检查 | 5 个文件全部通过 |
| 项目子路径 HTTP 资源读取 | 首页成功；14 个 JS/CSS/PNG 资源状态 200、字节匹配 |

## 浏览器覆盖

| 配置 | CSS 视口 | 执行用例 | 通过 / 跳过 |
|---|---|---:|---:|
| 桌面 | 1280×800 | 101 | 92 / 9 |
| 平板横屏 | 1180×820，DPR 2 | 101 | 101 / 0 |
| 手机竖屏 | 393×851，DPR 3 | 101 | 101 / 0 |
| 手机横屏 | 851×393，DPR 3 | 101 | 101 / 0 |
| 平板竖屏 | 820×1180，DPR 2 | 21（模板专项） | 21 / 0 |
| 小手机横屏 | 667×375，DPR 2 | 21（模板专项） | 21 / 0 |

9 个跳过项均是无触屏桌面配置下的原有触控用例；对应平板/手机完整套件已运行。
语言循环（7 种语言 × 5 个按钮）只是一个用例，不按循环次数重复计数。

## 核心断言

- 五个真实模板按钮没有触发系统 filechooser。
- 每张模板载入后的全画布原始像素哈希，与 Upload 选择同一张 PNG 完全一致。
- 同一图通过两个入口在同一个区域填色后，全画布原始像素哈希仍完全一致。
- 填色后的主体像素匹配目标 RGBA；独立细节、外部区域和暗色线条保持不变。
- 放大至 250% 并移动后依然填中目标区域；Undo/Redo 恢复准确。
- 每张图的 Download PNG 都实际产生了下载字节；检查 PNG 尺寸和目标填色色值。
- 图片切换是一次历史动作；工具、画笔颜色/粗细、背景、缩放和滚动位置保留。
- Blank/新绘画/Undo 会使尚未完成的旧载入请求失效；快速换图只采纳最后一次。
- 解码失败、不可读来源与超时，不清空已有画作；七语言错误提示正确。
- Upload 仍使用原生文件选择控件；重复上传同一文件与 blob URL 回收有覆盖。
- 原有自画区域 Fill、上传闭合图 Fill、Brush、Sparkle、Eraser、贴纸、缩放、
  语言、Save、背景、设备尺寸变化的回归套件一并重跑。

## 测试适配说明（未减少功能断言）

原先两条浏览器断言使用程序线稿的固定“圆头/眼睛”坐标，本次替换为附件原图的
主体与独立细节坐标，继续验证不会泄漏到相邻区域。模板按钮操作会等待图片解码。
原有一条单元测试从“出现 vector stroke”改为“解码后 source-over 导入”。
严格源码边界测试允许新的图片块，但把它还原后计算出的 app.js blob 必须与 main
相同：Fill、笔迹、Save 及手势代码区域仍受到完整性检查。
源码哈希检查适配 LF/CRLF；PNG 仍必须逐字节相同。
本次最终运行没有断言失败，没有隐藏失败或使用重试覆盖失败结果。

## 运行环境及不能据此保证的内容

Node.js v22.16.0、Python 3.13.5、Playwright 1.57.0、Chromium 144.0.7559.96，Linux。
尝试了浏览器访问 http://127.0.0.1，本环境返回 ERR_BLOCKED_BY_ADMINISTRATOR。
因此浏览器套件采用精确源文件注入；测试专用的 Image.src 适配层把这五个相对图片
地址映射为同一原始 PNG 字节的 data URL，再由真实 Chromium 图片解码器解码。
没有修改被测应用的实际导入/Fill 函数来迎合测试。
这验证了浏览器 DOM、像素、事件与导出，不验证真实 Safari、iOS、网络缓存或部署。

另外用 Python urllib 对真实静态 HTTP 服务器的 /Happy-Coloring/ 子路径做资源测试，
验证首页、版本化 JS/CSS 和五个 PNG 能按相对路径读取。这不是 iOS 浏览器测试。
没有可用的 WebKit 或物理 iPhone/iPad；系统分享仍沿用明确模拟的 API 场景，
没有声称打开了苹果原生分享面板或把照片写进 Photos。

请完成真机清单后，再创建 PR 合并。现有 Fill 算法没有新增“补洞”能力，
用户自己画的线稿仍需闭合；不承诺任何照片或开放轮廓都能像闭合线稿一样填色。

## 重跑

```powershell
npm test
npm run test:ui
npm run test:templates
py tests/check_template_resources.py
```

本机普通预览默认 HTTP。复现当前受限环境的后备方式：

```powershell
py tests/browser/run_template_tests.py --inline --profiles desktop tablet_landscape phone_portrait phone_landscape
py tests/browser/run_template_tests.py --inline --templates-only --profiles tablet_portrait phone_small_landscape
```

详细证据位于 `evidence/templates/final-summary.json`、`final-*/results.json`、
各 profile 日志、`unit-final.log`、`unit-crlf.log`、`syntax.json`、`http-resources.json`。
运行截图示例 `preview/templates/tablet_landscape-unicorn.png` 是实际测试应用局部填色，
不代表图片资产本身被修改。
