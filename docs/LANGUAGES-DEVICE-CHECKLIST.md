# Seven-language acceptance checklist / 七种语言真机验收

Use the new **Colorful L1** preview, not the already-tested Colorful 1 package.

1. iPhone portrait: tap the globe in the bottom quick-access bar. iPhone landscape: tap the globe in the left rail. iPad/desktop: tap the globe in the top toolbar. Narrow iPad split view uses the mobile layout.
2. Select English, Français, Português, Español, 简体中文, 日本語 and 한국어. Confirm labels, menus, tooltips, picture names and New/Clear messages change. Chinese is Simplified; Portuguese uses European/neutral wording.
3. Language names must remain readable in their native scripts even after changing to another language. Close and reopen the picker; the selected choice must have a check mark.
4. Before switching, draw a line and fill a small closed area. Zoom and pan. Switch through the seven languages. Drawing pixels, zoom, scroll position, selected tool/color, background and Undo/Redo must remain unchanged.
5. Continue drawing and filling after the switch. Check Brush, Sparkle, Eraser, Upload, stickers, Undo/Redo, Fit/Large, two-finger zoom and PNG saving.
6. Check long French/Portuguese/Spanish labels on a small phone. Open the tools drawer and scroll. Confirm that Upload and all tools can still be tapped.
7. In a short landscape window the language picker scrolls. Check all seven choices are reachable and it can be closed without touching the drawing.
8. In normal Safari, select a language and reload the preview. The menu language should persist on that browser/site. **Save the drawing first: this update does not add artwork autosave.** Different domains, ports or browser profiles may have separate preferences.
9. With storage blocked/private settings, switching should still work during the current session. Persistence may be unavailable.
10. VoiceOver/keyboard: names and announcements should follow the chosen menu language; the native language options retain their own `lang` tags. Escape closes the dialog on a keyboard, and focus returns to its opener.
11. Native photo/file pickers and the browser's OK/Cancel button labels are controlled by the OS/browser, not these in-app translations. The Clear question itself is translated.

本版没有增加账号、在线翻译 API 或风格切换功能。语言切换不会刷新页面，也不会自动保存画作。通过后再在 feature branch 提交；不要直接覆盖发布 main。
