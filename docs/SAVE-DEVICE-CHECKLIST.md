# Physical iPhone/iPad save acceptance

Do not merge until the iPhone on which Save failed has been checked.
Record device model, OS version, browser, and whether the URL is LAN HTTP or HTTPS.

1. Draw with at least two colors. Set a non-white paper background. Zoom in and pan.
2. Tap Save. A full-picture preview should appear immediately with a brief preparation state.
   Close must remain reachable in portrait and landscape, including small screens.
3. Download PNG. Check Safari's downloads and Files > Downloads, not only Photos.
   Open the file and verify the WHOLE drawing, background and resolution, with no UI borders.
4. Touch and hold the preview. Verify the native image menu and available save action.
   Try Open image too; it should open a separate tab and preserve the app tab.
5. Return to the app and confirm drawing, zoom, selected tool/color and Undo/Redo remain usable.
6. On a trusted HTTPS preview, tap Share / Save image. Verify the REAL native sheet,
   then try Save Image / Save to Files if offered. Confirm the file actually exists.
7. Cancel the share sheet. No unwanted download should occur and the artwork should be unchanged.
8. Save again after drawing another mark; the second PNG must contain the new mark.
9. Repeat on iPad to confirm its existing ability to save is preserved (now via the panel).
10. Cycle the seven menu languages, save in a non-English language, and rotate with the panel open.

On ordinary LAN HTTP the Share button should be disabled with an explanation;
that is the expected capability fallback, NOT an error in the drawing app.
Do not disable browser security. The app cannot directly grant Photos access.

Save artwork before reloading. This patch does not implement autosave.
