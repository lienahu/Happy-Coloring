# Happy Colors — Colorful S1: Save panel

Built from the accepted **seven-language Colorful L1** package. This is a complete
preview folder, not a deployment and not an App Store build. Nothing was pushed to
GitHub or main. Preserve earlier Git stashes and test on a feature branch.

## New save flow

1. Tap the existing Save button. A panel displays the FULL artwork, with its paper
   background, not a screenshot of the visible zoomed area.
2. On a secure context supporting PNG file sharing, tap **Share / Save image**.
   Select Save Image / Save to Files if offered by the device. Available actions
   and the device's menu language are controlled by the operating system.
3. **Download PNG** remains available on all supported browsers. On iPhone/iPad,
   look in Files > Downloads; a download does not automatically enter Photos.
4. Alternatively, touch and hold the preview or use **Open image**. The latter
   opens a separate tab; it never replaces the drawing tab.

The web app cannot silently write to Apple's Photos library. No automatic claim
of a successful save is shown: a download is reported as requested, and native
sharing is reported as finished rather than guaranteed saved to Photos.

The prepared PNG is local. There is no upload, API call, account or server.
All new labels are translated into the same seven supported menu languages.
Apple Colorful remains the only visual style.

## Local preview vs. HTTPS

Native Web Share requires a secure context. An iPhone visiting a computer's
`http://192.168...:8000/` address normally has no native file-sharing API.
The panel deliberately disables Share there and explains the alternative.
**Download PNG, image preview and Open image do not require Web Share.**
A computer's localhost may be considered trustworthy, but that does not make its
plain-HTTP LAN address trustworthy to the iPhone. Do not enable insecure flags or
disable browser security to test sharing. Verify the native sheet on a trusted
HTTPS preview origin; actual permissions/capabilities are checked at runtime.

## Preview

Extract to a NEW folder, then:

```powershell
py -m http.server 8000 --bind 0.0.0.0
```

Use the same private LAN preview process as before. No router port forwarding.
Stop the server with Ctrl+C when finished. The desktop/tablet build tag reads
**Colorful S1**; compact phone layouts hide the tag to save space.

## Files

There are ten runtime files:

- `index.html`
- `style.css`
- `apple-colorful.css`
- `languages.css`
- `save-picture.css` (new)
- `i18n.js` (19 additional messages per language)
- `canvas-zoom.js`
- `app.js` (only its Save handler changed)
- `mobile-ui.js`
- `save-picture.js` (new)

The five unchanged runtime files are byte-identical to Colorful L1. The drawing,
fill, history and pinch algorithms were not rewritten. Older documents/evidence
in this folder describe earlier work; current evidence is under `evidence/save/`.

## Tests

```powershell
npm test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
py tests/browser/run_save_tests.py --save-only
```

The normal test runner uses a local HTTP server. `--inline` is only for reproducing
the restricted execution environment described in `docs/SAVE-TEST-REPORT.md`.
The native-share branches are explicitly mocked; this does not test iOS's share
sheet or prove that Photos accepted the file.

## Applying after acceptance

On a clean feature branch based on your accepted seven-language files, copy the
new package's runtime files together (especially the two new save files).
Keep the tests and docs as well. Do not copy into main or apply multiple old patches.
`iphone-save.patch` is an alternative to copying: it targets the exact L1 package,
not the older repository main. Use `git apply --check` before applying it.
Do not apply the patch after already copying the updated files.

No artwork autosave is added. Save pictures before reloading or closing the app.
