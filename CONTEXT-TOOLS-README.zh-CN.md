# Happy Colors — Colorful E1

基于 GitHub main `497b49e8d94fa666f2b524b9082fbb406b00e94e`（五张原图模板合并后）。
本包仅用于预览、验收；没有创建/推送远端分支、PR 或修改线上网站。

## 本次三个功能

1. **XS 极细画笔**：新增 2 px（画作坐标）笔宽。原来的 S=8、M=16、L=28、XL=44 不变。
   点击 Brush，在按钮下方出现唯一的笔宽选项；选中后隐藏。手机还会同时关闭抽屉。
   Sparkle、Outline、Eraser 也可以通过自己的按钮选粗细，选完不切换成 Brush。
2. **手机按功能显示面板**：Tools 只显示绘画工具；Colors 显示颜色与画纸背景；
   Pages 显示模板与上传；Stickers 只显示贴纸；Language 沿用原来的语言对话框。
   大屏仍使用侧栏。选项是真正隐藏，键盘不能跳到不相关的隐藏控件。
3. **矩形选区内容缩放**：工具面板中的 Select／框选 -> 在画布上拖出矩形 ->
   用选区的 ± 或在框内用两指调整 -> Apply／应用，或 Cancel／取消。
   这是像素内容编辑，不是查看放大镜。已有全画布视图缩放不变。

## 选区行为（重要）

- 范围 25%–300%，± 每次 25 个百分点，等比例从选框中心缩放。
- 矩形框的位置和大小不变；框外每个像素保持不变。
- 放大超出选框的部分会被裁掉。框选时给图案多留一些空白。
- 缩小时空出的部分变透明，显示当前画纸背景；不自动猜测被移除部分的底图。
- 矩形里所有内容（线条、填色、贴纸、照片背景）一起缩放；不做 AI 物体分割。
- 预览完全在独立临时画布上；原画布直到 Apply 才写入。Cancel 不新增历史。
- Apply 是一次 Undo 动作；100% 不变的 Apply 不新增动作。
- 选区预览期间 Save、Undo、Redo 暂时不可用。先 Apply 或 Cancel。
- 选择其他工具/模板会取消尚未应用的预览，保留原画。
- 用户自身线稿仍须闭合才能可靠 Fill；缩小极细线条可能损失细节，可以 Undo。
- 旋转不重新取样整个画作。手势放大与修改选区是两种不同状态。

## 先独立试玩

完整预览 ZIP 解压到新的目录（不要清空 Git 仓库），运行：

```powershell
py -m http.server 8000 --bind 0.0.0.0
```

在同一可信家庭网络的手机/iPad 打开 `http://电脑局域网IP:8000/`。
测试结束 Ctrl+C 关闭。不要开放路由器外网端口。
桌面/平板版本标记是 `Colorful E1`；手机窄屏会隐藏品牌标记。

## 交付文件

原有十个运行文件保留；新加 `context-tools.css`、`selection-resize.js`。
更新 `index.html`、`i18n.js`、`mobile-ui.js`。绘画主代码 app.js、
全画布手势 canvas-zoom.js、Save 模块、原来的样式与五张 PNG 不变。

真机验收通过后，建议从相同 main 基线新建 `selection-context-tools` 分支，
把**增量包内容直接覆盖合并**进去；不要先删除旧文件，也不要再应用旧 patch。
完整试玩包不是替换整个仓库的文件清单，仓库内历史文档和证据仍应保留。

## 测试

```powershell
npm.cmd test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
npm.cmd run test:ui
npm.cmd run test:context
```

用户电脑默认通过本地 HTTP 运行。当前生成环境使用 `--inline` 的限制及完整
实测数量见 `docs/CONTEXT-TOOLS-TEST-REPORT.zh-CN.md`。
