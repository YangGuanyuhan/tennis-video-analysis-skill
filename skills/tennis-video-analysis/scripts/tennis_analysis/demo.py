"""A small reproducible demo using drawn figures, not a person's footage."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

from .media import extract, run
from .render import render


REPORT = """# Synthetic example / 示意案例

**These generated drawings demonstrate the review interface. They are not real tennis footage and do not support a coaching diagnosis.**

这些画面由程序绘制，用于展示报告、连续帧和原视频定位，不是对真实球员的动作评价。音轨为生成的示意音。

## Observation / 画面观察

The first window shows a figure near a fixed position; the second shows a moving figure. Compare their actual frames with the slider and arrow keys.

第一组人物位置相对固定，第二组人物在移动。用时间轴查看前后连续变化；不同组的对齐时刻仅是示例定位。

## A real review / 真实分析应如何写

Separate what is visible from what is inferred. Keep preparation, contact, follow-through and recovery in context. Record uncertain contact timing and any missing recovery frames.

| Evidence / 依据 | Interpretation / 解释 | Next check / 下一步 |
|---|---|---|
| A visible movement in a continuous window / 连续片段里可见的变化 | A tentative hypothesis / 有待验证的解释 | Compare similar balls and retain failed attempts / 比较相似来球并保留失败样本 |

## Limits / 限制

The software extracts and presents evidence. An agent or coach must inspect the footage and write observations; no pose score or automated fault diagnosis is generated.
"""


def make_demo(output: Path) -> Path:
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    drawings = output / "drawings"
    drawings.mkdir()
    for i in range(48):
        t = i / 12
        image = Image.new("RGB", (384, 216), "#e7eee1")
        d = ImageDraw.Draw(image)
        d.rectangle((18, 72, 366, 200), fill="#448571", outline="white", width=2)
        d.line((192, 72, 192, 200), fill="white", width=2)
        d.line((18, 136, 366, 136), fill="#d3e7d7", width=2)
        x = 140 if t < 2 else 120 + int((t - 2) * 52)
        y = 100
        phase = (t % 2) / 2 * math.pi * 2
        hand = (x + int(38 * math.cos(phase)), y + int(24 * math.sin(phase)))
        d.ellipse((x - 8, y - 31, x + 8, y - 15), fill="#eee6c5")
        d.line((x, y - 15, x, y + 20), fill="#f8f4e5", width=8)
        d.line((x, y, *hand), fill="#f8f4e5", width=5)
        d.line((x, y + 20, x - 15, y + 48), fill="#1c3934", width=5)
        d.line((x, y + 20, x + 15, y + 48), fill="#1c3934", width=5)
        d.ellipse((hand[0] - 8, hand[1] - 13, hand[0] + 8, hand[1] + 13), outline="#d7e878", width=2)
        ballx = 60 + int((t % 2) * 135)
        d.ellipse((ballx - 3, 107, ballx + 3, 113), fill="#e9ee70")
        d.text((18, 13), "SYNTHETIC DEMO / NOT REAL FOOTAGE", fill="#234b40")
        d.text((18, 31), f"t = {t:.3f} s", fill="#234b40")
        image.save(drawings / f"{i + 1:05d}.png")
    video = output / "synthetic.mp4"
    run(["ffmpeg", "-n", "-nostdin", "-v", "error", "-framerate", "12", "-i", str(drawings / "%05d.png"),
         "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(video)])
    plan = {"version": 1, "title": "Tennis Video Analysis · Synthetic Demo", "language": "en",
            "continuous_segments": [{"id": "demo", "start": 0, "end": 4}], "windows": [
                {"id": "D01", "start": 0.35, "end": 1.7, "contact_time": 1, "kind": "Stationary illustration",
                 "observation": "Generated figure near a fixed location; illustrative contact time, not a measured hit."},
                {"id": "D02", "start": 2.35, "end": 3.7, "contact_time": 3, "kind": "Moving illustration",
                 "observation": "Generated figure moving laterally; demonstration data, not evidence of a technique fault."}]}
    manifest = extract(video, plan, output / "evidence")
    report = output / "report.md"
    report.write_text(REPORT, encoding="utf-8")
    # Drawings are reproducible build inputs; the checked-in example uses only extracted evidence.
    return render(manifest, report, output / "index.html", video)
