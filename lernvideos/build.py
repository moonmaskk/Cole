# -*- coding: utf-8 -*-
"""Baut ein Lernvideo: Frames (PIL) + deutsche TTS (piper) + ffmpeg -> MP4."""
import importlib, os, re, shutil, subprocess, sys, wave
from concurrent.futures import ProcessPoolExecutor

import vlib
from vlib import new_frame, caption, save

SCR = "/tmp/claude-0/-home-user-Cole/609d3ab8-18b2-50d3-bff9-52a6a29a3834/scratchpad"
VOICE = f"{SCR}/voice/de-thorsten-low.onnx"
VCFG = VOICE + ".json"
PAD = 0.42          # Sekunden Nachlauf pro Shot
MIN_D = 2.4
SR = 22050
_voice = None


# ------------------------------------------------------------------ TTS
def _get_voice():
    global _voice
    if _voice is None:
        from piper import PiperVoice
        _voice = PiperVoice.load(VOICE, config_path=VCFG)
    return _voice


def speak_text(t):
    """Untertitel -> sprechbarer Text."""
    t = t.replace("„", "").replace("“", "").replace("‚", "")
    t = t.replace("–", ",").replace("—", ",").replace("→", "ergibt")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def tts_job(args):
    idx, text, outdir = args
    path = f"{outdir}/{idx:04d}.wav"
    v = _get_voice()
    with wave.open(path, "wb") as wf:
        v.synthesize_wav(speak_text(text), wf)
    with wave.open(path, "rb") as wf:
        dur = wf.getnframes() / float(wf.getframerate())
    return idx, path, dur


# ------------------------------------------------------------------ Frames
_MOD = None


def _mod(name):
    global _MOD
    if _MOD is None:
        _MOD = importlib.import_module(name)
    return _MOD


def frame_job(args):
    idx, modname, outdir = args
    m = _mod(modname)
    text, fn = m.SHOTS[idx]
    img, d = new_frame(m.TH)
    fn(img, d)
    caption(img, d, m.TH, text)
    p = f"{outdir}/{idx:04d}.png"
    save(img, p)
    return idx, p


# ------------------------------------------------------------------ Hilfen
def srt_time(s):
    h = int(s // 3600); m = int(s % 3600 // 60); sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def cat_wavs(paths, durs, out):
    sil = {}
    with wave.open(out, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
        for p, dtot in zip(paths, durs):
            with wave.open(p, "rb") as w:
                o.writeframes(w.readframes(w.getnframes()))
                used = w.getnframes() / float(w.getframerate())
            gap = max(dtot - used, 0)
            n = int(gap * SR)
            if n:
                if n not in sil:
                    sil[n] = b"\x00\x00" * n
                o.writeframes(sil[n])


def build(modname, outname, title):
    work = f"{SCR}/{modname}"
    fr, au = f"{work}/frames", f"{work}/audio"
    for p in (fr, au):
        shutil.rmtree(p, ignore_errors=True)
        os.makedirs(p, exist_ok=True)
    m = importlib.import_module(modname)
    n = len(m.SHOTS)
    print(f"[{modname}] {n} Shots")

    with ProcessPoolExecutor() as ex:
        frames = dict(ex.map(frame_job, [(i, modname, fr) for i in range(n)], chunksize=2))
        print(f"[{modname}] Frames fertig")
        res = list(ex.map(tts_job, [(i, m.SHOTS[i][0], au) for i in range(n)], chunksize=2))
    res.sort()
    wavs = [r[1] for r in res]
    durs = [max(r[2] + PAD, MIN_D) for r in res]
    total = sum(durs)
    print(f"[{modname}] Audio fertig, Laufzeit {total/60:.2f} min")

    cat_wavs(wavs, durs, f"{work}/narration.wav")
    with open(f"{work}/concat.txt", "w") as f:
        for i in range(n):
            f.write(f"file '{frames[i]}'\nduration {durs[i]:.3f}\n")
        f.write(f"file '{frames[n-1]}'\n")
    t = 0.0
    with open(f"{work}/subs.srt", "w", encoding="utf-8") as f:
        for i in range(n):
            f.write(f"{i+1}\n{srt_time(t)} --> {srt_time(t+durs[i]-0.08)}\n"
                    f"{m.SHOTS[i][0]}\n\n")
            t += durs[i]

    out = os.path.abspath(outname)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", f"{work}/concat.txt",
           "-i", f"{work}/narration.wav", "-i", f"{work}/subs.srt",
           "-map", "0:v", "-map", "1:a", "-map", "2:s",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-r", "30", "-vf", "fade=in:0:15",
           "-c:a", "aac", "-b:a", "128k", "-c:s", "mov_text",
           "-metadata:s:s:0", "language=deu", "-metadata:s:a:0", "language=deu",
           "-metadata", f"title={title}", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    shutil.copy(frames[0], out.rsplit(".", 1)[0] + "_vorschau.png")
    shutil.copy(f"{work}/subs.srt", out.rsplit(".", 1)[0] + ".srt")
    print(f"[{modname}] -> {out}")
    return out, total


if __name__ == "__main__":
    mod, outp, ttl = sys.argv[1], sys.argv[2], sys.argv[3]
    build(mod, outp, ttl)
