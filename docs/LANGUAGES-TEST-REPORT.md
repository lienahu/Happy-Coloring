# Happy Colors — Colorful L1: seven menu languages

## Delivered feature

One language picker, with English, Français, Português, Español, 简体中文, 日本語 and 한국어. The Apple Colorful design remains the only visual theme. Chinese is Simplified; Portuguese uses mainly European/neutral wording, with shorter compact-menu labels where needed.

The glossary contains **94 message keys for each of seven locales (658 strings)**. It covers controls, headings, picture and sticker names, brush sizes, zoom help, confirmations, and accessibility labels. Language names stay in their native scripts. Happy Colors branding and artwork are not translated.

A choice is remembered in browser localStorage when permitted. Failure or denial of storage is handled. The app starts in English when there is no valid saved preference. Switching does not reload the page. This feature does NOT add drawing autosave: save artwork before reloading.

## Base and scope

Built from the exact `happy-coloring-apple-colorful-tested.zip` accepted by the user, rather than an older experimental V4/V9 engine. That package was based on `main@7cbbeff631c9ae9b0e519cb824f6917c4a3afd17`. No remote branch, PR, main, or deployed site was modified during this work.

New runtime files: `i18n.js`, `languages.css`.
Updated runtime files: `index.html`, `mobile-ui.js`, and exactly one confirmation-message expression in `app.js`.
`canvas-zoom.js`, `style.css`, and `apple-colorful.css` are unchanged from the accepted package. The Node suite checks both the unchanged zoom engine hash and the app.js change boundary.

## Final results — actually executed

| Check | Result |
|---|---|
| Node unit tests | **151 passed, 0 failed** (95 existing + 56 new) |
| Final browser case/profile combinations | **234 run: 225 passed, 9 skipped, 0 failed/errors** |
| JavaScript syntax | All four runtime JavaScript files pass `node --check` |
| Patch application | `git apply --check` passes; applied files match the delivered files |
| Runtime freeze | The eight runtime-file SHA-256 hashes match those recorded before final tests began |

The 9 skips are touch-only cases in the desktop profile. Equivalent touch cases ran in the full tablet-landscape and phone-landscape suites.

### Browser profile coverage

| Profile | Viewport | Final cases |
|---|---|---:|
| Desktop | 1280 × 800 | 63 (9 touch-only skipped) |
| Tablet landscape | 1180 × 820 | 63 |
| Phone landscape | 851 × 393 | 63 |
| Phone portrait | 393 × 851 | 11 language cases |
| Small phone landscape | 667 × 375 | 11 language cases |
| Mini phone portrait | 320 × 568 | 11 language cases |
| Tablet portrait | 820 × 1180 | 11 language cases |
| Very small landscape | 568 × 320 | 1 all-languages layout case |

Each all-languages case cycles through all seven choices with real DOM controls. Case/profile counts do not inflate those loops into additional test counts.

### What the tests check

- Translation completeness, locale resolution, safe fallbacks, native option names and matching `lang` attributes.
- All seven choices update labels, titles, accessibility labels and selected state.
- Switching preserves raw canvas pixel hashes, bitmap dimensions, selected tool/color/size, background, zoom, scroll offsets, history and redo stacks.
- New and Clear questions translate correctly; cancelling preserves the drawing.
- Dynamic swatch names remain translated after tool/color selection; Large/Fit help remains translated.
- Dialog focus, Escape, selected check mark, inert background and return of focus.
- Long translated labels and all language options remain reachable on small screens.
- Preference helpers, simulated storage roundtrip, and storage-denied fallback.
- Existing Brush, Sparkle, Eraser, Fill on self-drawn/template/uploaded images, Upload, Undo/Redo, stickers, backgrounds, pinch/pan, rotation and complete PNG export.
- No theme-switching UI is reintroduced.

## Defect found and fixed during this work

Two preliminary failures (desktop and tablet-landscape `test_62`) detected a **1-pixel pan shift** when moving from Latin text to Chinese/Japanese. The hint's automatic line box changed from 15px to 16px with a fallback font. That altered the viewport and its zoom anchor.

The fix sets the hint line height explicitly to 18px; it does not change the drawing or zoom algorithm. The full final desktop and tablet suites reran and passed, including the exact state equality assertion. The initial failures remain under `evidence/languages/regression-desktop` and `regression-tablet`; final results are under `final-*`.

The picker was also adjusted so short landscape screens scroll the choice list while keeping the title/Close button visible. Compact labels avoid awkwardly splitting long French/Portuguese words.

## Test environment and limitations

Node.js 22.16.0, Python 3.13.5, Playwright 1.57.0, Chromium 144.0.7559.96 on Linux.

This environment blocks HTTP/HTTPS browser navigation with `ERR_BLOCKED_BY_ADMINISTRATOR`. Tests therefore inject the exact final local HTML, CSS and JavaScript into real Chromium. They exercise its DOM, layout, canvas and input pipeline, but **do not validate hosting, cache busting, external resource delivery, actual iOS, Safari/WebKit, physical Apple Pencil input or real system photo pickers**.

Browser storage on the injected origin is unavailable. Preference read/write behavior is covered by pure helper tests; the browser roundtrip test uses explicitly simulated storage seeded across app initializations. This is **not a claim that a real Safari reload/storage test was performed**. Please verify remembered language on the real preview origin on iPhone/iPad.

Translations were authored for this application and checked programmatically for coverage, not professionally reviewed by native speakers of every language. Native photo/file-picker UI and browser OK/Cancel labels remain controlled by the device/browser.

## Reproduce

```
npm test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
py tests/browser/run_language_tests.py
```

Default mode uses local HTTP on an ordinary computer. To reproduce this restricted environment:

```
py tests/browser/run_language_tests.py --inline --profiles desktop tablet_landscape phone_landscape
py tests/browser/run_language_tests.py --inline --only-languages --profiles phone_portrait phone_small_landscape phone_mini_portrait tablet_portrait
py tests/browser/run_language_tests.py --inline --profiles phone_tiny_landscape --tests test_67_all_languages_fit_controls_sidebar_and_picker
```

Current evidence: `evidence/languages/final-summary.json`, `final-unit.log`, `final-*/results.json`, `syntax.json`, `patch-check.json`, and `tested-runtime-sha256.json`.

Run `docs/LANGUAGES-DEVICE-CHECKLIST.md` before merging a new `menu-languages` branch. Keep previous stashes; no destructive Git cleanup is needed.
