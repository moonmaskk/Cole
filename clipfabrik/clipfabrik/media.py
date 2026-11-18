"""ffmpeg-Helfer: Aufnahme-Puffer, Ausschneiden, 9:16-Rendern, Untertitel."""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SEG_FMT = "%Y%m%d-%H%M%S"
NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0   # kein schwarzes Fenster unter Windows


def ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def run(args: list[str], cwd: Path | None = None, timeout: int = 900) -> None:
    p = subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", *args],
                       cwd=cwd, capture_output=True, text=True, timeout=timeout,
                       creationflags=NO_WINDOW)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or "ffmpeg-Fehler").strip()[-600:])


def segment_cmd(out_dir: Path, seg_s: int) -> list[str]:
    """ffmpeg liest den Stream von stdin und schreibt ihn ohne Neukodierung in kurze Segmente."""
    return [ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", "pipe:0",
            "-map", "0:v:0?", "-map", "0:a:0?", "-c", "copy",
            "-f", "segment", "-segment_time", str(seg_s), "-segment_format", "mpegts",
            "-reset_timestamps", "1", "-strftime", "1", str(out_dir / f"{SEG_FMT}.ts")]


def seg_time(p: Path) -> float | None:
    try:
        return datetime.strptime(p.stem, SEG_FMT).timestamp()
    except ValueError:
        return None


def segments(buf_dir: Path) -> list[tuple[float, Path]]:
    out = []
    for p in buf_dir.glob("*.ts"):
        t = seg_time(p)
        if t is not None:
            out.append((t, p))
    return sorted(out)


def prune(buf_dir: Path, keep_s: float) -> None:
    cutoff = time.time() - keep_s
    segs = segments(buf_dir)
    for t, p in segs[:-2]:          # die laufenden Segmente nie löschen
        if t < cutoff:
            p.unlink(missing_ok=True)


def cut(buf_dir: Path, start: float, end: float, out: Path) -> float:
    """Segmente zwischen start und end zusammenfügen. Gibt den Versatz von start im Ergebnis zurück."""
    segs = segments(buf_dir)
    chosen = []
    for i, (t, p) in enumerate(segs):
        t_next = segs[i + 1][0] if i + 1 < len(segs) else t + 3600
        if t < end and t_next > start:
            chosen.append((t, p))
    if not chosen:
        raise RuntimeError("Zeitraum nicht mehr im Puffer")
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for _, p in chosen), "utf-8")
    run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])
    lst.unlink(missing_ok=True)
    return max(0.0, start - chosen[0][0])


# ---------- Untertitel ----------

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial Black,92,&H00FFFFFF,&H0000E5FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,2,2,60,60,560,1
Style: Hook,Arial Black,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,1,0,0,0,100,100,0,0,3,18,0,8,70,70,150,1
Style: Src,Arial,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,2,40,40,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(s: float) -> str:
    s = max(0.0, s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def esc(t: str) -> str:
    t = "".join(ch for ch in t if ord(ch) < 0x2600).strip()   # Emojis kann libass nicht sicher zeichnen
    return t.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def build_ass(words: list[tuple[float, float, str]], duration: float, source: str, hook: str = "") -> str:
    lines = [ASS_HEAD]
    if hook:
        lines.append(f"Dialogue: 1,{ts(0)},{ts(min(3.0, duration))},Hook,,0,0,0,,{esc(hook)}\n")
    lines.append(f"Dialogue: 0,{ts(0)},{ts(duration)},Src,,0,0,0,,Quelle: {esc(source)}\n")
    # Wenige Wörter pro Zeile, das gerade gesprochene Wort gelb hervorgehoben
    for g in range(0, len(words), 3):
        group = words[g:g + 3]
        for i, (ws, we, _) in enumerate(group):
            end = group[i + 1][0] if i + 1 < len(group) else we
            parts = [("{\\c&H00E5FF&}" + esc(w).upper() + "{\\c&HFFFFFF&}") if j == i else esc(w).upper()
                     for j, (_, _, w) in enumerate(group)]
            lines.append(f"Dialogue: 0,{ts(ws)},{ts(end)},Cap,,0,0,0,,{' '.join(parts)}\n")
    return "".join(lines)


def transcribe(path: Path, model_name: str, lang: str | None) -> list[tuple[float, float, str]]:
    """Wort-Zeitstempel mit faster-whisper. Fehlt das Paket, gibt es einfach keine Untertitel."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return []
    model = _model(model_name)
    segs, _ = model.transcribe(str(path), language=lang or None, word_timestamps=True, vad_filter=True)
    return [(w.start, w.end, w.word.strip()) for s in segs for w in (s.words or []) if w.word.strip()]


_models: dict = {}


def _model(name: str):
    if name not in _models:
        from faster_whisper import WhisperModel
        try:
            _models[name] = WhisperModel(name, device="cuda", compute_type="float16")
        except Exception:
            _models[name] = WhisperModel(name, device="cpu", compute_type="int8")
    return _models[name]


# ---------- 9:16 ----------

def layout_filter(facecam: dict | None, subs: bool) -> str:
    sub = ",subtitles=subs.ass" if subs else ""
    if facecam:
        x, y, w, h = (float(facecam[k]) for k in ("x", "y", "w", "h"))
        return (f"[0:v]split=2[a][b];"
                f"[a]crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},scale=1080:640:force_original_aspect_ratio=increase,"
                f"crop=1080:640,setsar=1[cam];"
                f"[b]crop=ih*1080/1280:ih:(iw-ow)/2:0,scale=1080:1280,setsar=1[game];"
                f"[cam][game]vstack=inputs=2,fps=30,setsar=1{sub}[v]")
    return ("[0:v]split=2[a][b];"
            "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=28:2,"
            "eq=brightness=-0.12[bg];"
            "[b]scale=1080:-2,setsar=1[fg];"
            f"[bg][fg]overlay=0:(H-h)/2,fps=30,setsar=1{sub}[v]")


def render(raw: Path, offset: float, duration: float, out: Path, facecam: dict | None,
           ass_text: str | None) -> None:
    work = out.parent
    clip_src = work / "src.mp4"
    # Erst genau zuschneiden, damit Whisper-Zeiten und Untertitel bei 0 beginnen
    run(["-ss", f"{offset:.2f}", "-i", str(raw), "-t", f"{duration:.2f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "192k", str(clip_src)])
    if ass_text:
        (work / "subs.ass").write_text(ass_text, "utf-8")
    args = ["-i", "src.mp4", "-filter_complex", layout_filter(facecam, bool(ass_text)),
            "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-movflags", "+faststart", out.name]
    try:
        run(args, cwd=work)
    except RuntimeError:
        if not ass_text:
            raise
        # Falls libass/Schriften fehlen: ohne Untertitel rendern statt abbrechen
        args[3] = layout_filter(facecam, False)
        run(args, cwd=work)
    run(["-ss", "1", "-i", out.name, "-frames:v", "1", "-vf", "scale=360:-2", "thumb.jpg"], cwd=work)
