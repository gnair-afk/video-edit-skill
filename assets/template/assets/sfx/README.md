# Sound effects

Six sound effects (whoosh-short, pop, sparkle, click, click-soft, impact-bass-1) are generated with ElevenLabs by
`scripts/elevenlabs.py sfx-pack` (about 1,200 credits, once) and cached in the audio library. `scripts/setup.py`
copies cached ones here on every run without spending credits. Generated files are not committed.

To swap in your own, drop an `.mp3` here with the same name, or generate one:
`PY scripts/elevenlabs.py sfx "<prompt>" --seconds 0.6 --name <name> --out assets/template/assets/sfx/<name>.mp3`
