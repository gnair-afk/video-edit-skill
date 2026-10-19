# Extras for inserts (added 2026-10-19)

Used when making animated inserts (stat, chart, title, background) with the HeyGen `/motion-graphics` skill.

- `design-md/<brand>/DESIGN.md`: 84 real-brand style guides (colors, fonts, mood). Read one when asked for "make it look like <brand>". Use for mood and palette only; never imply the brand is involved. MIT.
- `taste-skill/`: Leonxlnx taste-skill (web design taste). Web-page oriented: borrow its art-direction and "review your own screenshots" habits for inserts, do not run its full website build. MIT.
- `shadergradient/ShaderGradient.tsx`: ruucm/shadergradient source, React + three.js, so it cannot be dropped into HyperFrames directly. Plan: port to plain JS driven frame by frame (seek-safe), or render one looping clip and use it as a background. MIT.
- HeyGen `motion-graphics` is installed globally (`~/.agents/skills`, linked into `~/.claude/skills`) with its helpers: hyperframes, hyperframes-core, hyperframes-creative, hyperframes-cli, hyperframes-registry, media-use, figma.
- Rule from the Remotion repo idea: never restate the voiceover as on-screen text.
