"""Build edits/cartagena.json (the EDL) and edits/bed.wav (the music bed) from a shot list.

The shot list below IS the edit: every entry carries its source, in/out (seconds on the
normalized source) and a written reason. Chapter titles, music sections and on-screen text
are anchored to shots so reordering/trimming shots moves everything with them.

    uv run python edits/build_cartagena.py            # writes cartagena.json + bed.wav
    uv run video-agent edl edits/cartagena.json -o /dev/null --report --dry-run
    uv run video-agent edl edits/cartagena.json -o outputs/draft.mp4 --draft
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NORM = "inputs/norm"
FPS = 24
W, H = 1080, 1920
AMBIENT_LUFS = -28.0          # where the original sound sits under the music
XFADE = 4.0                   # seconds of overlap between songs

LOUD = json.load(open(os.path.join(HERE, "source_loudness.json")))

PHOTOS = {
    "sunset": "photo_dji_mimo_20260930_175700_20260930175700_1790816696764_photo",
    "sunset2": "photo_DJI_20260930_200508_Edit_Composited_Photo",
    "islandwater": "photo_DJI_20261002_083808_Edit_Composited_Photo",
    "dog": "photo_IMG_7422", "sea": "photo_IMG_7423",
    "plaza1": "photo_IMG_7440", "plaza2": "photo_IMG_7442",
    "wall1": "photo_IMG_7500", "wall2": "photo_IMG_7504",
    "bar1": "photo_IMG_7598", "bar2": "photo_IMG_7602", "bar3": "photo_IMG_7608",
}


def src_path(ref: str) -> str:
    kind, name = ref.split(":", 1)
    if kind == "d":      # DJI export: d:0930_200312
        return f"{NORM}/dji_export_2026{name}_0.f_compose_0.mp4"
    if kind == "i":      # iPhone: i:7398
        return f"{NORM}/IMG_{name}.mp4"
    if kind == "p":      # photo clip
        return f"{NORM}/{PHOTOS[name]}.mp4"
    return f"{NORM}/{name}.mp4"     # o:<file stem>


SHOTS: list[dict] = []
CHAPTERS: list[dict] = []
TEXTS: list[dict] = []


def chapter(key, song, song_start, title=None, sub=None):
    CHAPTERS.append(dict(key=key, song=song, song_start=song_start, first=len(SHOTS)))
    if title:
        TEXTS.append(dict(at=len(SHOTS), off=0.8, dur=4.2, kind="chapter", text=title, sub=sub))


def shot(ref, a, b, why, **kw):
    SHOTS.append(dict(ref=ref, a=a, b=b, why=why, **kw))
    return len(SHOTS) - 1


def text(kind, txt, sub=None, off=0.8, dur=3.5, **kw):
    TEXTS.append(dict(at=len(SHOTS) - 1, off=off, dur=dur, kind=kind, text=txt, sub=sub, **kw))


def photo(name, dur, why, **kw):
    kw.setdefault("fit", "blur")
    kw.setdefault("punch", [1.0, 1.06])
    return shot(f"p:{name}", 0.5, 0.5 + dur, why, photo=True, **kw)


# ---------------------------------------------------------------- PROLOGUE
chapter("prologue", "one_dance", 0.0)
shot("d:0930_200312", 28.0, 38.0, "Opening image: calm pink sunset over the water, longest shot so the piece starts slow",
     amb=-34)
text("title", "CARTAGENA", "30 SEP – 4 OCT · 2026", off=1.2, dur=6.0)
shot("d:1001_185654", 175.5, 180.0, "Teaser: the fish — the highlight of the trip, shown for a beat")
shot("d:1002_090317", 2.0, 6.5, "Teaser: boat wake past the mangroves, motion and sea")
shot("d:0930_212101", 61.0, 65.5, "Teaser: colonial street with flags, the city", vout=0.7)

# ---------------------------------------------------------------- DÍA 1 — LLEGADA
chapter("llegada", "one_dance", 0.0, "Llegada", "30 de septiembre")
shot("d:0930_211042", 0.0, 5.5, "Pool from the water: arrival, settling in", vin=0.7)
shot("d:0930_211042", 16.0, 21.5, "Friend swimming in the pool, personality beat")
shot("d:0930_211400", 10.0, 16.0, "Walking a colourful street, first look at the old town")
shot("d:0930_211400", 43.0, 49.0, "Same walk, different street — keeps the exploring feel")
shot("d:0930_211400", 65.0, 71.0, "Yellow taxi and corner, end of the walk")
shot("d:0930_211649", 10.0, 15.0, "Supermarket run, friends reacting to prices")
shot("d:0930_211649", 30.0, 36.0, "Fridge aisle, wide fisheye texture")
shot("d:0930_211649", 82.0, 87.5, "Face to camera with sunglasses")
shot("d:0930_211649", 98.0, 103.0, "Second face beat closes the supermarket scene")
shot("d:0930_212101", 23.0, 29.0, "Walking behind the group down the street")
shot("d:0930_212101", 63.0, 69.0, "Yellow colonial buildings with balconies")
shot("d:0930_212101", 108.0, 114.0, "Yellow cab crossing, city life")
shot("d:0930_212101", 143.0, 149.0, "Red brick sidewalk, corner shop")
shot("d:0930_212101", 183.0, 189.0, "End of the street walk on red brick", vout=0.6)
shot("d:0930_195948", 3.0, 9.0, "Beach at dusk: tonal shift from city to sea", vin=0.7)
photo("sunset", 4.0, "Still of the pink sunset breaks the video rhythm, quiet beat", fit="cover")
shot("d:0930_200105", 13.0, 19.0, "Waves and skyline under the pink sky")
shot("d:0930_200312", 43.0, 50.0, "Wide pink sky and the red house, held longer")
shot("d:0930_200312", 58.0, 64.0, "Same sunset, lower: the colour deepens")
shot("d:0930_200714", 4.5, 7.5, "Friend washing his hair: small human moment")
shot("d:0930_202429", 3.0, 8.0, "Selfie in the water at dusk")
shot("d:0930_205359", 28.0, 35.0, "Beach getting dark, last light of day one", vout=0.8)

# ---------------------------------------------------------------- DÍA 2 — ISLAS DEL ROSARIO
chapter("islas", "feels", 0.0, "Islas del Rosario", "1 de octubre")
shot("i:7398", 0.0, 5.5, "Dock in the morning: the day starts, boats waiting", vin=0.7)
shot("i:7399", 1.0, 6.0, "Shade at the dock, skyline behind")
shot("d:1002_090650", 0.0, 5.5, "Selfie on the boat with sunglasses")
shot("d:1002_090650", 8.5, 13.5, "Everyone on the boat, the group")
shot("d:1002_090133", 3.0, 9.0, "Bow of the boat, house on stilts passing")
shot("d:1002_090442", 3.0, 9.0, "Open sea, islands on the horizon")
shot("d:1002_090133", 28.0, 34.0, "Teal water along the hull")
shot("i:7410", 0.0, 6.0, "iPhone wide: wake and islands")
shot("d:1002_090442", 24.0, 30.0, "Islands getting closer")
shot("i:7411", 3.5, 9.5, "Approaching shore on the iPhone")
shot("i:7407", 0.0, 7.0, "Arrival walk on the boardwalk, 'Oceanario' sign")
shot("d:1002_083840", 2.0, 8.0, "Palapa shade over the beach, relaxed")
shot("d:1002_083948", 14.0, 21.0, "Friend with sunglasses waves from the chair")
photo("dog", 4.0, "Dog in the sand: the small charm of the island")
shot("i:7414", 0.0, 6.0, "People wading in the shallows")
shot("i:7417", 0.0, 5.5, "Beach view from under the palm roof")
shot("i:7419", 4.0, 9.5, "Quiet stretch of beach")
shot("d:1002_082428", 5.0, 11.0, "Faces in the water — the group having fun")
shot("d:1002_083115", 0.0, 6.0, "Snorkel mask selfie before going under")
shot("d:1002_083115", 34.0, 42.0, "Face to camera at the surface")
shot("d:1002_083623", 8.0, 14.0, "Floating with the resort in the background")
shot("d:1002_083715", 4.0, 10.0, "Water-level view of the sea, breath before the fish", vout=0.7)

chapter("peces", "passionfruit", 20.0)
shot("d:1001_185241", 12.0, 18.0, "Surface snorkelling with the group", vin=0.7, amb=-30)
text("tag", "Con los peces", None, off=0.8, dur=3.5)
shot("d:1001_185241", 27.0, 33.0, "Snorkeler under the surface", amb=-30)
shot("d:1002_084126", 21.0, 27.0, "Rocky bottom, first fish", amb=-32)
shot("d:1001_185654", 171.0, 177.0, "The fish start to gather", amb=-30)
shot("d:1001_185654", 178.0, 185.0, "Dozens of striped fish — the shot to hold", amb=-30)
shot("d:1001_185654", 187.0, 194.0, "Hands feeding them", amb=-30)
shot("d:1001_190320", 8.0, 12.0, "A fish nibbling the hand", amb=-30)
shot("d:1001_190320", 46.0, 53.0, "Legs and fish at the bottom", amb=-30)
shot("d:1002_084333", 3.0, 9.5, "Landscape clip (real orientation): coral — blur fill", fit="blur", amb=-32)
shot("d:1001_190320", 83.0, 90.0, "Fish up close", amb=-30)
shot("d:1001_190320", 93.0, 100.0, "Big striped fish at the lens", amb=-30)
shot("d:1001_191200", 14.0, 21.0, "School of yellow fish", amb=-30)
shot("d:1001_191347", 17.0, 24.0, "Snorkeler selfie with fish", amb=-30)
shot("d:1002_084515", 17.0, 24.0, "Landscape clip: reef wall — blur fill", fit="blur", amb=-32)
shot("d:1002_084702", 2.0, 9.0, "Colourful fish over the rocks", amb=-30)
shot("d:1001_190320", 132.0, 138.0, "Close fish, face level", amb=-30)
shot("d:1002_085359", 43.0, 50.0, "Reef and coral", amb=-32)
shot("d:1001_190320", 202.0, 209.0, "Fish eating from a hand", amb=-30)
shot("d:1001_190320", 256.0, 263.0, "Fish around a swimmer", amb=-30)
shot("d:1001_190320", 296.0, 302.0, "Boy with snorkel, fish passing", amb=-30)
shot("d:1001_190320", 310.0, 316.0, "Fish at the lens, close", amb=-30)
shot("d:1002_085958", 0.5, 9.5, "Landscape clip: surface with the stilt house and fish — calm exit, blur fill", fit="blur", amb=-30)
shot("d:1002_090751", 6.0, 18.0, "Heading back: city skyline from the boat", amb=-30)
shot("d:1002_090957", 3.0, 8.0, "Last look at the skyline", vout=0.9)

# ---------------------------------------------------------------- NOCHE
chapter("noche", "no_idea", 38.0, "Noches en la ciudad", "2 de octubre")
photo("plaza1", 4.5, "Old town building lit at night", vin=0.7)
photo("plaza2", 4.0, "Plaza at night with blue lights")
photo("wall1", 4.0, "City wall at night, leading lines")
photo("wall2", 4.0, "Wall and lawn, the quiet side of the night")
shot("i:7570", 0.5, 7.5, "Dancers in yellow in the plaza, street life", amb=-24)
photo("bar1", 3.5, "Bar: red light, a drink")
photo("bar2", 3.5, "Friends in the red light", fit="blur")
photo("bar3", 3.5, "Peace signs, the night out")
shot("o:DF7CF623-C32F-499F-A692-0FDB01D74684", 0.0, 9.7, "Short party clip in red light", amb=-34, vout=0.8)

# ---------------------------------------------------------------- ÚLTIMOS DÍAS
chapter("final", "lost", 0.0, "Últimos atardeceres", "3 y 4 de octubre")
shot("i:7631", 0.0, 6.5, "Driving along the coast, leaving the old town", vin=0.7)
shot("i:7637", 1.0, 6.5, "Rocks and a bird by the sea")
shot("i:7638", 0.0, 5.0, "Grey beach, calm")
shot("i:7641", 2.0, 8.5, "Seagulls at the water's edge")
shot("o:1791067611605", 2.0, 10.0, "Dusk on the beach, waves", amb=-34)
shot("o:1791068039802", 4.0, 12.0, "Tree on the breakwater, the last light", amb=-34)
shot("o:A001_10031749_C019", 14.0, 24.0, "Friends playing in the waves", amb=-34)
shot("o:1791067887927", 28.0, 36.0, "Swimmers at dusk", amb=-34)
shot("o:1791067887927", 50.0, 57.0, "Friends coming out of the sea", amb=-34)
shot("d:0930_200312", 58.0, 71.0, "Bookend: back to the pink sunset from the opening; longest shot, the ending breathes",
     amb=-34, vout=2.5)
text("closing", "Gracias, Cartagena", "y por muchos viajes más", off=1.5, dur=9.0)

SONGS = {
    "one_dance": "Drake - One Dance (Lyrics) ft. Wizkid & Kyla.mp3",
    "feels": "Calvin Harris - Feels ft. Pharrell Williams, Katy Perry, Big Sean.mp3",
    "passionfruit": "Drake - Passionfruit.mp3",
    "no_idea": "Don Toliver - No Idea (Lyrics).mp3",
    "lost": "Frank Ocean - Lost (Lyrics).mp3",
}


def q(t):
    return round(t * FPS) / FPS


def build():
    clips, starts = [], []
    t = 0.0
    for i, s in enumerate(SHOTS):
        dur = q(s["b"]) - q(s["a"])
        starts.append(t)
        t += dur
    total = t

    chap_start = [starts[c["first"]] for c in CHAPTERS]
    chap_end = chap_start[1:] + [total]
    chap_first = {c["first"] for c in CHAPTERS}
    chap_last = {c["first"] - 1 for c in CHAPTERS[1:]} | {len(SHOTS) - 1}

    for i, s in enumerate(SHOTS):
        path = src_path(s["ref"])
        c = {"src": path, "start": s["a"], "end": s["b"], "rationale": s["why"]}
        if s.get("fit"):
            c["fit"] = s["fit"]
        if s.get("punch"):
            c["punch"] = s["punch"]
        vin = s.get("vin", 0.0)
        vout = s.get("vout", 0.0)
        if vin:
            c["vfade_in"] = vin
        if vout:
            c["vfade_out"] = vout
        if not s.get("photo"):
            src_l = LOUD.get(os.path.basename(path))
            target = s.get("amb", AMBIENT_LUFS)
            if src_l is not None:
                c["gain_db"] = round(max(-40.0, min(10.0, target - src_l)), 1)
        clips.append(c)

    texts = []
    for tx in TEXTS:
        t0 = starts[tx["at"]] + tx["off"]
        base = dict(start=round(q(t0), 3), end=round(q(t0 + tx["dur"]), 3), fade=0.7)
        if tx["kind"] == "title":
            base.update(text=tx["text"], sub=tx["sub"], font="playfair", weight="Bold", size=150,
                        tracking=10, sub_font="montserrat", sub_weight="Medium", sub_size=40,
                        sub_tracking=8, align="center", y=0.31, line_gap=0.45)
        elif tx["kind"] == "chapter":
            base.update(text=tx["text"], sub=tx["sub"].upper(), font="playfair-italic",
                        weight="Medium", size=108, tracking=0, sub_font="montserrat",
                        sub_weight="SemiBold", sub_size=36, sub_tracking=7, align="left",
                        y=0.66, line_gap=0.4)
        elif tx["kind"] == "tag":
            base.update(text=tx["text"], font="playfair-italic", weight="Medium", size=84,
                        align="left", y=0.70)
        elif tx["kind"] == "closing":
            base.update(text=tx["text"], sub=tx["sub"], font="playfair-italic", weight="Medium",
                        size=104, sub_font="montserrat", sub_weight="Medium", sub_size=40,
                        sub_tracking=4, align="center", y=0.40, line_gap=0.5, fade=1.2)
        texts.append(base)

    edl = {"fps": FPS, "width": W, "height": H, "seam_fade": 0.02,
           "crf": 15, "preset": "slow", "maxrate": "24M", "bufsize": "48M",
           "music": {"src": "edits/bed.wav", "gain_db": 0.0, "duck": False,
                     "fade_in": 0.0, "fade_out": 3.0},
           "texts": texts, "clips": clips}
    json.dump(edl, open(os.path.join(HERE, "cartagena.json"), "w"), indent=1, ensure_ascii=False)
    return total, chap_start, chap_end


def build_bed(chap_start, chap_end):
    """Concatenate one song section per chapter with XFADE-second crossfades."""
    norm_dir = os.path.join(ROOT, "inputs", "music_norm")
    os.makedirs(norm_dir, exist_ok=True)
    segs = []
    for k, c in enumerate(CHAPTERS):
        song = os.path.join(ROOT, "inputs", "musica", SONGS[c["song"]])
        nrm = os.path.join(norm_dir, c["song"] + ".wav")
        if not os.path.exists(nrm):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", song, "-af",
                            "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2", nrm],
                           check=True)
        length = chap_end[k] - chap_start[k]
        last = k == len(CHAPTERS) - 1
        segs.append((nrm, c["song_start"], length + (0 if last else XFADE)))

    # Merge consecutive chapters that share a song into one continuous section.
    merged = []
    for k, (nrm, st, ln) in enumerate(segs):
        if merged and CHAPTERS[k]["song"] == CHAPTERS[k - 1]["song"] and \
                CHAPTERS[k]["song_start"] == CHAPTERS[k - 1]["song_start"]:
            p = merged[-1]
            merged[-1] = (p[0], p[1], p[2] - (XFADE if k - 1 < len(CHAPTERS) - 1 else 0) + ln)
        else:
            merged.append((nrm, st, ln))

    inputs, parts = [], []
    for j, (nrm, st, ln) in enumerate(merged):
        inputs += ["-i", nrm]
        parts.append(f"[{j}:a]atrim={st:.3f}:{st + ln:.3f},asetpts=PTS-STARTPTS[s{j}]")
    cur = "s0"
    for j in range(1, len(merged)):
        parts.append(f"[{cur}][s{j}]acrossfade=d={XFADE}:c1=tri:c2=tri[x{j}]")
        cur = f"x{j}"
    out = os.path.join(HERE, "bed.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex",
                    ";".join(parts), "-map", f"[{cur}]", "-ar", "48000", out], check=True)
    return merged


if __name__ == "__main__":
    os.chdir(ROOT)
    total, cs, ce = build()
    merged = build_bed(cs, ce)
    print(f"{len(SHOTS)} shots, {total:.1f}s ({total / 60:.1f} min)")
    for c, a, b in zip(CHAPTERS, cs, ce):
        print(f"  {c['key']:<10} {a:7.1f} -> {b:7.1f}  ({b - a:5.1f}s)  song={c['song']}")
    print("bed sections:", [(os.path.basename(m[0]), m[1], round(m[2], 1)) for m in merged])
    sys.exit(0)
