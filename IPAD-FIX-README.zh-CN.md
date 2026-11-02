# Happy Coloring — iPad viewport fix 1（待真机验收）

基于 `lienahu/Happy-Coloring` 的 `main@b3c2d4782b5ee58bab87ea349f105819a3f9d115`。
只在本地制作文件，没有提交、推送、合并或更改 GitHub Pages。

## 这次修改

* 画作的像素尺寸在页面初始化时确定，之后旋转、分屏、地址栏高度变化只调整 CSS 显示尺寸。
* 两个方向使用同一个缩放比例；画作不会因旋转被拉长，必要时周围会留空。
* 触摸位置换算成固定的画作坐标，填色也使用相同坐标系。
* 主手指/笔绘画时忽略第二个指针，支持 pointercancel / lostpointercapture / 切后台后结束笔画。
* 画布区域使用禁止手势的 CSS 和局部 touch/gesture 拦截；工具栏保留单指滚动和原生上传点击。
* 顶部工具栏自适应，侧栏独立滚动；窄屏颜色按钮改为两列，避免横向溢出。
* 取消依赖全页 `user-scalable=no`；没有尝试禁用系统辅助功能缩放。
* 为回归测试修正三个小问题：21 个快照支持 20 次撤销；恢复/加载图片不继承橡皮的混合模式；填色“颜色相同”判断包含透明度。

没有引入 AI，没有增加图层，没有替换 flood-fill 算法，没有恢复 stash 中的模板或 assets。当前 main 的简单程序绘制模板保持不变。

## 验证结果

见 `docs/TEST-REPORT.zh-CN.md` 和 `evidence/`。34 个 Node 单元测试通过；Chromium 六种尺寸配置的 120 次浏览器测试中 118 次通过、2 次桌面专属跳过、0 失败。四个旧版对照用例按预期失败。

**尚未满足正式发布条件**：本环境无法运行 WebKit，没有连接真实 iPad；Chromium 触屏模拟不能证明 Safari 原生双击/捏合、Apple Pencil 或照片选择器已修好。当前结果允许进行分支/真机预览，不建议直接合并 main。

## 先在 iPad 预览，不必修改仓库

将 ZIP 解压到一个新目录（不要直接覆盖仓库），例如：

```powershell
cd C:\project\happycolor\ipad-fix-preview
py -m http.server 8000 --bind 0.0.0.0
```

在另一窗口执行 `ipconfig`，找到电脑当前 Wi-Fi 的 IPv4 地址。例如地址是 `192.168.1.23`，则在同一家庭网络的 iPad Safari 打开：

```text
http://192.168.1.23:8000/
```

地址只是示例，替换成电脑实际地址。Windows 防火墙如询问，仅允许私有家庭网络。不要关闭防火墙、不要开放路由器端口；测试完用 `Ctrl+C` 停止服务。这个 Python 简易服务器仅用于本地测试，不用于公网生产。

页面标题旁应显示 **iPad fix 1**。现有 GitHub Pages 网站仍是旧 main，不是这个预览。

验收表在 `docs/IPAD-MANUAL-CHECKLIST.md`：重点验证双击、两指误触、横竖屏往返、画圆不变形、侧栏滚动后上传、画笔/填色/撤销保存。

## 应用到现有分支

你已经在干净的 `ipad-viewport-fix` 分支，旧实验保存在 stash。不要重新创建分支，也不要运行 `git stash pop` 或 `git clean`。

最简单的方法：只复制本包的 `index.html`、`style.css`、`app.js` 到：

```text
C:\project\happycolor\code\Happy-Coloring
```

`README.md`、stash 和旧图片备份不用动。随后检查 `git diff --stat`，应只显示这三个运行文件。

另一种方式是使用包内补丁（二选一，不要两种都做）：

```powershell
# 在仓库目录执行，将路径改成你的实际解压目录。
git apply --check "C:\project\happycolor\ipad-fix-preview\ipad-viewport-fix.patch"
# 上一步成功、没有错误时才执行：
git apply "C:\project\happycolor\ipad-fix-preview\ipad-viewport-fix.patch"
```

补丁已在该基线副本中执行 apply --check 和实际 apply 校验。若你的基线后来变动或检查报错，不要使用强制覆盖/--reject；先核对差异。

真机验收完成后再创建/更新 PR；本包不自动发布。测试源码、package.json、requirements-test.txt 可以另行一起加入此分支，但不是运行网页的依赖。

## 自己重跑测试

Node.js 20+（单元测试不需要 npm install）：

```powershell
node --test tests/unit/viewport.test.cjs
```

Python 3.10+，建议使用独立虚拟环境：

```powershell
py -m venv .venv-tests
.\.venv-tests\Scripts\python.exe -m pip install -r requirements-test.txt
.\.venv-tests\Scripts\python.exe -m playwright install chromium webkit
.\.venv-tests\Scripts\python.exe tests\browser\run_browser_tests.py
.\.venv-tests\Scripts\python.exe tests\browser\run_browser_tests.py --browser webkit
```

默认浏览器测试自动启动仅绑定 `127.0.0.1` 的临时 HTTP 服务。这里由于环境限制，实际执行采用 `--inline`，把同一份 HTML/CSS/JavaScript 直接加载进 Chromium，不覆盖网络、缓存或部署。

复现本包运行方式：

```powershell
py tests/browser/run_browser_tests.py --inline
```

旧版缺陷对照（预期返回失败，不能当成修复版失败）：

```powershell
py tests/browser/run_browser_tests.py --inline --baseline-only --root tests/baseline --profiles desktop tablet_portrait --evidence test-results/baseline
```

不要把未运行或跳过的测试计为通过；WebKit 通过之后仍需真实 iPad Safari 验收。
