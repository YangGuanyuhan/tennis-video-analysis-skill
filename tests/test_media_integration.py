import hashlib
import json
import shutil
import subprocess

import pytest
from PIL import Image

from tennis_analysis.media import extract, overview, probe, run
from tennis_analysis.model import load_json, validate_manifest

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg not installed")


@pytest.fixture
def video(tmp_path):
    source = tmp_path / "原声 可变帧率.mp4"
    run(["ffmpeg", "-n", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=2",
         "-f", "lavfi", "-i", "sine=frequency=880:duration=2", "-vf", "select=not(eq(n\\,3)+eq(n\\,9)+eq(n\\,27))",
         "-fps_mode", "vfr", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(source)])
    return source


def test_real_vfr_frames_source_audio_and_resolution_remain_intact(video, tmp_path):
    before = hashlib.sha256(video.read_bytes()).hexdigest()
    p = {"version": 1, "continuous_segments": [{"id": "whole", "start": 0, "end": 2}],
         "windows": [{"id": "S01", "start": 0.113, "end": 0.817, "contact_time": 0.5, "crop": [10, 10, 200, 120]}]}
    target = extract(video, p, tmp_path / "输出", "png")
    manifest = load_json(target)
    frames = manifest["windows"][0]["frames"]
    raw = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(video)]).stdout)
    source_times = [float(f["best_effort_timestamp_time"]) for f in raw["frames"]]
    expected = [t for t in source_times if p["windows"][0]["start"] <= t < p["windows"][0]["end"]]
    assert [f["time"] for f in frames] == pytest.approx(expected, abs=0.0001)
    gaps = [round(b["time"] - a["time"], 3) for a, b in zip(frames, frames[1:])]
    assert len(set(gaps)) > 1  # Native gaps survive; no constant-fps reconstruction.
    with Image.open(target.parent / frames[0]["src"]) as image:
        assert image.size == (200, 120)
    assert before == hashlib.sha256(video.read_bytes()).hexdigest()
    assert probe(video)["audio"][0]["codec"] == "aac"
    assert manifest["media"]["width"] == 320
    assert validate_manifest(manifest, target.parent)["cut_check"] == "checked"
    with pytest.raises(FileExistsError):
        extract(video, p, target.parent)


def test_rejected_plan_creates_no_output_directory(video, tmp_path):
    p = {"version": 1, "continuous_segments": [{"start": 0, "end": 1}, {"start": 1, "end": 2}],
         "windows": [{"id": "S01", "start": 0.8, "end": 1.2, "contact_time": 1}]}
    output = tmp_path / "should-not-exist"
    with pytest.raises(ValueError, match="crosses a cut"):
        extract(video, p, output)
    assert not output.exists()


def test_overview_is_separately_identified_as_scaled_preview(video, tmp_path):
    output = tmp_path / "overview"
    overview(video, output, 0.5, 160)
    data = load_json(output / "overview.json")
    assert data["scaled_preview"] is True
    assert len(data["frames"]) == 4
    with Image.open(output / data["frames"][0]["src"]) as image:
        assert image.width == 160
