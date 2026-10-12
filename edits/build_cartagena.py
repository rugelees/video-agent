"""Build edits/cartagena.json (the EDL) and edits/bed.wav (the music bed) from a shot list.

The shot list below IS the edit: every entry carries its source, in-point, length in *beats*
and a written reason. Every cut lands on a beat of the song playing under it: each section
(one song) gets a steady beat grid fitted to the track (edits/beatgrid.py), shots are a whole
number of beats long, and the bed is trimmed so the section's downbeat sits exactly on the
section's first cut. Song changes are crossfades that finish on that cut.

    uv run python edits/build_cartagena.py            # writes cartagena.json + bed.wav
    uv run video-agent edl edits/cartagena.json -o /dev/null --report --dry-run
    uv run video-agent edl edits/cartagena.json -o outputs/x.mp4 --chunked --jobs 2
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import beatgrid  # noqa: E402
import video_agent as va  # noqa: E402

NORM = "inputs/norm"
FPS = 24
W, H = 1080, 1920
AMBIENT_LUFS = -28.0          # where the original sound sits under the music
XFADE = 4.0                   # seconds of crossfade between songs, ending on the cut

LOUD = json.load(open(os.path.join(HERE, "source_loudness.json")))

# Phone footage arrives washed-out next to the action-cam clips; these lift contrast/colour.
PHONE_GRADE = ("eq=contrast=1.12:saturation=1.35:gamma=0.92,"
               "curves=all='0/0 0.2/0.15 0.5/0.5 0.8/0.84 1/1'")
FLAT_GRADE = ("eq=contrast=1.2:saturation=1.55:gamma=0.92,"
              "curves=all='0/0 0.2/0.15 0.5/0.5 0.8/0.85 1/1'")


def src_path(ref: str) -> str:
    kind, name = ref.split(":", 1)
    if kind == "d":      # DJI export: d:0930_200312
        return f"{NORM}/dji_export_2026{name}_0.f_compose_0.mp4"
    if kind == "dv":     # DJI landscape clip re-cropped to a true 9:16 (normalize --vcrop)
        return f"{NORM}/dji_export_2026{name}_0.f_compose_0_v.mp4"
    if kind == "i":      # iPhone: i:7398
        return f"{NORM}/IMG_{name}.mp4"
    return f"{NORM}/{name}.mp4"     # o:<file stem>


SONGS = {
    "one_dance": ("Drake - One Dance (Lyrics) ft. Wizkid & Kyla.mp3", 104),
    "feels": ("Calvin Harris - Feels ft. Pharrell Williams, Katy Perry, Big Sean.mp3", 98),
    "passionfruit": ("Drake - Passionfruit.mp3", 112),
    "lost": ("Frank Ocean - Lost (Lyrics).mp3", 123),
}

SHOTS: list[dict] = []
SECTIONS: list[dict] = []
TEXTS: list[dict] = []


def section(song, song_from):
    """Start a new music section; `song_from` = earliest second of the song to start at."""
    SECTIONS.append(dict(song=song, song_from=song_from, first=len(SHOTS)))


def shot(ref, a, beats, why, **kw):
    SHOTS.append(dict(ref=ref, a=a, beats=beats, why=why, **kw))
    return len(SHOTS) - 1


def text(kind, txt, sub=None, off=0.8, dur=3.5, **kw):
    TEXTS.append(dict(at=len(SHOTS) - 1, off=off, dur=dur, kind=kind, text=txt, sub=sub, **kw))


# ================================================================ A · One Dance — arrival
section("one_dance", 0.0)
shot("d:0930_200312", 28.0, 16, "Opening image: calm pink sunset over the water, held for two bars so the piece starts slow",
     amb=-34, vin=0.7)
shot("d:1001_185654", 175.5, 4, "Teaser: the fish, the highlight of the trip, one bar")
shot("d:1002_090317", 2.0, 4, "Teaser: boat wake past the mangroves")
shot("d:0930_212101", 61.0, 4, "Teaser: colonial street with flags")
shot("d:0930_211042", 0.0, 8, "Pool from the water: arrival, settling in")
shot("d:0930_211042", 16.0, 8, "Friend swimming in the pool, personality beat")
shot("d:0930_211400", 10.0, 8, "Walking a colourful street, first look at the old town")
shot("d:0930_211400", 65.0, 4, "Yellow taxi and corner")
shot("d:0930_211649", 82.0, 4, "Face to camera with sunglasses")
shot("d:0930_212101", 63.0, 8, "Yellow colonial buildings with balconies")
shot("d:0930_212101", 108.0, 4, "Yellow cab crossing, city life")
shot("d:0930_195948", 3.0, 8, "Beach at dusk: tonal shift from city to sea")
shot("d:0930_200105", 13.0, 8, "Waves and skyline under the pink sky")
shot("d:0930_200714", 4.5, 4, "Friend washing his hair: small human moment")

# ================================================================ B · Feels — the islands
section("feels", 4.0)
shot("i:7398", 0.0, 8, "Dock in the morning: the day starts, boats waiting", vin=0.5)
shot("d:1002_090650", 0.0, 8, "Selfie on the boat with sunglasses")
shot("d:1002_090133", 3.0, 8, "Bow of the boat, house on stilts passing")
shot("i:7410", 0.0, 8, "iPhone wide: wake and islands")
shot("d:1002_090442", 3.0, 8, "Open sea, islands on the horizon")
shot("i:7411", 3.5, 4, "Approaching shore")
shot("i:7407", 0.0, 8, "Arrival walk on the boardwalk")
shot("d:1002_083840", 2.0, 8, "Palapa shade over the beach, relaxed")
shot("i:7414", 0.0, 8, "People wading in the shallows")
shot("i:7417", 0.0, 4, "Beach view from under the palm roof")
shot("d:1002_082428", 5.0, 4, "Faces in the water, the group having fun")
shot("d:1002_083115", 0.0, 8, "Snorkel mask selfie before going under")
shot("d:1002_083715", 4.0, 8, "Water-level view of the sea, breath before the fish", vout=0.5)

# ================================================================ C · Passionfruit — the fish
section("passionfruit", 20.0)
shot("d:1001_185241", 12.0, 8, "Surface snorkelling with the group", vin=0.5, amb=-30)
shot("d:1002_084126", 21.0, 8, "Rocky bottom, first fish", amb=-32)
shot("d:1001_185654", 171.0, 8, "The fish start to gather", amb=-30)
shot("d:1001_185654", 178.0, 16, "Dozens of striped fish: the shot to hold", amb=-30)
shot("d:1001_185654", 187.0, 8, "Hands feeding them", amb=-30)
shot("d:1001_190320", 8.0, 4, "A fish nibbling the hand", amb=-30)
shot("d:1001_190320", 46.0, 8, "Legs and fish at the bottom", amb=-30)
shot("dv:1002_084333", 3.0, 8, "Landscape original re-cropped to 9:16: coral heads", amb=-32)
shot("d:1001_190320", 83.0, 8, "Fish up close", amb=-30)
shot("d:1001_190320", 93.0, 8, "Big striped fish at the lens", amb=-30)
shot("d:1001_191200", 14.0, 8, "School of yellow fish", amb=-30)
shot("d:1001_191347", 17.0, 8, "Snorkeler selfie with fish", amb=-30)
shot("d:1002_084702", 2.0, 8, "Colourful fish over the rocks", amb=-30)
shot("d:1002_084833", 2.0, 4, "Parrotfish and small fish over the rocks", amb=-30)
shot("d:1002_084948", 14.0, 8, "Cave full of yellow fish, light from above", amb=-30)
shot("d:1001_190320", 132.0, 4, "Close fish, face level", amb=-30)
shot("d:1002_085359", 43.0, 8, "Reef and coral", amb=-32)
shot("d:1001_190320", 202.0, 8, "Fish eating from a hand", amb=-30)
shot("d:1001_190320", 256.0, 4, "Fish around a swimmer", amb=-30)
shot("d:1001_190320", 342.0, 8, "Last big gathering of fish", amb=-30)
shot("d:1002_084833", 26.0, 4, "Big striped sergeant fish passes", amb=-30)
shot("dv:1002_084515", 11.0, 8, "Landscape original re-cropped to 9:16: legs over the seabed, then swimmers", amb=-32)
shot("dv:1002_085958", 0.5, 12, "Landscape original re-cropped to 9:16: surface, stilt house and fish, calm exit", amb=-30)
shot("d:1002_090751", 6.0, 12, "Heading back: city skyline from the boat", amb=-30, vout=0.6)

# ================================================================ D · Lost — night, dusk, goodbye
section("lost", 0.0)
shot("i:7631", 0.0, 8, "Driving through the city as the day ends", vin=0.5)
shot("i:7570", 0.5, 12, "Dancers in yellow in the plaza, street life at night", amb=-24)
shot("o:DF7CF623-C32F-499F-A692-0FDB01D74684", 0.0, 16, "Short party clip in red light, the night out", amb=-34)
shot("i:7637", 1.0, 8, "Rocks and a bird by the sea")
shot("i:7638", 0.0, 4, "Grey beach, calm")
shot("i:7641", 2.0, 8, "Seagulls at the water's edge")
shot("o:1791067540104", 1.0, 8, "Lifeguard hut on the sand: quiet establishing shot", amb=-34)
shot("o:1791068039802", 4.0, 8, "Tree on the breakwater, the last light", amb=-34)
shot("o:A001_10031749_C019", 14.0, 16, "Friends playing in the waves", amb=-34)
shot("o:1791119255902", 8.0, 8, "Friends in the surf in the blue hour", amb=-34)
shot("o:1791067887927", 28.0, 8, "Swimmers at dusk", amb=-34)
shot("o:1791067887927", 50.0, 8, "Friends coming out of the sea", amb=-34)
shot("o:1791119333104", 52.0, 8, "Two friends walking out of the waves", amb=-34)
shot("d:0930_200312", 58.0, 24, "Bookend: back to the pink sunset from the opening; the ending breathes",
     amb=-34, vout=2.5)
text("closing", "Gracias, Cartagena", "y por muchos viajes más", off=1.5, dur=9.0)


def q(t):
    return round(t * FPS) / FPS


def grade_for(path: str):
    name = os.path.basename(path)
    if name.startswith("IMG_"):
        return PHONE_GRADE
    if name.startswith(("A001", "1791", "1E79", "b94506")):
        return FLAT_GRADE
    return None


def song_path(key):
    return os.path.join(ROOT, "inputs", "musica", SONGS[key][0])


def plan():
    """Place every shot on the output timeline so each cut sits on a beat of its section's song."""
    grids = {}
    for sec in SECTIONS:
        key = sec["song"]
        nrm = os.path.join(ROOT, "inputs", "music_norm", key + ".wav")
        grids.setdefault(key, beatgrid.fit_grid(nrm, SONGS[key][1]))
    bounds = [s["first"] for s in SECTIONS] + [len(SHOTS)]
    t0 = 0.0
    for k, sec in enumerate(SECTIONS):
        g = grids[sec["song"]]
        p, down = g["period"], g["downbeat"]
        # First bar line at or after the requested start; later sections also need XFADE of
        # lead-in music before it.
        need = sec["song_from"] + (XFADE if k else 0.0)
        s0 = down + p * 4 * max(0, -(-(need - down) // (4 * p)))
        sec.update(t0=t0, s0=s0, period=p)
        beats = 0
        for i in range(bounds[k], bounds[k + 1]):
            SHOTS[i]["cut"] = q(t0 + beats * p)
            beats += SHOTS[i]["beats"]
        t0 = q(t0 + beats * p)
        sec["t_end"] = t0
    for i, s in enumerate(SHOTS):
        end = SHOTS[i + 1]["cut"] if i + 1 < len(SHOTS) else SECTIONS[-1]["t_end"]
        s["dur"] = round(end - s["cut"], 6)
        s["b"] = round(s["a"] + s["dur"], 6)
    return grids, t0


def check_sources():
    bad = []
    for s in SHOTS:
        d = va.video_info(src_path(s["ref"]))["duration"]
        if s["b"] > d + 0.01:
            bad.append(f'{s["ref"]}: needs {s["b"]:.2f}s, source is {d:.2f}s')
    if bad:
        raise SystemExit("shots run past their source:\n  " + "\n  ".join(bad))


def build(total):
    clips = []
    for s in SHOTS:
        path = src_path(s["ref"])
        c = {"src": path, "start": s["a"], "end": s["b"], "rationale": s["why"]}
        if s.get("vin"):
            c["vfade_in"] = s["vin"]
        if s.get("vout"):
            c["vfade_out"] = s["vout"]
        g = grade_for(path)
        if g:
            c["vfilter"] = g
        src_l = LOUD.get(os.path.basename(path))
        if src_l is not None:
            c["gain_db"] = round(max(-40.0, min(10.0, s.get("amb", AMBIENT_LUFS) - src_l)), 1)
        clips.append(c)

    texts = []
    for tx in TEXTS:
        t0 = SHOTS[tx["at"]]["cut"] + tx["off"]
        base = dict(start=round(q(t0), 3), end=round(q(t0 + tx["dur"]), 3), fade=0.7)
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


def build_bed():
    """One song section per music section; each crossfade completes exactly on the cut."""
    norm_dir = os.path.join(ROOT, "inputs", "music_norm")
    os.makedirs(norm_dir, exist_ok=True)
    inputs, parts = [], []
    for k, sec in enumerate(SECTIONS):
        nrm = os.path.join(norm_dir, sec["song"] + ".wav")
        if not os.path.exists(nrm):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", song_path(sec["song"]),
                            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2", nrm],
                           check=True)
        length = sec["t_end"] - sec["t0"]
        start = sec["s0"] - (XFADE if k else 0.0)
        stop = sec["s0"] + length
        inputs += ["-i", nrm]
        parts.append(f"[{k}:a]atrim={start:.4f}:{stop:.4f},asetpts=PTS-STARTPTS[s{k}]")
    cur = "s0"
    for k in range(1, len(SECTIONS)):
        parts.append(f"[{cur}][s{k}]acrossfade=d={XFADE}:c1=tri:c2=tri[x{k}]")
        cur = f"x{k}"
    out = os.path.join(HERE, "bed.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex",
                    ";".join(parts), "-map", f"[{cur}]", "-ar", "48000", out], check=True)


if __name__ == "__main__":
    os.chdir(ROOT)
    grids, total = plan()
    check_sources()
    build(total)
    build_bed()
    print(f"{len(SHOTS)} shots, {total:.1f}s ({total / 60:.2f} min)")
    for sec in SECTIONS:
        g = grids[sec["song"]]
        print(f"  {sec['song']:<13} out {sec['t0']:6.1f} -> {sec['t_end']:6.1f}  "
              f"song@{sec['s0']:.2f}s  {g['bpm']:.1f} bpm")
    sys.exit(0)
