# Happy Coloring — Canvas zoom 1 测试报告

## 范围与基线

- 来源：`lienahu/Happy-Coloring` 的 `main@0a6ae02c5895f3d77466bb3ec43090bb31b746c1`，即已合并 iPad viewport 修复的 main。
- 读取 GitHub 后，与先前测试包中的 `index.html`、`style.css`、`app.js` 逐文件 Git blob SHA 核对一致。
- 本次只增加画布局部缩放、双指平移、滚动控制和相应触摸路由；没有改写填色算法或替换模板。
- 未向 GitHub 写入文件、创建远程分支、合并 PR 或发布线上网站。

## 实际执行结果

| 检查 | 结果 |
|---|---|
| JavaScript 语法（`app.js`、`canvas-zoom.js`） | 通过 |
| 单元测试 | 67 通过，0 失败，0 跳过 |
| Chromium 浏览器测试 | 240 次执行：231 通过，0 失败，9 跳过 |
| Patch 应用与运行文件一致性 | 见 `evidence/zoom/patch-apply-check.txt` |

| 浏览器配置 | 执行数 | 通过 | 跳过 | 失败 |
|---|---:|---:|---:|---:|
| desktop | 40 | 31 | 9 | 0 |
| tablet_portrait | 40 | 40 | 0 | 0 |
| tablet_landscape | 40 | 40 | 0 | 0 |
| tablet_split_view | 40 | 40 | 0 | 0 |
| phone_portrait | 40 | 40 | 0 | 0 |
| phone_landscape | 40 | 40 | 0 | 0 |

9 项跳过均为桌面配置下的触摸专属用例（原有 2 项 + 新增 7 项）；同名用例在其他五种触控配置均执行并通过。
各配置在独立 Chromium 进程中运行。最终源代码 SHA256 与每份浏览器报告记录的值完全一致。

## 重点检查

- 双指距离改变只影响画布显示倍率，页面的 `visualViewport.scale` 保持 1；顶部按钮、侧栏矩形保持不变。
- 双指中点移动可平移画布；缩放以双指中点为锚点，画作边界限制滚动范围。
- 手指先画了一小段，再放第二根手指时，只取消当前未完成笔画，精确恢复此前像素，不新增 Undo 状态。
- Fill／贴纸选中时进行双指操作，不误填色、不误盖章；这些单指动作改在抬起时确认。
- 手势结束后剩余的一根手指不突然开始画；取消、失焦、三指误触后可以恢复。
- 放大且滚动后，Brush、Sparkle、Eraser、自画闭合区域填色、内置模板填色和上传 PNG 填色落点正确。
- 滚动滑条通过实际鼠标／触摸点击驱动，不仅仅检查属性存在。
- 旋转、浏览器栏高度变化、缩放、滚动都不重设 canvas 像素宽高、不拉伸画作。
- Undo／Redo 仍保留 20 步绘画；视图变化不消耗绘画历史。
- 导出的 PNG 尺寸为完整画作尺寸，并检查了当前视口外的笔画像素。
- 上传控件滚动后仍触发 file chooser；同一个文件可以重复选择。

## 浏览器与环境限制（必须保留）

- 实际浏览器：Chromium `144.0.7559.96`；Playwright `1.57.0`。
- 六种配置是桌面浏览器的 viewport/DPR/touch 模拟，不是真实的 iOS／Android 设备。
- 本环境的浏览器 localhost 导航被策略拦截，因此用 `--inline` 加载同一份 HTML、CSS、JS 源码完成测试；没有把这次执行描述成 HTTP、GitHub Pages、缓存或部署测试。
- 多指触摸用例使用 Chromium DevTools Protocol 的 `Input.dispatchTouchEvent` 注入浏览器触摸管线；其余包含真实鼠标／单指点击及少量定向合成 Pointer Events。合成 pen 事件检查路由逻辑，不等同 Apple Pencil 硬件验证。
- WebKit 和 Firefox 均尝试启动，但本环境缺少相应可执行文件，**未执行**这两个引擎的测试。详情见 `evidence/zoom/environment.json`。
- 未连接真实 iPad，也没有替用户完成 Safari 原生手势、Apple Pencil、iOS Photos／Files 选择器验收。
- 本补丁为已通过上述自动化检查的候选版；真实 iPad 验收应在合并前完成。

## 如何复现

```powershell
npm test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
py tests/browser/run_browser_tests.py --inline --evidence test-results\zoom-inline
```

不加 `--inline` 时，测试程序自动启动本地 HTTP 服务。用户设备上推荐也运行 HTTP 模式，以补充本环境未完成的导航、文件路径加载检查。

## 40 项浏览器用例（每种配置各执行一次）

1. `test_01_layout_and_touch_targets`
2. `test_02_rotation_preserves_exact_pixels_and_aspect`
3. `test_03_browser_bar_height_changes_do_not_rebuild_bitmap`
4. `test_04_brush_and_exact_undo_redo`
5. `test_05_sparkle_leaves_paint_and_highlights`
6. `test_06_eraser_then_undo_restores_exact_pixels`
7. `test_07_bucket_self_drawn_closed_region`
8. `test_08_bucket_after_resize_hits_same_region`
9. `test_09_bucket_builtin_and_other_page_buttons`
10. `test_10_upload_after_scrolling_opens_native_filechooser`
11. `test_11_draw_after_rotation_maps_to_pointer`
12. `test_12_rapid_taps_and_dblclick_keep_scale_and_toolbar`
13. `test_13_multi_pointer_and_cancel_recovery`
14. `test_14_twenty_step_undo_limit`
15. `test_15_sticker_background_and_png_export`
16. `test_16_new_confirmation_does_not_clear_on_cancel`
17. `test_17_touch_gesture_handlers_scoped_away_from_upload`
18. `test_18_actual_touch_swipe_draws_without_scrolling`
19. `test_19_actual_toolbar_touch_scroll_keeps_header`
20. `test_20_after_eraser_templates_and_uploads_are_visible`
21. `test_21_zoom_buttons_and_fit_preserve_exact_pixels`
22. `test_22_actual_two_finger_pinch_changes_canvas_not_page`
23. `test_23_two_finger_pan_preserves_view_scale_and_art`
24. `test_24_pinch_rolls_back_unfinished_stroke_without_undo_entry`
25. `test_25_bucket_selected_pinch_does_not_fill`
26. `test_26_sticker_selected_pinch_does_not_stamp`
27. `test_27_horizontal_and_vertical_scroll_sliders_move_only_canvas`
28. `test_28_brush_after_zoom_and_scroll_hits_correct_artwork`
29. `test_29_sparkle_and_eraser_work_while_zoomed`
30. `test_30_self_drawn_bucket_fills_after_zoom_and_scroll`
31. `test_31_template_fill_after_zoom_does_not_leak_through_eye`
32. `test_32_uploaded_picture_fill_at_zoom_and_reupload`
33. `test_33_rotation_while_zoomed_preserves_pixels_and_zoom`
34. `test_34_save_exports_entire_picture_not_only_zoomed_view`
35. `test_35_zoomed_double_taps_do_not_zoom_the_page`
36. `test_36_pen_pointer_ignores_palm_touches`
37. `test_37_blur_during_gesture_recovers_without_marks`
38. `test_38_zoom_visual_layout_and_scroll_to_edges`
39. `test_39_trusted_finger_brush_hits_zoomed_scrolled_canvas`
40. `test_40_zoom_anchor_stays_under_the_finger_midpoint`

## 测试来源与设计参考

W3C Pointer Events：touch-action 与指针捕获规范；Playwright 官方 Emulation 文档。
代码以 `touch-action: none` 把画板上的手势交给应用处理，但不用 CSS transform 缩放整页。
所有生成的运行记录都针对本次候选代码，不是之前 iPad fix 1 的日志。
