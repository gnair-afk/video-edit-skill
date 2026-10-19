# Extras for inserts (added 2026-10-19)

Used when making animated inserts (stat, chart, title, background) with the HeyGen `/motion-graphics` skill.

- `design-md/<brand>/DESIGN.md`: 84 real-brand style guides (colors, fonts, mood). Read one when asked for "make it look like <brand>". Use for mood and palette only; never imply the brand is involved. MIT.
- `taste-skill/`: Leonxlnx taste-skill (web design taste). Web-page oriented: borrow its art-direction and "review your own screenshots" habits for inserts, do not run its full website build. MIT.
- **ShaderGradient (ported, works):** `SK/assets/shadergradient/shadergradient-hf.js` is a plain-JS, seek-safe port of ruucm/shadergradient (MIT). Copy the folder into the project's `assets/`, add the three.js importmap (three@0.181.2 for both `three` and `three/addons/`), put a full-frame `<canvas id="sg">` under the content, and call `mountShaderGradient(canvas, { preset, color1..3, brightness, loop: <comp seconds> })`. All 10 presets (halo, pensive, mint, interstella, nightyNight, violaOrientalis, universe, sunset, mandarin, cottonCandy) or a `urlString` from shadergradient.co/customize. `loop` = seamless loop over that many seconds. Grain ('on') is the original halftone pass. Not ported: lightType 'env' (falls back to ambient). Tested 2026-10-19 in `projects/test-gradient-01` (explainer palette: '#D2583C', '#EBCFB2', '#E9B48A', brightness 1.15). Light colours with brightness above 1 blow out to white; keep brightness near 1.1 with a cream colour. Grain makes files big (about 17 MB for 5 s at high quality), and the phone copy compresses it.
- `shadergradient/ShaderGradient.tsx`: original React source, kept for reference.
- HeyGen `motion-graphics` is installed globally (`~/.agents/skills`, linked into `~/.claude/skills`) with its helpers: hyperframes, hyperframes-core, hyperframes-creative, hyperframes-cli, hyperframes-registry, media-use, figma.
- Rule from the Remotion repo idea: never restate the voiceover as on-screen text.

- **Windows gotcha:** never save composition HTML with PowerShell `Set-Content -Encoding utf8` (5.1 adds a BOM). HyperFrames turns the BOM into a blank line and shifts the whole frame down 18 px. Write files with the Write tool or `[IO.File]::WriteAllText(path, text, (New-Object Text.UTF8Encoding($false)))`.
