# OSINT-1 — "Pentimento" — Solution

## Flag

```
zdk{52e38f85819f184cd265679fddc30349d71d82fb46144b4f6a798668fb840803}
```

---

## 1. Identifying the source medium

`lead.png` is 300×288 px, RGB, with no metadata (only `IHDR`/`IDAT`/`IEND`). Every
pixel run is exactly 6 px wide and 6 px tall, so the true image is **50×48 logical
pixels** upscaled 6×.

It uses exactly 21 distinct colours, and all 21 are members of the **r/place 2022
32-colour palette** (`#ff4500`, `#51e9f4`, `#ffd635`, `#3690ea`, `#811e9f`,
`#7eed56`, `#b44ac0`, `#00a368`, `#6d482f`, …). Combined with the given date
(2022-04-03, mid-event), the source is the **r/place 2022 canvas**.

Visible content: the 東方 (Touhou) kanji banner, a Yin-Yang orb, a vertical "ZUN",
Nitori Kawashiro, a large white silhouette, and a "⑨"-style purple/cyan tile.

## 2. Recovering the coordinates

Ground truth used: the **Place Atlas Initiative** repository
(`github.com/placeAtlas/atlas`), which ships both `web/atlas.json` and the full
set of 166 half-hourly canvas snapshots under `web/_img/canvas/place30/`.

Snapshots are stored as a base plate plus a transparent diff layer, composited
per `web/_js/main/time.js`. I rebuilt all 166 frames and ran an exhaustive
50×48 sliding-window comparison over each full 2000×2000 canvas.

Result — the crop's top-left lands at the **same position in every frame**, and the
match is decisively unique:

| period | UTC | best mismatch | position |
|---|---|---|---|
| 105 | 2022-04-03 18:00 | 74 px | (478, 508) |
| 106 | 2022-04-03 18:30 | 62 px | (478, 508) |
| **107** | **2022-04-03 19:00** | **45 px** | **(478, 508)** |
| 108 | 2022-04-03 20:00 | 81 px | (478, 508) |

Global uniqueness check at period 107 (all 1951×1953 candidate offsets):
best = 45 px at (478, 508); runner-up = 1164 px. A ~26× gap — unambiguous.

```
origin = 478,508
```

### Why a non-zero residual is expected (and confirms the timestamp)

2022-04-03 18:46:22 UTC falls **between** the 18:30 and 19:00 snapshots, so `lead.png`
cannot match either exactly. Verifying it behaves like a genuine intermediate state
of a 2304-pixel crop:

- differs from 18:30 in 62 px, from 19:00 in 45 px (18:30→19:00 itself differs in 87 px)
- matches **both** in 2304 px
- matches 18:30-only in 34 px (not yet changed), 19:00-only in 51 px (already changed)
- only **11 px** differ from both — transient pixels placed and overwritten inside the
  30-minute window

That monotone "partway between the two bracketing snapshots" profile is exactly the
signature of a live frame at 18:46:22.

## 3. What was actually in the frame

The large white silhouette centred at roughly (491–510, 528–554) is the
**Bad Apple!! PV [Shadow]** artwork — the Reimu Hakurei silhouette holding an apple
from the opening of the shadow-art PV.

Atlas entry `txatim`, "Bad Apple!! PV [Shadow]", confirms it, and its description
states the art *"originally took the form of a silhouette of the character Hakurei
Reimu holding an apple shown at the very beginning of the music video, but changed
to an apple core after the concession of territory to a Peruvian streamer."*

This is the "painted over" pentimento, and it is why **later states must not be used**:
from period 158 onward the art is redrawn as a bare apple core, and after the final
whiteout the region is blank. Only the 18:46 frame still shows the Reimu silhouette.

## 4. Tracing back to "something older"

The r/place tile is a reproduction of a Niconico video, which itself was built from
an older Niconico video:

- **record** — 【東方】Bad Apple!! ＰＶ【影絵】 by あにら, posted 2009-10-27.
  Its own source ID: **`sm8628149`** (the exact URL cited by Atlas entry `txatim`).
- **root** — 【ＵＰ主が見たい】Bad Apple!! ＰＶ【誰か描いてくれ】 by Μμ, posted
  2008-06-08. The stick-figure storyboard the shadow PV was drawn from.
  Its own source ID: **`nm3601701`**.

The shadow PV's own description opens with 「例の元ネタ様(nm3601701)を影絵風にして
みました」 — "I made the well-known original (nm3601701) into a shadow-play style" —
so the root is stated by the record itself.

Note the ID prefixes differ (`sm` vs `nm`) and are part of how each source writes its
own identifier, so both are reproduced verbatim, with no URL and no extra prefix.
`record` and `root` are correctly distinct, as the accession requires.

## 5. Building the ledger

The two time fields refer to different facts:

- `<x>,<y>` → crop origin `478,508`
- `<timestamp>` → completion/publication time of the `record`. Niconico reports
  `sm8628149` as uploaded at `2009-10-27 03:13:22 JST`, which is
  `2009-10-26 18:13:22 UTC`; truncating to the required whole minute gives
  `2009-10-26t18:13:00z`.
- `<record>` → `sm8628149`
- `<root>` → `nm3601701`
- `<n>` → whole seconds since epoch for the crop’s source frame, i.e. the given
  2022-04-03 18:46:22 UTC → `1649011582`

Exact bytes hashed (LF after every line, including the last):

```
pentimento/witness/v1
origin=478,508
completed_utc=2009-10-26t18:13:00z
record=sm8628149
root=nm3601701
snapshot_unix=1649011582
```

```python
import hashlib
ledger = (
    "pentimento/witness/v1\n"
    "origin=478,508\n"
    "completed_utc=2009-10-26t18:13:00z\n"
    "record=sm8628149\n"
    "root=nm3601701\n"
    "snapshot_unix=1649011582\n"
)
print("zdk{%s}" % hashlib.sha256(ledger.encode()).hexdigest())
```

```
zdk{52e38f85819f184cd265679fddc30349d71d82fb46144b4f6a798668fb840803}
```

## Integrity

`SHA256SUMS` verified for both handout files:

- `lead.png` → `d2cc57c3…81f688` ✓
- `accession.txt` → `89dc5357…b28096` ✓ (the local `accession (1).txt` hashes to the
  listed `accession.txt` value, so the rename did not alter content)

## Notes on constraints

- Later states were not relied upon — they diverge by design (apple core redesign,
  then whiteout). All positional work used the 18:00–20:00 window, and the identification
  is anchored on the 18:30/19:00 bracket.
- No one involved was contacted. Everything came from archived public artifacts: the
  Place Atlas repository (canvas snapshots + `atlas.json`), the Place Atlas wiki, and
  public Niconico video metadata.

## Reproducing

```bash
git clone --depth 1 https://github.com/placeAtlas/atlas.git
python3 -c "
from PIL import Image; import numpy as np
base=Image.open('atlas/web/_img/canvas/place30/104.png').convert('RGBA')
base.alpha_composite(Image.open('atlas/web/_img/canvas/place30/107_104.png').convert('RGBA'))
a=np.array(base.convert('RGB'))
lead=np.array(Image.open('lead.png').convert('RGB'))[::6,::6]
print('mismatch at (478,508):', (a[508:556,478:528]!=lead).any(axis=2).sum(), '/ 2400')
"
```

## Artifacts

- `solution_location.png` — period-107 canvas around (478, 508); magenta box is the
  crop footprint, green box is the Bad Apple!! Reimu silhouette.
