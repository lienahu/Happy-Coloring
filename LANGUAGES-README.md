# Happy Colors — Colorful L1 / Seven menu languages

Based on the exact `happy-coloring-apple-colorful-tested.zip` accepted by the user on iPhone and iPad. This is not a reconstruction from an older V4/V9 package. The original package was based on `main@7cbbeff631c9ae9b0e519cb824f6917c4a3afd17`; this deliverable does not assume the remote branch is unchanged or modify GitHub.

## Operation

- iPhone portrait: globe button in the bottom quick-access bar.
- iPhone landscape: globe button in the left quick-access rail.
- Desktop and normal-width iPad: globe button in the top toolbar.
- Narrow iPad split view uses the compact/mobile layout.
- Languages: English, Français, Português, Español, 简体中文, 日本語, 한국어.
- Default is English. A manually chosen preference is stored under `happy-colors.language` when browser storage permits. No automatic switch based on the device language.
- Chinese is Simplified. Portuguese uses European/neutral vocabulary; a dedicated Brazilian variant is not included.
- The Apple Colorful appearance is still the single fixed design. There is no theme picker.

## What is translated

Tool and menu names, headings, colors' accessible names, picture and sticker names, brush sizes, quick-access controls, zoom help, accessibility labels, New confirmation and the Clear question. Branding (`Happy Colors`), the build identifier, drawn artwork and PNG file names are not translated. Native system photo/file dialogs and browser confirmation-button captions use the OS/browser language.

Switching is in-place: no page refresh, no redraw, no replacement of tool IDs or handlers, and no new Undo step. **Language persistence does not provide artwork autosave.** Save artwork before reloading.

## Runtime files — all eight belong together

```
index.html
style.css
apple-colorful.css
languages.css           # NEW: picker + translated-label layout
i18n.js                 # NEW: 94 messages × 7 languages + picker
app.js                  # ONLY the Clear confirmation message changed
canvas-zoom.js          # byte-for-byte unchanged
mobile-ui.js            # dynamic labels use the selected language
```

`i18n.js` has no network or API dependency. It exposes `HappyI18n.t(key)`, `setLanguage(code)` and `getLanguage()` for application code; pure helpers are exported for Node tests. Markup uses `data-i18n`, `data-i18n-aria` and `data-i18n-title`. Tool IDs and data attributes used by the drawing engine remain unchanged.

## Preview safely

Extract to a NEW directory, run `py -m http.server 8000 --bind 0.0.0.0`, then access the computer's LAN IP from the iPhone/iPad on the same trusted home network. No router port-forwarding is needed. Stop the local test server with Ctrl+C. Check the build identifier is **Colorful L1** (hidden on narrow phone layouts).

Do not merge before the device checklist passes. A suitable new branch name is `menu-languages`. Keep previous stashes untouched. This package includes `menu-languages.patch` relative to the accepted Apple Colorful package, **not necessarily the current remote main**. Use file replacement OR the patch, not both.

## Automated tests

```
npm test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
py tests/browser/run_language_tests.py
```

`--only-languages` runs just the new language-specific browser tests. Ordinary computers use local HTTP by default. `--inline` is a restricted-environment fallback that loads exact local source into Chromium; it does NOT validate hosting, caching, real iOS, or real localStorage persistence across navigation. See the current report under `docs/LANGUAGES-TEST-REPORT.md` and `evidence/languages/` for exactly what was run.

Earlier Colorful reports/evidence are retained as historical material; they are not results of this language release. The new manifest covers this delivery only; old manifests refer to previous packages.
