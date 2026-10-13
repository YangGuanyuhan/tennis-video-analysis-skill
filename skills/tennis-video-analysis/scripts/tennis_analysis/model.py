"""Validated timelines and portable evidence paths."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path, PurePosixPath


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def finite(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def stamp(t: float) -> str:
    milliseconds = round(t * 1000)
    minutes, rest = divmod(milliseconds, 60000)
    return f"{minutes:02}:{rest // 1000:02}.{rest % 1000:03}"


def relative_path(value: str) -> str:
    if not isinstance(value, str) or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("Evidence paths must be relative POSIX paths")
    p = PurePosixPath(value)
    if not value or p.is_absolute() or ".." in p.parts or p.as_posix() == ".":
        raise ValueError("Evidence path escapes its report directory")
    return p.as_posix()


def validate_plan(plan: dict, duration: float, width: int, height: int) -> dict:
    if type(plan.get("version")) is not int or plan.get("version") != 1:
        raise ValueError("Plan version must be 1")
    windows = plan.get("windows")
    if not isinstance(windows, list) or not windows:
        raise ValueError("Plan needs at least one window")
    segments = plan.get("continuous_segments", [])
    if not isinstance(segments, list):
        raise ValueError("continuous_segments must be a list")
    spans = []
    for s in segments:
        start, end = finite(s["start"], "segment start"), finite(s["end"], "segment end")
        if not 0 <= start < end <= duration + 0.002:
            raise ValueError("Invalid continuous segment")
        spans.append((start, end, str(s.get("id", len(spans) + 1))))
    spans.sort()
    if any(b[0] < a[1] for a, b in zip(spans, spans[1:])):
        raise ValueError("Continuous segments overlap")
    result = dict(plan)
    result["windows"] = []
    ids = set()
    for item in windows:
        w = dict(item)
        sid = w.get("id", "")
        if not isinstance(sid, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", sid) or sid in ids:
            raise ValueError("Window IDs must be unique safe directory names")
        ids.add(sid)
        start, end = finite(w["start"], "window start"), finite(w["end"], "window end")
        if not 0 <= start < end <= duration + 0.002:
            raise ValueError(f"{sid}: window outside the video")
        contact = w.get("contact_time")
        if contact is not None:
            contact = finite(contact, "contact_time")
            if not start <= contact < end:
                raise ValueError(f"{sid}: contact_time outside window")
        w.update(start=start, end=end, contact_time=contact)
        cr = w.get("contact_range")
        if cr is not None:
            if not isinstance(cr, list) or len(cr) != 2:
                raise ValueError("contact_range must contain two times")
            lo, hi = [finite(v, "contact_range") for v in cr]
            if not start <= lo <= hi < end or contact is not None and not lo <= contact <= hi:
                raise ValueError("contact_range outside window or missing its estimate")
        crop = w.get("crop", [0, 0, width, height])
        if not isinstance(crop, list) or len(crop) != 4 or any(type(v) is not int for v in crop):
            raise ValueError("crop must be [x, y, width, height] in integer source pixels")
        x, y, cw, ch = crop
        if x < 0 or y < 0 or cw <= 0 or ch <= 0 or x + cw > width or y + ch > height:
            raise ValueError(f"{sid}: crop outside the source image")
        w["crop"] = crop
        if spans:
            match = next((s for s in spans if s[0] <= start and end <= s[1] + 1e-6), None)
            if match is None:
                raise ValueError(f"{sid}: window crosses a cut or lacks a containing segment")
            w["segment"] = match[2]
        else:
            w["segment"] = None
        result["windows"].append(w)
    return result


def validate_manifest(manifest: dict, directory: Path | None = None) -> dict:
    if type(manifest.get("version")) is not int or manifest.get("version") != 1 or not manifest.get("windows"):
        raise ValueError("Invalid or empty manifest")
    count, ids = 0, set()
    root = directory.resolve() if directory is not None else None
    for w in manifest["windows"]:
        if w["id"] in ids:
            raise ValueError("Duplicate window ID")
        ids.add(w["id"])
        start, end = finite(w["start"], "start"), finite(w["end"], "end")
        if not 0 <= start < end:
            raise ValueError("Invalid window bounds")
        contact = w.get("contact_time")
        if contact is not None and not start <= finite(contact, "contact_time") < end:
            raise ValueError("Contact estimate outside the window")
        frames = w.get("frames", [])
        if not frames:
            raise ValueError(f"{w['id']}: no frames")
        previous = -math.inf
        paths = set()
        for f in frames:
            t = finite(f["time"], "frame time")
            if not start - 1e-6 <= t < end + 1e-6 or t <= previous:
                raise ValueError(f"{w['id']}: frame order or bounds invalid")
            previous = t
            p = relative_path(f["src"])
            if p in paths:
                raise ValueError("Repeated image path inside a window")
            paths.add(p)
            if root is not None:
                target = (root / p).resolve()
                if not target.is_relative_to(root) or not target.is_file():
                    raise ValueError(f"Missing or unsafe frame: {p}")
            count += 1
    if manifest.get("cut_check") == "checked":
        if not manifest.get("continuous_segments"):
            raise ValueError("A checked cut status requires continuous segment boundaries")
        media = manifest["media"]
        checked = validate_plan({"version": 1, "continuous_segments": manifest["continuous_segments"], "windows": manifest["windows"]},
                                media["duration"], media["width"], media["height"])
        if any(a.get("segment") != b["segment"] for a, b in zip(manifest["windows"], checked["windows"])):
            raise ValueError("Window segment IDs disagree with the cut boundaries")
    return {"window_count": len(ids), "frame_count": count, "ordered_frames": True,
            "cut_check": manifest.get("cut_check", "not_checked")}
