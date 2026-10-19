# Looks (exact values)

Bold, cool girl and cool dude live in `assets/template/build.py`; explainer (below) has its own reference build. Accent everywhere: butter yellow `#FAE67A`.
The user's default look is in `config.json` (`defaultLook`); a line in the script that names a look
("you can get the cool girl aesthetic like this") switches that section to it.

## Bold (default base look)
Kinetic lowercase words placed around the speaker, the big ones tucked BEHIND the head.
- Grade on footage layers (`.g` = base video + cutout): `contrast(1.07) saturate(.9) brightness(.97)`, plus a soft-light teal/warm tone, light vignette, and dark gradients top/bottom for legibility. Keep skin natural: darker versions push faces red.
- Type: Inter Tight, lowercase, `letter-spacing:-.05em`, `line-height:.9`, white with soft shadow `0 10px 40px rgba(0,0,0,.55)`.
  - `sm` 84px/800 lead-in lines, `sm2` 56px/800 for long lines, `md` 150px, `big` 236px, `xl` 220px, `huge` 300px (900 weight). Yellow `y` class for the punch word.
- Layout: lead-in lines CENTRED in front of the speaker over the chest band (y ~950-1300). Lines pinned to the left edge look off.
- Big punch words BEHIND the head (`back` class sits below the cutout layer). Only the bottom ~25-30% of the letters may be covered (formula in layout.md); a fully hidden middle ("cla_de") reads as broken.
- Motion: each word blur-pops in on its spoken frame (`scale 1.22 + blur 22px -> 1`, .2s power3.out); groups blur out (.12s) and are hard-killed with `tl.set`.
- Every cut gets a punch (`#stage` scale 1.05 -> 1 over .32s).

## Cool girl
- Grade: `sepia(.18) saturate(.9) contrast(.93) brightness(1.05) hue-rotate(-5deg)` + warm soft-light overlay + soft warm vignette.
- Type: small calm lowercase Inter 500 (64px) + one punch line in **Instrument Serif italic** in butter yellow (200px in the top band, 150px for lower blocks so 3 words fit one line). Cream text `#FFF8EF`.
- Accents: yellow sparkles (✦) twinkling near the italic, optional handwritten note in Caveat 600 with a drawn SVG arrow (strokeDashoffset).
- No date/time stamps: they read as clutter.
- Signature move: the creator's own reels orbit them (orbit() in the template). Each reel tile exists twice (back copy below the cutout, front copy above), positions precomputed as GSAP keyframes every 0.1s around an ellipse, autoAlpha swapping at the ring's left/right extremes. Tiles 190x338, cream border. Keep the ring inside the safe zone.

## Cool dude (editorial studio look)
Inspired by high-end studio interview edits: dark room, lit subject, tiny tracked caps and big serif words.
- Grade: room `contrast(1.1) saturate(.84) brightness(.8) hue-rotate(-4deg)`, the speaker cutout lifted: `contrast(1.06) saturate(.86) brightness(.98)` so they stay lit while the room falls back. Teal soft-light tone + vignette (.5) + bottom gradient. Dark is good; NO film grain (it reads as noise on faces).
- Type: tiny wide-tracked caps in **Montserrat 500** (34px, letter-spacing .32em, words can be spread across the width with flex space-between) + heavy lowercase punch words in **DM Serif Display** (210-270px, italic for the final word). Cream `#F7F4EE`.
- Motion: serif letters rise from a mask (`yPercent 115 -> 0`, stagger .028, expo.out) with a blur/scale settle; tracked words "track in" via `scaleX 1.45 -> 1` + blur (NOT letterSpacing, lint rejects it); quick .45s blur-to-focus into the section; slow push-ins (scale 1 -> 1.05 across a shot) instead of cut punches; one soft light sweep (screen blend) when the section opens.
- Shots: wide, then a ~1.9x close-up cropped from the 4K original (alternate wide/close like a studio interview).
- Tried and dropped: replacing the room with an AI-generated background (looked fake), black and white, crushed-dark grades, film grain.

## Explainer (split screen; first built for a Hinglish interior-design reel)
Calm, warm, "smart explainer" look: a cream card on top explains the idea while the speaker talks below.
- Split: cream panel `#F3EEE4` from y 0 to 880 (soft shadow on its edge), speaker video shifted down ~350px inside
  `#stage` so the head top sits at ~y 980. At the punch line, drop the panel and cut to a full-frame punch-in.
- Panel content (inside y 220-880): a 104px rounded-square icon in terracotta `#D2583C` with a white line glyph,
  a DM Serif Display title (128px, ink `#221C18`), a terracotta italic serif subtitle with an underline that draws
  (scaleX), white pill chips (Inter 600 44px, map-pin SVG) that pop in on their spoken word.
- Captions: white pill (`#fff`, Inter 600 50px, radius 99, soft shadow), centred on the seam (top 836) in the split,
  on the chest (top ~1340, below the chin) full frame. The key word sits on a butter marker `#F7E35C` that wipes in.
  Start every caption hidden (`gsap.set('.capw',{autoAlpha:0})`) or they all show at once.
- Punch line: one DM Serif Display word (230px, cream `#FFF8EE`) BEHIND the head with a terracotta `?`/accent.
- Sound: pops on chips, soft click on the underline, whoosh into the punch-in, a quiet bass hit on the punch word,
  ElevenLabs lo-fi piano bed at 0.10. Voice track at ~0.8 so peaks land around -2.5 dB.
- Reference build: `projects/test-01/build.py` in the user's studio folder.

## Beat (minimal, fun, fast; every cut on the beat)
Learned 2026-10-19 from four reference reels (files in the user's studio `references/ref1-4.mp4`, frames in
`references/_analysis/`): ref1 text animation + beat cuts, ref2 hook + captions + sound, ref3 image placement +
simpleness, ref4 motion graphics. It should feel like a tasteful indie edit, not a template: fast pace, calm screen.
Fonts: Clash Display 700 + Playfair Display (+italic) from `projects/flats-03/assets/fonts/` (fonts-extra.css),
Inter 600 for captions and word builds.

**Pace and the beat (priority 1)**
- Something changes on screen every 1-2 beats (0.5-1.2 s): a cut, a punch-in, an image swap, a slide change. The
  refs measured 1-4 beats per shot; nothing static for more than ~3 s except a talking stretch with moving captions.
- Every change lands ON a beat: cuts, image swaps, card in/out, slide whips, big words. Order of work: music first
  (prompt with an explicit bpm, 100-120, steady kick), then `PY SK/scripts/beatgrid.py <project> --bpm <n> --snap`
  moves the edl cuts inside real pauses onto the grid and picks the music start offset, then assemble, then
  `--check` (every cut within 1 frame). build.py reads `beats.json` for every graphic change and plays the bgm
  from `musicStart` (`data-media-start`).
- A speech cut that cannot reach the grid (`OFF`): keep it, and put a graphic hit on the nearest beat next to it so
  the eye reads the beat. Never cut into a word to force the beat.
- Strong beats (`strong` in beats.json) take the big moments: section changes, the hook's punch word, the CTA.
- Spoken words still pop on the spoken word (captions, word builds); transitions go on the beat.

**Hook (first 2-3 s, ref2 + ref3)**
- Frame 1 already says the topic: a stacked headline BEHIND the head (cutout), 3-4 short lowercase lines, left
  aligned at x 70, Clash Display 700 ~150px, line-height .9, cream `#F6F1E7`, soft shadow. Lines pop in word by word
  with the voice, then the whole stack drops away on a beat.
- Optional: a row of 3-4 small thumbnails (app logos or photos of what's coming, 150px, radius 18) under the face,
  each popping on a beat: a promise of the list to come.
- Alternative hook (ref3): b-roll on the top half and one bold claim in a black label (`#111`, white Inter 600
  40px, radius 10) on the seam, e.g. "koi bhi ye nahi kar raha".
- One white matte flash of the cutout (2 frames) on the first beat is allowed, once.

**Captions (ref3, ref2)**
- No pill. 1-3 words at a time, white Inter 600 lowercase 58px, `text-shadow 0 4px 18px rgba(0,0,0,.35)`,
  centred on the chest (top ~1180-1300, never on the face).
- The key word of a line grows: Clash Display 700 130px under the small words, the small line overlapping its top
  by ~15%. At most one big word per 2-3 s.
- On paper slides and full-frame graphics captions shrink to Inter 600 34px under the graphic (ref2's tiny
  captions), so the graphic stays the hero.
- Word in: `y 18 -> 0, blur 6 -> 0, autoAlpha 0 -> 1`, .14 s power3.out; groups hard-cut out (no fades).

**Text animation (ref1)**
- Word builds: on paper slides the sentence builds one word per spoken word, words SCATTERED over 3-5 rows (not one
  justified line), Inter 600 lowercase 54px in ink `#2A211B`, ONE word per phrase in Playfair Display italic at
  2.2x size (the feeling word). Accent version: the whole phrase in terracotta `#C9573A`.
- Over footage: the same build in white with a soft shadow, beside the head, never over it.
- Huge word behind the head (ref1 "TOO", "WON'T"): Clash Display 700 caps ~360px, white, on a strong beat, one per
  section, held 1-2 beats. Same readability formula as Bold (layout.md).
- Paper slide exit: whip left on a beat (`x 0 -> -1080`, .22 s power3.in, blur 10px) while the next shot whips in
  from the right, with a whoosh.
- Photo strips behind the italic word (ref1 "supposed"): 3-4 thin cropped photo strips, 520x110, stacked with small
  offsets, the italic word over them.

**Images (ref3, simpleness)**
ONE of these per moment, never two at once. While listing, images swap on beats (every 1-2 beats).
- Top half: the photo fills x 0-1080, y 0-900 with a hard edge, no border, no radius; the speaker is reframed into
  the lower half (edl `cy` / stage shift) so the head sits right under the seam. Captions stay on the chest.
- Floating objects: 1-3 product cutouts (background removed, PNG), 260-340px, on the wall ABOVE the head,
  `drop-shadow(0 18px 30px rgba(0,0,0,.25))`, pop in on a beat (scale .6 -> 1, back.out(2)), gone on the next cut.
- Paper card: full-frame paper `#F2EFEA` with one photo centred (760px wide, square corners, soft shadow), the
  caption small under it. For the "look at this" moment.
- Triptych: three photos side by side across the top half (360 each, no gaps), changing one at a time on beats.
- Real photos only (Pinterest, the user's own site photos, product shots). No AI images, no stock-looking 3D.

**Motion graphics (ref4)**
- Card mode for list items: the speaker video shrinks into a rounded card (`scale .78`, radius 48) on a sage
  `#8A977A` or paper background with a long soft shadow (`0 60px 80px rgba(40,30,20,.28)`). A Playfair Display title
  on top with the first letter of each word 1.5x bigger ("Series Navigator" style). Sage and paper alternate per
  list item. In/out on a beat with a quick settle (scale 1.06 -> 1, .3 s expo.out).
- Folder tabs: a stack of 3 rounded folders (charcoal `#3B3540`, lime `#C8CC5C`, maroon `#7A1F2B`) with small
  "number 1/2/3" tabs, fanned slightly; the next one slides up on each beat as a list counter.
- Sparkles: 2-3 eight-point stars (thin SVG, grey `#B9B4AC` on paper, white on footage), slow rotate (40 deg/s),
  drifting a few px. Never a sparkle cloud.
- Ghost word: the section's key word huge and blurred (`blur 6px`, 25% opacity) BEHIND a graphic.
- Notification card: frosted iOS banner (`backdrop-filter blur(18px)`, white 55%, radius 26, app icon + two lines)
  slides down to y 240, for news / updates.
- Scribble circle: a hand-drawn SVG loop (2-3 overlapping ellipses, cream stroke 3px) drawing around one Playfair
  italic word ("final result"), strokeDashoffset over .5 s.
- App logo tile above the head (Simple Icons, rounded square 220px) pops a beat early on the named app.
- Ransom title (once per reel at most): letters alternate Clash Display and Playfair italic at mixed sizes; a small
  cursor taps two letters and they swap font on beats.

**Sound (ref2)**
- BGM: upbeat warm indie-pop / lo-fi house, 100-120 bpm, steady kick and claps, bright keys, no vocals. The refs mix
  full and present (no silent gaps, peaks ~-1 dB). Music gain ~0.25-0.3, the voice still loudest.
- SFX only on the beat changes: whoosh on slide whips, soft pop on image / word pops, click on cursor taps, a light
  paper swish on paper slides, one bass hit on the hook's punch. Cached library sounds first.

**Learned on the first beat reel (beat-01, 2026-10-19)**
- Music models do not always play the bpm asked for (asked 110, got 122): beatgrid.py measures it; never trust the prompt.
- Never show the speaker looking away from the camera: scan eye close-ups every 0.5 s (then 0.2 s around suspects) and
  cover each look-away with a full-frame insert that starts on a beat (gradient word slide, photo split, moodboard grid).
- ElevenLabs music tracks fade out on their own ~3 s before the asked length: measure the RMS, then extend the bed
  by repeating a 16-beat stretch joined exactly on a beat (same phase), and fade only the last 1 s.
- End the reel with a 1 s held last frame (tpad clone on aroll + cutout): the renderer drops the final ~0.25 s of audio,
  and the last word must never be clipped.
- Keep the speaker on screen while the caption build is running over him; a slide that cuts in mid-line breaks the
  flow (the user preferred footage there even with a small glance away).
- Accent colour can come from the speaker's outfit (sample it from the footage): it ties the slides to the person.
- The user's own photos for list items go INSIDE the card (voice over), title above animating letter by letter, no
  captions there. Text over a busy room: cream type + a soft top shade, never ink.

**Anti AI-slop rules (priority 2)**
- One idea per screen. One accent colour per reel (terracotta OR sage family); the rest is paper, ink and white.
- Two type families (Clash Display + Playfair Display italic) plus Inter for captions. No gradient text, glow, neon,
  emoji, 3D icons, stock "tech" backgrounds, or a highlight on every word.
- Real photos and real logos only. Hand-made touches (scribble circles, scattered words, paper) over perfect
  symmetric templates.
- Motion arrives quickly and settles: no bouncing loops, constant wobble or shake. Things land on a beat and hold.
- Empty space is fine. More than 3 elements on top of the speaker at once: remove one.

## Fonts on hand (assets/template/assets/fonts, latin woff2 + fonts.css, SIL Open Font License)
Inter 500/600, Inter Tight 800/900, Instrument Serif italic, DM Serif Display (+italic), Montserrat 500/600, JetBrains Mono 500, Caveat 600.
Add more with the Google Fonts CSS2 API + a Chrome user agent, keep only the `/* latin */` blocks, `font-display:block`.

## Avoid (they looked worse every time)
Orange captions, Anton / condensed poster caps, black and white grades, @handle watermarks in the corner, date stamps.
