# Happy Colors — Colorful F1

## 本次交付

15 种填充样式，以及容易／一般／困难各 10 张、共 30 张实际图案的懒加载图库。
保留固定 Apple Colorful、七语言、iPhone Save、画布双指缩放、原图上传；也包含上一份 E1 候选版的 XS 2 px 画笔、分类菜单和矩形内容缩放。不是线上已发布版本。

## 使用

- 工具 → 填色：展开 15 个图案预览，选择后面板自动收起，使用当前画笔颜色。
- 图案 → 图案库：选择难度，每页最多 6 张；当前每档为 6＋4 两页。
- 原来的独角兽、公主、小猫、蝴蝶、恐龙快捷按钮、空白和上传保留。
- 打开图库只读目录与当前页可见缩略图；点选某张后才读那一张大图。继续使用既有 `loadPictureSource()`，不会调起相册来假装自动选择本地文件。
- 默认纯色；Sparkle 是能保存进 PNG 的静态闪光纹理，不是动画。
- 同一区域可从花纹改成另一种花纹或纯色，Undo/Redo 一次恢复一个操作。

## 在手机/平板试用

将完整包解压到一个新的目录，然后在该目录的 PowerShell 执行：

```powershell
py -m http.server 8000 --bind 0.0.0.0
```

让手机和平板与电脑连接同一家庭网络，在 Safari 打开 `http://电脑的局域网IP:8000/`。
这一版图库通过 fetch 读取 JSON，请使用本地 HTTP 或正式 HTTPS，不要双击 `index.html` 以 file:// 作为完整图库验收。
家庭网络 HTTP 下原生 Web Share 可能不可用；下载 PNG 和预览备用方式仍保留。
测试结束用 Ctrl+C 停止服务器，不要开放路由器端口。
版本标记 **Colorful F1**；小屏会隐藏品牌文字。

先完成 `docs/FILL-LIBRARY-DEVICE-CHECKLIST.zh-CN.md`。不会自动保存作品，刷新前先保存。

## 文件与发布

新增运行文件：`fill-patterns.js`、`fill-library-ui.js`、`fill-library.css`。
新增资源：`assets/template-library/catalog.json`、独立 `thumbs/` 缩略图、`full/` 大图。
完整运行需要全部 JS、CSS 和 assets，不要只复制 app.js。

远端基线为 `main@497b49e8d94fa666f2b524b9082fbb406b00e94e`（P1）。
增量包是 **E1＋F1 的累计覆盖包**，可用于这个主分支或已放入 E1 的测试副本。
因为 E1 的框选和分类菜单此前尚未确认合并，不能只交付 F1 三个新文件。

**覆盖合并文件夹，不要删除仓库里的文件，不要执行 git clean/reset --hard。**
增量包没有 .git/.gitignore，不会更改仓库身份、旧 stash 或清除历史证据。
不需要再应用任何旧 .patch 文件；建议测试后使用 `fill-patterns-library` 新分支。

## 扩充到每档 50 张

添加一张大图和一张独立缩略图，再向 catalog.json 的 items 加入唯一 ID、level、src、thumb 和七语言 title。分页按实际数量计算，代码没有将容量限制为 10；测试覆盖 50 张/档的分页计算，但本包实际只交付 10 张/档。发布时同步维护图库入口的多语言数量说明，并再次进行真实图片载入、填色和延迟加载测试。

`tools/build_template_library.py` 提供本批新增线稿/组合场景的重建源码；运行应用不需要运行这个工具。
原五张附件 PNG 字节不变；新增 25 张为程序化线稿或利用原角色组成的场景，不是 25 张额外手工绘制/购买的商业插画。图案目录见 docs/TEMPLATE-CATALOG-30.zh-CN.md。

## 填色范围和限制

普通纯色仍走原来的区域算法；选择花纹或再填已有花纹时，用同样的四邻域和 RGBA 容差规则提取跨度掩码，在掩码内写入纹理。此功能不是全画布覆盖层。
为了再次点击时不会只改一个点/一条线，当前文档内保存花纹区域成员信息，并与 Undo/Redo 快照一起恢复。

- 轮廓仍需闭合；没有添加自动补洞或照片对象识别。
- 导出的 PNG 是普通合成图片。重新 Upload 该 PNG 不携带原来的花纹区域元数据；其内部装饰也会成为像素边界。
- 矩形内容缩放应用后，仅该矩形内的花纹元数据作废，外部保留；矩形内按普通位图重新识别。
- 样式密度固定在画作坐标，缩放查看不改变已填内容。
- 上一版框选为固定选框内的实际图案缩放，不是智能抠图；超框部分会裁切。

## 测试

```powershell
npm.cmd test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
npm.cmd run test:ui
npm.cmd run test:fill-library
npm.cmd run test:library-resources
```

默认浏览器测试使用本地 HTTP。当前执行环境因策略封锁浏览器 HTTP，使用 `--inline` 后备模式；详见本批测试报告，不将模拟测试称为 iPhone/Safari 真机通过。
