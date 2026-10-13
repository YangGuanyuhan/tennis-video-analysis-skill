"""Read media and extract actual frames without writing to the source video."""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .model import load_json, save_json, stamp, validate_manifest, validate_plan


def run(args: list[str]) -> subprocess.CompletedProcess:
    if not shutil.which(args[0]):
        raise RuntimeError(f"{args[0]} is required; install FFmpeg and put it on PATH")
    proc = subprocess.run(args, capture_output=True, encoding="utf-8", errors="replace", shell=False)
    if proc.returncode:
        raise RuntimeError(f"{args[0]} failed:\n{proc.stderr[-4000:]}")
    return proc


def probe(video: Path) -> dict:
    video = Path(video).resolve(strict=True)
    raw = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)]).stdout)
    stream = next((s for s in raw["streams"] if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")), None)
    if stream is None:
        raise ValueError("No video stream found")
    def rate(value):
        try:
            return float(Fraction(value))
        except (ValueError, ZeroDivisionError):
            return None
    rotation = next((s.get("rotation", 0) for s in stream.get("side_data_list", []) if "rotation" in s), 0)
    return {"name": video.name, "duration": float(raw["format"]["duration"]),
            "width": stream["width"], "height": stream["height"], "codec": stream.get("codec_name"),
            "nominal_fps": rate(stream.get("r_frame_rate", "0/0")),
            "average_fps": rate(stream.get("avg_frame_rate", "0/0")),
            "rotation": rotation, "pixel_format": stream.get("pix_fmt"),
            "audio": [{"codec": s.get("codec_name"), "sample_rate": s.get("sample_rate"), "channels": s.get("channels")}
                      for s in raw["streams"] if s.get("codec_type") == "audio"]}


def parse_showinfo(log: str, start: float, file_count: int) -> list[float]:
    base = re.search(r"config in time_base:\s*(\d+)/(\d+)", log)
    ticks = re.findall(r"\bn:\s*\d+\s+pts:\s*(-?\d+)\s+pts_time:", log)
    if base and ticks:
        ratio = Fraction(int(base[1]), int(base[2]))
        times = [round(start + float(int(t) * ratio), 9) for t in ticks]
    else:
        pts = re.findall(r"\bn:\s*\d+\s+pts:\s*\S+\s+pts_time:([\d.e+\-]+)", log)
        times = [round(start + float(t), 9) for t in pts]
    # The filter may log one or two frames rejected by the output duration gate.
    if not file_count or not 0 <= len(times) - file_count <= 2:
        raise ValueError(f"FFmpeg frame/timestamp mismatch: {file_count} images, {len(times)} timestamps")
    return times[:file_count]


def contact_sheet(directory: Path, window: dict, indices: list[int], output: Path, tile_width: int = 300) -> None:
    if not indices:
        return
    columns = 6
    cw, ch = window["crop"][2:]
    tile_height = round(tile_width * ch / cw) + 24
    canvas = Image.new("RGB", (tile_width * columns, tile_height * ((len(indices) + columns - 1) // columns)), "#eef4f4")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for j, i in enumerate(indices):
        f = window["frames"][i]
        with Image.open(directory / f["src"]) as original:
            image = original.copy()
        image.thumbnail((tile_width, tile_height - 24), Image.Resampling.LANCZOS)
        x, y = (j % columns) * tile_width, (j // columns) * tile_height
        canvas.paste(image, (x + (tile_width - image.width) // 2, y))
        draw.text((x + 4, y + tile_height - 20), f"{stamp(f['time'])}  F{i + 1}", font=font, fill="#16333d")
    canvas.save(output, quality=92)


def extract(video: Path, plan: dict, output: Path, image_format: str = "jpg") -> Path:
    if image_format not in ("jpg", "png"):
        raise ValueError("image_format must be jpg or png")
    metadata = probe(video)
    if metadata["rotation"]:
        raise ValueError("Rotation metadata is present: use displayed-orientation footage or explicitly prepare a separate normalized copy first")
    plan = validate_plan(plan, metadata["duration"], metadata["width"], metadata["height"])
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError("Extraction output already exists; choose a new directory to avoid stale frames")
    source = Path(video).resolve(strict=True)
    before = source.stat()
    output.mkdir(parents=True)
    manifest = {"version": 1, "title": plan.get("title", "Tennis video review"), "language": plan.get("language", "zh"),
                "profile": plan.get("profile", {}), "media": metadata,
                "cut_check": "checked" if plan.get("continuous_segments") else "not_checked",
                "continuous_segments": plan.get("continuous_segments", []), "windows": []}
    for item in plan["windows"]:
        w = dict(item)
        folder = output / w["id"] / "frames"
        folder.mkdir(parents=True)
        x, y, cw, ch = w["crop"]
        filters = f"crop={cw}:{ch}:{x}:{y}:exact=1,showinfo"
        args = ["ffmpeg", "-n", "-nostdin", "-v", "info", "-threads", "2", "-ss", str(w["start"]),
                "-i", str(source), "-t", str(w["end"] - w["start"]), "-map", "0:v:0", "-an", "-sn", "-dn",
                "-vf", filters, "-fps_mode", "passthrough", "-threads", "1"]
        if image_format == "jpg":
            args += ["-q:v", "3"]
        args += [str(folder / f"%05d.{image_format}")]
        log = run(args).stderr
        (folder.parent / "ffmpeg.log").write_text(log, encoding="utf-8")
        files = sorted(folder.glob(f"*.{image_format}"))
        times = parse_showinfo(log, w["start"], len(files))
        w["frames"] = [{"time": t, "src": f.relative_to(output).as_posix()} for f, t in zip(files, times)]
        w["sheet"] = f"{w['id']}/sequence.jpg"
        w["contact_sheet"] = f"{w['id']}/contact.jpg"
        step = max(1, round((metadata["nominal_fps"] or 30) / 10))
        contact_sheet(output, w, list(range(0, len(times), step)), output / w["sheet"])
        anchor = w.get("contact_time")
        if anchor is not None:
            near = [i for i, t in enumerate(times) if anchor - 0.3 <= t <= anchor + 0.32]
            contact_sheet(output, w, near, output / w["contact_sheet"])
        manifest["windows"].append(w)
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("Source changed during extraction; inspect it before using this evidence")
    manifest["validation"] = validate_manifest(manifest, output)
    manifest["source_unchanged_stat"] = True
    save_json(output / "manifest.json", manifest)
    export_csv(manifest, output / "observations.csv")
    return output / "manifest.json"


def export_csv(manifest: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "start_seconds", "end_seconds", "contact_estimate_seconds", "kind", "observation", "confidence", "segment"])
        for w in manifest["windows"]:
            cells = [w["id"], w["start"], w["end"], w.get("contact_time"), w.get("kind", ""), w.get("observation", ""), w.get("confidence", ""), w.get("segment", "")]
            writer.writerow([("'" + v) if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v for v in cells])


def overview(video: Path, output: Path, interval: float = 30, width: int = 640) -> None:
    if interval <= 0 or width <= 0:
        raise ValueError("interval and width must be positive")
    metadata = probe(video)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    frames = []
    i = 0
    while i * interval < metadata["duration"]:
        t = i * interval
        filename = f"{i + 1:05d}.jpg"
        run(["ffmpeg", "-n", "-nostdin", "-v", "error", "-ss", str(t), "-i", str(video), "-frames:v", "1",
             "-vf", f"scale={width}:-2", "-threads", "1", "-update", "1", str(output / filename)])
        if (output / filename).is_file():
            frames.append({"time": t, "src": filename})
        i += 1
    save_json(output / "overview.json", {"version": 1, "media": metadata, "frames": frames, "scaled_preview": True})
    for n in range(0, len(frames), 24):
        w = {"crop": [0, 0, metadata["width"], metadata["height"]], "frames": frames}
        contact_sheet(output, w, list(range(n, min(n + 24, len(frames)))), output / f"overview-{n // 24 + 1:03d}.jpg", 320)


def import_legacy(index: Path, output: Path, metadata: dict | None = None) -> Path:
    """Import an existing index; image paths continue to point into its original directory."""
    rows = load_json(index)
    if not isinstance(rows, list):
        raise ValueError("Legacy index must be a list")
    windows = []
    for r in rows:
        files = sorted((index.parent / r["id"] / "frames").glob("*.jpg"))
        times = r["frame_times"]
        if len(files) != len(times):
            raise ValueError(f"{r['id']}: legacy frame count mismatch")
        windows.append({"id": r["id"], "start": r["start"], "end": r["end"], "crop": r["crop"],
                        "contact_time": None if r.get("contact_uncertain") else r.get("contact_estimate", r.get("time")),
                        "kind": r.get("kind", ""), "observation": r.get("note", ""), "confidence": r.get("confidence", ""),
                        "segment": r.get("segment"), "sheet": f"{r['id']}/连续动作.jpg", "contact_sheet": f"{r['id']}/触球逐帧.jpg",
                        "frames": [{"time": t, "src": f.relative_to(index.parent).as_posix()} for f, t in zip(files, times)]})
    manifest = {"version": 1, "title": "击球动作分析", "language": "zh", "media": metadata or {},
                "cut_check": "not_checked", "continuity_note": "Imported frame order; cut boundaries require the original edit list or manual verification.",
                "windows": windows}
    if output.parent.resolve() != index.parent.resolve():
        raise ValueError("Keep the imported manifest beside the legacy index so frame paths remain portable")
    manifest["validation"] = validate_manifest(manifest, index.parent)
    save_json(output, manifest)
    return output
