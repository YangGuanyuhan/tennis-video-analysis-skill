import copy
import math

import pytest

from tennis_analysis.model import relative_path, stamp, validate_manifest, validate_plan
from tennis_analysis.media import parse_showinfo


def plan():
    return {"version": 1, "continuous_segments": [{"id": "one", "start": 0, "end": 2}, {"id": "two", "start": 2, "end": 4}],
            "windows": [{"id": "S01", "start": 0.5, "end": 1.5, "contact_time": 1, "crop": [0, 0, 320, 180]}]}


@pytest.mark.parametrize("value", [math.nan, math.inf, True, "1"])
def test_invalid_numeric_timing_is_rejected(value):
    p = plan()
    p["windows"][0]["start"] = value
    with pytest.raises(ValueError):
        validate_plan(p, 4, 320, 180)


def test_cross_cut_window_is_rejected():
    p = plan()
    p["windows"][0].update(start=1.7, end=2.3, contact_time=2)
    with pytest.raises(ValueError, match="crosses a cut"):
        validate_plan(p, 4, 320, 180)


@pytest.mark.parametrize("sid", ["../outside", "C:escape", "bad/path", ".", "x" * 65])
def test_unsafe_window_ids_are_rejected(sid):
    p = plan()
    p["windows"][0]["id"] = sid
    with pytest.raises(ValueError):
        validate_plan(p, 4, 320, 180)


def test_invalid_contact_and_crop():
    p = plan()
    p["windows"][0]["contact_time"] = 1.8
    with pytest.raises(ValueError, match="contact_time"):
        validate_plan(p, 4, 320, 180)
    p = plan()
    p["windows"][0]["crop"] = [300, 0, 80, 180]
    with pytest.raises(ValueError, match="crop"):
        validate_plan(p, 4, 320, 180)


def test_unknown_contact_is_supported_and_no_cuts_are_invented():
    p = plan()
    p.pop("continuous_segments")
    p["windows"][0]["contact_time"] = None
    w = validate_plan(p, 4, 320, 180)["windows"][0]
    assert w["contact_time"] is None and w["segment"] is None


def test_irregular_pts_are_retained():
    log = "config in time_base: 1/600\nn: 0 pts: 0 pts_time:0\nn: 1 pts: 10 pts_time:0.0166667\nn: 2 pts: 30 pts_time:0.05\nn: 3 pts: 40 pts_time:0.0666667"
    assert parse_showinfo(log, 2, 4) == pytest.approx([2, 2 + 1 / 60, 2.05, 2 + 1 / 15])
    with pytest.raises(ValueError, match="mismatch"):
        parse_showinfo(log, 2, 3)
    with pytest.raises(ValueError, match="mismatch"):
        parse_showinfo(log, 2, 5)


def test_stamp_does_not_round_to_sixty_seconds():
    assert stamp(59.9996) == "01:00.000"


@pytest.mark.parametrize("path", ["../secret.jpg", "/abs.jpg", "C:/secret.jpg", "https://site/image.jpg", "S01\\image.jpg"])
def test_external_frame_paths_are_rejected(path):
    with pytest.raises(ValueError):
        relative_path(path)


def test_manifest_rechecks_cut_claim_and_frame_order():
    base = {"version": 1, "cut_check": "not_checked", "windows": [{"id": "S01", "start": 0, "end": 1,
            "frames": [{"time": 0.1, "src": "a.jpg"}, {"time": 0.4, "src": "b.jpg"}]}]}
    assert validate_manifest(base)["frame_count"] == 2
    broken = copy.deepcopy(base)
    broken["windows"][0]["frames"][1]["time"] = 0.05
    with pytest.raises(ValueError):
        validate_manifest(broken)
    base["cut_check"] = "checked"
    with pytest.raises(ValueError, match="requires"):
        validate_manifest(base)
