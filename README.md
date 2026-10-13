# Tennis Video Analysis Skill

[中文说明](README.zh-CN.md) · [MIT License](LICENSE) · [Skill entrypoint](skills/tennis-video-analysis/SKILL.md)

![CI](https://github.com/YangGuanyuhan/tennis-video-analysis-skill/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

**Review a whole stroke, not just a contact pose.** An agent skill and Python toolkit for tennis footage inspection, continuous frame evidence, and offline HTML coaching reports.

Tools extract and present media. An agent or coach must visually review it and write the analysis. This project does **not** automatically detect successful shots, diagnose biomechanical faults or assign technique scores.

![Synthetic report preview](docs/images/demo.png)

*The public demo uses programmatically drawn figures and a synthetic audio tone. It includes no player's footage, personal report or local paths.*

## Features

- A self-contained `tennis-video-analysis` skill with evidence standards, coaching references and executable helpers.
- Metadata and sparse scouting sheets, followed by consecutive actual frames with presentation timestamps, including variable frame rates.
- Known montage intervals reject cross-cut windows; unchecked continuity is labeled explicitly.
- One HTML page combines the complete Markdown report, contents, side-by-side frame stepping, contact-relative alignment, slow review and original-video playback.
- Chinese/English interfaces, Unicode paths, CSV observations and an optional byte-range server for large-video seeking.
- Read-only source media. Screenshot crops retain their dimensions; scaled sheets and JPEG previews do not modify source quality, frame rate or audio.

## Quick start

Requirements: Python 3.10+, FFmpeg and ffprobe on PATH. Install FFmpeg separately using [official instructions](https://ffmpeg.org/download.html). The generated demo needs `libx264` and AAC encoding; analysis needs video decoding/image encoding.

```text
git clone https://github.com/YangGuanyuhan/tennis-video-analysis-skill.git
cd tennis-video-analysis-skill
python -m pip install -e .
tennis-analysis demo --output output/demo
```

Open `output/demo/index.html`. Keep its evidence directory alongside it. The HTML embeds data, styles and scripts; images and video are linked files. No remote service or JavaScript build is required. You can also open the checked-in [example](examples/demo/index.html) after cloning.

Optional local preview:

```text
tennis-analysis serve --directory output/demo --port 8765
```

Open `http://127.0.0.1:8765/index.html`; Ctrl+C stops the server.

## Install the skill

```text
python tools/install_skill.py
```

The installer respects `CODEX_HOME`, otherwise uses `~/.codex/skills`, and refuses to overwrite an existing skill. Alternatively copy `skills/tennis-video-analysis/` there with the repository MIT license, or unpack the skill ZIP from Releases.

Example request:

```text
Use $tennis-video-analysis to review my tennis video. Compare consecutive
frames around contact and keep preparation, follow-through and recovery in
context. I have played for three months and struggle with crowding and rally
consistency. Create a detailed HTML report and retain the original audio.
```

Standalone skill: install Pillow and markdown-it-py, then run `<skill-directory>/scripts/analyze.py` with the same subcommands below.

## Review your footage

1. Read metadata and scout:

   ```text
   tennis-analysis inspect "path/to/tennis.mp4"
   tennis-analysis overview "path/to/tennis.mp4" --output output/scouting --interval 30
   ```

2. Visually choose continuous windows. Adapt [examples/plan.json](examples/plan.json) to actual times/crops and known edit boundaries. Leave contact estimates `null` until reviewed.

   ```text
   tennis-analysis extract "path/to/tennis.mp4" --plan plan.json --output output/evidence
   ```

3. Inspect sequence sheets and adjacent frames, update human-authored manifest observations/contact estimates, write a Markdown review with timed evidence, and render:

   ```text
   tennis-analysis validate output/evidence/manifest.json
   tennis-analysis render --manifest output/evidence/manifest.json --report review.md --video "path/to/tennis.mp4" --output output/review.html
   ```

Use `--overwrite` for intentional HTML revisions. Extraction requires a new directory. Default JPEG previews save space; `--format png` produces lossless screenshots.

See [workflow and Windows examples](docs/workflow.md), [timeline schema](skills/tennis-video-analysis/references/timeline-schema.md), and [architecture](docs/architecture.md).

## Evidence and limitations

Different windows are comparisons, not consecutive rally time. Millisecond labels locate frames; visual contact estimates are not millisecond-accurate. One view may not establish grip, racket angle, three-dimensional spacing, spin, landing position or force transfer. Successful-contact montages cannot establish miss rates. State actual review coverage honestly.

Automatic cut detection, pose tracking, biomechanical measurement, HDR tone mapping, rotation normalization, video editing and automatic technique diagnosis are outside this release. A report does not substitute for a separately requested editing deliverable. Tools do not upload private footage; generated pages contain no telemetry.

## Development

```text
python -m pip install -e ".[dev]"
python -m pytest -q
python tools/validate_skill.py
python -m build
python tools/package_skill.py
```

Tests compare native variable-rate timestamps with FFprobe and check cuts, source-byte/audio preservation, Unicode paths, safe rendering and HTTP range seeking. CI runs on Windows/Linux. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

Code, documentation and generated demonstration assets are MIT licensed. FFmpeg is separately distributed with build-dependent licensing; no FFmpeg binaries are bundled. [NOTICE](NOTICE) lists third-party references. USTA/LTA do not endorse the project.
