"""Command-line interface, also usable directly from an installed skill."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .demo import make_demo
from .media import extract, import_legacy, overview, probe
from .model import load_json, save_json, validate_manifest
from .render import render
from .server import serve


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Extract continuous tennis frame evidence and render a human-authored review.")
    p.add_argument("--version", action="version", version=__version__)
    subs = p.add_subparsers(dest="command", required=True)
    inspect = subs.add_parser("inspect", help="Read resolution, timing and audio metadata")
    inspect.add_argument("video", type=Path)
    inspect.add_argument("--output", type=Path)
    ov = subs.add_parser("overview", help="Generate scaled scouting sheets; not detailed frame evidence")
    ov.add_argument("video", type=Path)
    ov.add_argument("--output", required=True, type=Path)
    ov.add_argument("--interval", type=float, default=30)
    ov.add_argument("--width", type=int, default=640)
    ex = subs.add_parser("extract", help="Extract consecutive actual frames from a validated plan")
    ex.add_argument("video", type=Path)
    ex.add_argument("--plan", required=True, type=Path)
    ex.add_argument("--output", required=True, type=Path)
    ex.add_argument("--format", choices=["jpg", "png"], default="jpg")
    rd = subs.add_parser("render", help="Merge Markdown review and interactive evidence in one HTML")
    rd.add_argument("--manifest", required=True, type=Path)
    rd.add_argument("--report", required=True, type=Path)
    rd.add_argument("--output", required=True, type=Path)
    rd.add_argument("--video", type=Path)
    rd.add_argument("--overwrite", action="store_true")
    check = subs.add_parser("validate", help="Check actual frame files, timeline order and manifest bounds")
    check.add_argument("manifest", type=Path)
    legacy = subs.add_parser("import-legacy", help="Import an earlier frame_times index without extracting again")
    legacy.add_argument("index", type=Path)
    legacy.add_argument("--output", required=True, type=Path)
    legacy.add_argument("--video", type=Path)
    demo = subs.add_parser("demo", help="Generate a playable example using drawn synthetic figures")
    demo.add_argument("--output", required=True, type=Path)
    server = subs.add_parser("serve", help="Preview local report directories with byte-range video seeking")
    server.add_argument("--directory", type=Path, default=Path.cwd())
    server.add_argument("--port", type=int, default=8765)
    return p


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    try:
        if args.command == "inspect":
            result = probe(args.video)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                if args.output.resolve() == args.video.resolve():
                    raise ValueError("Metadata output cannot overwrite the input video")
                save_json(args.output, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "overview":
            overview(args.video, args.output, args.interval, args.width)
            print(args.output)
        elif args.command == "extract":
            print(extract(args.video, load_json(args.plan), args.output, args.format))
        elif args.command == "render":
            print(render(args.manifest, args.report, args.output, args.video, args.overwrite))
        elif args.command == "validate":
            print(json.dumps(validate_manifest(load_json(args.manifest), args.manifest.parent), ensure_ascii=False, indent=2))
        elif args.command == "import-legacy":
            print(import_legacy(args.index, args.output, probe(args.video) if args.video else None))
        elif args.command == "demo":
            print(make_demo(args.output))
        elif args.command == "serve":
            serve(args.directory, args.port)
        return 0
    except (OSError, ValueError, RuntimeError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
