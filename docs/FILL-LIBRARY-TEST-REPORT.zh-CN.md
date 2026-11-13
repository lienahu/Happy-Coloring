# Happy Colors — Colorful F1 填充样式与懒加载图库测试报告

## 基线与交付范围

只读核对 GitHub main：`497b49e8d94fa666f2b524b9082fbb406b00e94e`（P1）。
开发基线是上一份准确的 `happy-coloring-context-tools-tested.zip`（E1），因此保留 XS、笔宽弹出、手机菜单隔离和选区内容缩放。
**没有修改任何 GitHub 分支、PR、main、线上网站或用户电脑。**
增量包为相对 main 的 E1＋F1 累计覆盖包，不要求用户先合并 E1，也不删除旧文件。

新增 15 种 Fill 样式和容易／一般／困难各 10 张实际 PNG。原五个快捷模板保留；其原始 PNG 字节不变。
图库有独立 192×192 缩略图，每页6张、当前每档6＋4；目录首次打开才 fetch，当前页缩略图进入视口才分配 src，选中后才读大图。
新增25张图为程序化矢量线稿或原角色组合场景；不是额外购买/手绘的商业插画。详见图案目录与生成源码。

## 最终实际执行结果

| 检查 | 结果 |
|---|---|
| Node 单元测试 | **378通过，0失败**（E1原有304＋新增74） |
| Windows式 CRLF 文件副本单元测试 | **378通过，0失败**；不重复计入上行 |
| 浏览器最终设备／用例组合 | **638执行：627通过、11跳过、0失败／错误** |
| JS语法检查 | 8个运行脚本通过 |
| 源码／资源冻结检查 | 76个文件与最终测试前的 SHA-256 一致 |
| HTTP项目子路径资源检查 | 76个 HTML/JS/CSS/JSON/PNG 资源均200且字节一致 |
| 增量覆盖原图模板P1副本 | 0旧文件删除；76个运行／资源校验一致；378项单元测试通过 |

| 配置 | 用例数 | 通过 | 跳过 |
|---|---:|---:|---:|
| desktop | 148 | 137 | 11 |
| tablet_landscape | 148 | 148 | 0 |
| phone_portrait | 148 | 148 | 0 |
| phone_landscape | 148 | 148 | 0 |
| phone_mini_portrait | 23 | 23 | 0 |
| phone_tiny_landscape | 23 | 23 | 0 |

四种主要配置执行全部148个测试；320×568小手机竖屏和568×320小手机横屏执行23个新增用例。
11个跳过均为无触屏desktop中的触屏专用用例，对应触控配置已运行。
一个用例中循环15种样式、30张图片或7种语言不重复放大统计数字。

## 关键断言

- 实际点击Fill展开15个预览，选后收起；与Brush笔宽面板互斥。
- 15种样式逐一在闭合区域填入；外围像素和黑边不变；黑色与白色也可使用花纹。
- 同一片花纹可再次改成其它花纹或纯色，不只改变一个圆点/一条纹路。
- 模式元数据与Undo/Redo一起恢复；新图／Blank／Upload不残留旧区域。
- 新画一条分界线后，只替换所点击一侧；不把新笔迹误当旧花纹覆盖。
- 放大与移动后填色落点正确；完整PNG导出含花纹与背景，不是当前可见局部。
- 启动时没有图库目录／新图库图片读取；打开后仅当前页缩略图，选中才分配该大图来源。
- 三档各10个真实资源、唯一ID、不同缩略图和大图，6＋4分页正确。
- 30张图逐一载入，并在每张选定的闭合区域使用波浪纹填色。
- 浏览难度／翻页不改变画作或历史；目录失败可重试；图片失败／关闭加载不清空作品；快速选择只采纳最后请求。
- 七种语言覆盖新增按钮和图案名；小屏按钮至少44px；关闭、键盘Escape、难度tab和焦点恢复。
- E1所有旧功能回归仍在：原五图模板与Upload的像素一致性、普通Fill、Brush、XS、Sparkle、Eraser、选区、缩放、上传、语言、保存、背景和20步Undo/Redo。
- 50张/档的数据分页逻辑有单元测试，但本包实际只提供10张/档，不声称已提供150张图。

## 实现边界

`canvas-zoom.js`、原有Save模块、基础样式和原五张PNG与E1逐字节相同。
`app.js`有5处明确的Fill分发／快照／恢复／新图重置挂接；剥除这些精确挂接后仍与E1完整一致。
普通纯色、无花纹历史时保留既有Fill实现。花纹路径采用相同四邻域和RGBA总容差45规则，用跨度掩码限制写入，随机输入与参考算法逐像素对比。
`selection-resize.js`仅增加应用选区时对该矩形花纹元数据的失效处理。
`mobile-ui.js`仅协调新面板与既有菜单，包括下面实际捕获的点击问题。

## 首轮发现的问题及处理

1. 初轮23项手机横屏专项有1项功能失败：Brush笔宽展开时，点击Fill会在pointerdown阶段先收起笔宽，导致按钮在pointerup前移位，点击丢失。把“点外部关闭”放到click阶段，保留交互断言，专项复测通过；最终四大配置完整回归再次通过。
2. 同一轮1项测试错误：测试中的异步Image.src适配尚未赋原生src，读取属性得到null。记录实际分配的本地路径而不是读取尚未赋值的属性；测试直接进入easy第一页，避免测试辅助函数先开easy再切medium造成重复页请求假设。仍严格验证只出现活动页缩略图、未读大图，没有删除懒加载断言。
3. 新app.js挂接最初触发1项旧源码完整性断言。测试现在仅剥除5处精确挂接再比较旧源码，不再错误要求这5处也不能变化；其它绘画／Save／手势源码仍受同一检查约束。
4. 一次完整运行在结束前主动中止，用于修正两张宫殿图案顶部旗帜被裁的问题。修正图片后重新冻结76个文件、从头执行本报告的最终运行。中断日志不计入最终通过数，保留在interrupted-final目录。

初始日志、失败截图、专项复测和完整最终结果均在 `evidence/fill-library/`，不是只保存成功截图。

## 环境与不能据此保证的内容

Node v22.16.0、Python3.13.5、Playwright1.57.0、Chromium144.0.7559.96，Linux。
本环境浏览器访问本地HTTP被策略阻止（ERR_BLOCKED_BY_ADMINISTRATOR），因此浏览器使用 `--inline` 注入最终文件，并由明确的测试适配层提供目录JSON和原始PNG字节。
这些用例验证真实Chromium的DOM／canvas／输入管线、像素、图片解码和文件下载；懒加载断言检查应用何时分配资源，并非真实Safari网络吞吐测试。
额外由Python urllib连接真实静态HTTP服务器，验证 `/Happy-Coloring/` 项目子路径下全部资源200及字节匹配；这不替代Safari网页加载测试。
没有连接真实iPhone/iPad，没有执行Safari/WebKit或Apple Pencil。继承的原生分享／浏览器存储模拟仍是明确模拟，不声称Apple分享面板或Photos实际工作。

## 行为限制

- 轮廓仍须闭合，没有自动补洞或照片对象识别。
- Sparkle为静态可导出的纹理，不是发光动画；当前只使用所选颜色及其明暗对比色。
- 导出PNG再上传不会携带花纹区域成员信息，内部纹理会成为普通像素边界。
- 选区内容变换应用后，只使该矩形内的成员信息失效；变换后的区域按普通位图分析，框外元数据不变。
- 没有自动保存画作；刷新前先保存。
- 必须先在iPhone/iPad完成真机清单再合并。请使用HTTP/HTTPS预览，而非file://。

## 重跑

```powershell
npm.cmd test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
npm.cmd run test:ui
npm.cmd run test:fill-library
npm.cmd run test:library-resources
```

当前受限环境：

```powershell
py tests/browser/run_fill_library_tests.py --inline --profiles desktop tablet_landscape phone_portrait phone_landscape
py tests/browser/run_fill_library_tests.py --inline --new-only --profiles phone_mini_portrait phone_tiny_landscape
```

## 技术参考

- MDN Lazy loading: https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Lazy_loading
- MDN putImageData: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/putImageData
