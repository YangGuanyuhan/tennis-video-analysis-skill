"""Render a Markdown report and frame viewer as one offline HTML document."""
from __future__ import annotations

import html
import json
import os
import re
from importlib.resources import files
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from markdown_it import MarkdownIt

from .model import load_json, relative_path, validate_manifest


def local_uri(target: Path, base: Path) -> str:
    target, base = target.resolve(), base.resolve()
    try:
        return quote(Path(os.path.relpath(target, base)).as_posix(), safe="/")
    except ValueError:
        return target.as_uri()


def markdown_report(text: str, report_directory: Path, output_directory: Path) -> tuple[str, str]:
    # Raw HTML and unsafe link protocols are disabled by the Markdown renderer.
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    tokens = md.parse(text)
    headings, number = [], 0
    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            number += 1
            token.attrSet("id", f"chapter-{number}")
            title = tokens[i + 1].content
            headings.append(f'<a class="toc-{token.tag}" href="#chapter-{number}">{html.escape(title)}</a>')
        for child in token.children or []:
            if child.type == "image":
                src = child.attrGet("src") or ""
                parsed = urlsplit(src)
                target = (report_directory / unquote(parsed.path)).resolve()
                if parsed.scheme or parsed.netloc or not target.is_relative_to(report_directory.resolve()):
                    child.type = "text"
                    child.content = f"[Image omitted: {child.content}]"
                    child.children = None
                    child.attrs = {}
                else:
                    child.attrSet("src", local_uri(target, output_directory))
            elif child.type == "link_open":
                href = child.attrGet("href") or ""
                parsed = urlsplit(href)
                if not parsed.scheme and not parsed.netloc and parsed.path:
                    child.attrSet("href", local_uri(report_directory / unquote(parsed.path), output_directory) + ("#" + parsed.fragment if parsed.fragment else ""))
    return md.renderer.render(tokens, md.options, {}), "\n".join(headings)


def render(manifest_path: Path, report_path: Path, output: Path, video: Path | None = None, overwrite: bool = False) -> Path:
    manifest_path, report_path, output = Path(manifest_path).resolve(), Path(report_path).resolve(), Path(output).resolve()
    if output.suffix.lower() != ".html" or output in (manifest_path, report_path) or video and output == Path(video).resolve():
        raise ValueError("HTML output must be separate from the input files")
    if output.exists() and not overwrite:
        raise FileExistsError("HTML exists; use --overwrite to intentionally update the report")
    data = load_json(manifest_path)
    validation = validate_manifest(data, manifest_path.parent)
    report, toc = markdown_report(report_path.read_text(encoding="utf-8-sig"), report_path.parent, output.parent)
    windows = []
    for item in sorted(data["windows"], key=lambda w: w["start"]):
        w = dict(item)
        w["frames"] = [{"time": f["time"], "src": local_uri(manifest_path.parent / f["src"], output.parent)} for f in item["frames"]]
        for key in ("sheet", "contact_sheet"):
            if w.get(key):
                w[key] = local_uri(manifest_path.parent / w[key], output.parent)
        windows.append(w)
    language = data.get("language", "zh")
    if language not in ("zh", "en"):
        language = "zh"
    payload = {"windows": windows, "validation": validation, "media": data.get("media", {}), "language": language,
               "default_comparison": data.get("default_comparison", [])}
    supplement = []
    cards = data.get("summary_cards", [])
    if cards:
        card_html = "".join('<div class="tip"><strong>' + html.escape(str(c.get("title", ""))) + '</strong>' +
                            html.escape(str(c.get("text", ""))) + '</div>' for c in cards)
        heading = ("练球时先记住这三件事" if len(cards) == 3 else "练球要点") if language == "zh" else "Practice priorities"
        supplement.append('<section class="card"><h2>' + heading + '</h2><div class="tips">' + card_html + '</div></section>')
    boards = []
    root = manifest_path.parent.resolve()
    for item in data.get("comparison_images", []):
        target = (root / relative_path(item["src"])).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise ValueError("Missing or unsafe comparison image")
        boards.append('<img src="' + html.escape(local_uri(target, output.parent), quote=True) + '" alt="' +
                      html.escape(str(item.get("alt", "")), quote=True) + '">')
    if boards:
        heading = "关键阶段对照" if language == "zh" else "Key phase comparisons"
        supplement.append('<section class="card boards"><h2>' + heading + '</h2>' + "".join(boards) + '</section>')
    # Escape HTML script terminators even when notes contain hostile strings.
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    assets = files("tennis_analysis").joinpath("_assets")
    template = assets.joinpath("report.html").read_text(encoding="utf-8")
    values = {"LANG": language, "TITLE": html.escape(str(data.get("title", "Tennis video analysis"))),
              "CSS": assets.joinpath("report.css").read_text(encoding="utf-8"),
              "JS": assets.joinpath("viewer.js").read_text(encoding="utf-8"), "DATA": encoded,
              "REPORT": report, "TOC": toc, "VIDEO": html.escape(local_uri(Path(video), output.parent), quote=True) if video else "",
              "MARKDOWN": html.escape(local_uri(report_path, output.parent), quote=True),
              "INTRO": html.escape(str(data.get("intro", ""))), "SUPPLEMENT": "".join(supplement)}
    page = re.sub(r"@@([A-Z]+)@@", lambda m: values[m[1]], template)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    return output
