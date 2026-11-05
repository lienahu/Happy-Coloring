# Happy Colors — Colorful S1 Save update: test report

## Baseline and scope

Built from the exact `happy-coloring-seven-languages-tested.zip` supplied in this
conversation (Colorful L1), not from an assumed current repository main.
No GitHub branch, PR, main, deployment or user computer was modified.

The old Save handler composed the full PNG, created a detached anchor with a data
URL, and called `click()`. It offered no preview, alternative method, error state,
or explanation of Files vs Photos. The user reported that this worked on iPad but
not iPhone. **That exact device-specific failure was not reproduced on physical
hardware; this is a targeted robustness update, not a confirmed Safari root-cause diagnosis.**

New behavior: Save opens a modal preview. The app encodes the full artwork and
paper background into a PNG Blob. Native file sharing is checked by capability,
not by user-agent strings, and is launched by a separate real tap after encoding.
Explicit Download PNG and Open image links remain available. The image allows
native touch-and-hold. No network image upload or translation API is introduced.

Changed runtime files: `index.html`, `i18n.js`, and only the Save handler in
`app.js`. Added: `save-picture.js`, `save-picture.css`.

Byte-identical to L1: `canvas-zoom.js`, `mobile-ui.js`, `style.css`,
`apple-colorful.css`, `languages.css`. See `engine-integrity.json`.
The single fixed Apple Colorful style and all seven languages are retained;
19 new strings per locale cover the Save panel and its error/fallback states.

## Final executed results

| Check | Result |
|---|---|
| Node unit tests | **201 passed, 0 failed** (151 existing + 50 new) |
| Browser case/profile combinations | **338 run: 329 passed, 9 skipped, 0 failed/errors** |
| JavaScript syntax | All five runtime scripts pass `node --check` |
| Runtime freeze | Ten runtime SHA-256 hashes match the files used for final tests |
| Patch | Checked on the exact L1 package; applied source files match this build |

All 80 browser cases ran in desktop, tablet-landscape, phone-portrait and
phone-landscape configurations: 320 combinations. Six focused Save cases ran
additionally on mini-phone portrait (320 × 568), very small phone landscape
(568 × 320), and tablet portrait: 18 combinations.
The 9 skips are existing touch-only cases in the desktop configuration.
Language loops within one case are NOT counted as seven separate test cases.

## What was checked

- The actual Save button responds to mouse clicks and simulated touch taps.
- The preview and downloaded PNG use the full artwork bitmap, not the current
  zoomed viewport. Decoded PNG dimensions and colored pixels/background match.
- Real Chromium download events and downloaded bytes are inspected.
- With an **explicitly mocked** share API, the handler passes a real PNG File
  (not a blob URL/text link) with correct name, MIME, content and user activation.
- No sharing happens while encoding: only the second real user tap calls share.
- Cancelled, denied, synchronously throwing, unsupported, insecure and pending
  sharing scenarios preserve the preview and artwork; no forced download occurs.
- A pending native-share Promise cannot permanently lock Close or the download
  fallback, and late callbacks cannot overwrite a newer Save panel.
- Failed/delayed PNG encoding can be closed or retried without clearing artwork;
  a failed second export cannot expose the preceding picture as a stale download.
- The preview URL remains usable after closing; it is not immediately revoked.
- All seven languages fit the panel, including narrow/short screens. Close stays
  reachable, links remain at least 44px high, focus returns, and Escape works.
- The image is outside the app's canvas gesture blockers and its context-menu
  event is not cancelled. **The actual iOS long-press menu remains untested.**
- Previous Brush, Sparkle, Eraser, Fill, upload, same-file upload, history, stickers,
  background, rotation, pinch/pan, toolbar layout and language checks reran.

## Changes to test scripts and initial failures

The Save workflow intentionally gains a preview. Four previous export checks now
click Save, wait for the PNG, and click Download PNG. Their existing file-content,
resolution and background assertions remain intact; no assertion was removed to
hide a product failure.

The source-integrity test permits only the narrowly scoped Save handler change,
in addition to the previously allowed Clear-message translation.

An initial 34-case Save run had 4 test errors (2 cases × 2 phone profiles).
The fault-injection script returned an assigned function from `page.evaluate`,
which Playwright then invoked unintentionally: restoring `toBlob` caused an
Illegal invocation; assigning a deliberately throwing test double triggered it
before the app could handle it. Wrapping those assignments in void-returning
functions fixed the TEST SCRIPT. The final 338-case run passed. The initial logs
and failure screenshots are retained under `evidence/save/initial*`.

## Execution environment and limits

Node.js 22.16.0; Python 3.13.5; Playwright 1.57.0;
Chromium 144.0.7559.96 on Linux.

HTTP navigation to the container's local server was attempted and rejected with
`net::ERR_BLOCKED_BY_ADMINISTRATOR`. Browser tests therefore inject the exact local
HTML/CSS/JavaScript into a real Chromium page. These tests do **not** verify HTTP
resource delivery, site caching, GitHub Pages, the iOS operating system or Photos.

WebKit installation was attempted but failed due to DNS/download errors
(`EAI_AGAIN`); see `webkit-install-attempt.log`. No WebKit/Safari test is claimed.
No physical iPhone/iPad, native Apple share sheet, Photos permission flow, actual
long-press save menu or iOS file-picker destination was tested.

The native file-sharing scenarios use mocked `navigator.canShare`,
`navigator.share` and secure-context capability. These are logic/interaction tests,
NOT evidence that Apple's share sheet opened or wrote a photo on an iPhone.
Language storage roundtrip also retains the earlier explicitly simulated storage
mode used by this restricted origin.

## Real-device acceptance

Use `docs/SAVE-DEVICE-CHECKLIST.md` on the iPhone that exhibited the problem and
on the previously working iPad. A plain HTTP LAN preview can test PNG download,
preview and Open image but normally cannot test native Web Share. Use a trusted
HTTPS preview to verify the actual native share sheet; never disable browser
security. Confirm the actual saved file in Photos or Files, not just a UI message.
This patch does not add artwork autosave.

## Reproduce

```powershell
npm test
py -m pip install -r requirements-test.txt
py -m playwright install chromium
py tests/browser/run_save_tests.py --profiles desktop tablet_landscape phone_portrait phone_landscape
py tests/browser/run_save_tests.py --save-only
```

Default mode uses local HTTP on a normal computer. The current restricted
execution used `--inline`, with the profile sets in the final JSON reports.

## Technical references consulted

- WebKit, The User Activation API: https://webkit.org/blog/13862/the-user-activation-api/
- MDN, Navigator.share: https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share
- MDN, HTMLCanvasElement.toBlob: https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob
- Apple, Where to find downloads: https://support.apple.com/en-us/102440
