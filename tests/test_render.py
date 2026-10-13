import json

import pytest
from PIL import Image

from tennis_analysis.model import save_json
from tennis_analysis.render import markdown_report, render


def test_markdown_disables_raw_html_and_external_image_requests(tmp_path):
    result, toc = markdown_report("# Review\n<script>alert(1)</script>\n\n[x](javascript:alert(1))\n\n![tracking](https://example.com/t.png)", tmp_path, tmp_path)
    assert "<script>" not in result
    assert 'href="javascript:' not in result
    assert 'src="https://example.com' not in result
    assert "chapter-1" in toc


def test_render_safe_json_and_portable_image_paths(tmp_path):
    root = tmp_path / "证据"
    root.mkdir()
    Image.new("RGB", (16, 16)).save(root / "frame.jpg")
    manifest = {"version": 1, "title": "Review", "language": "en", "windows": [{"id": "S01", "start": 0, "end": 1,
                "contact_time": 0.4, "observation": '</script><script>alert("x")</script>', "frames": [{"time": 0.4, "src": "frame.jpg"}]}]}
    manifest["summary_cards"] = [{"title": '<img src=x onerror="alert(1)">', "text": "A < B"}]
    manifest["comparison_images"] = [{"src": "frame.jpg", "alt": '" onload="alert(1)'}]
    save_json(root / "manifest.json", manifest)
    report = tmp_path / "report.md"
    report.write_text("# Evidence\n\n![frame](证据/frame.jpg)", encoding="utf-8")
    output = render(root / "manifest.json", report, tmp_path / "review.html")
    page = output.read_text(encoding="utf-8")
    assert "\\u003c/script\\u003e" in page
    assert "alert(\"x\")</script>" not in page
    assert "%E8%AF%81%E6%8D%AE/frame.jpg" in page
    assert '<img src=x onerror="alert(1)">' not in page
    assert "A &lt; B" in page
    assert "@@REPORT@@" not in page
    with pytest.raises(FileExistsError):
        render(root / "manifest.json", report, output)


def test_missing_evidence_prevents_report_publication(tmp_path):
    manifest = {"version": 1, "windows": [{"id": "S01", "start": 0, "end": 1,
                "frames": [{"time": 0.4, "src": "missing.jpg"}]}]}
    save_json(tmp_path / "manifest.json", manifest)
    (tmp_path / "report.md").write_text("# Review", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing"):
        render(tmp_path / "manifest.json", tmp_path / "report.md", tmp_path / "index.html")
