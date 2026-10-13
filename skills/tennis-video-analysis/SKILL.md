---
name: tennis-video-analysis
description: Review local tennis strokes using continuous frame evidence and create an offline HTML coaching report with timed comparisons, original-video playback, and practical drills. Use for preparation, contact, footwork, follow-through, and recovery analysis; media helpers do not automatically diagnose technique.
---

# Tennis Video Analysis

Turn actual footage into a visually reviewed, timestamped coaching report. Scripts handle evidence and presentation; inspect the frames before writing technique conclusions. Preserve the user's source media and requested scope.

## Inspect and choose continuous windows

Python dependencies: Pillow and markdown-it-py. FFmpeg and ffprobe must be on PATH. Run the installed skill directly:

```text
python -X utf8 <skill-directory>/scripts/analyze.py inspect <video>
python -X utf8 <skill-directory>/scripts/analyze.py overview <video> --output <new-scouting-directory>
```

Ask about experience and recurring difficulties when unknown and material to the advice; continue independent inspection while waiting. Do not infer level solely from selected hits.

Scout the footage, then choose representative windows from preparation through recovery. Include comfortable and challenged balls, moving contacts, both stroke sides and consecutive shots where available. A successful-contact montage cannot establish failure rates or every cause of a missed ball.

Read [references/timeline-schema.md](references/timeline-schema.md) before constructing a plan. For a montage, obtain its edit list or manually identify cut boundaries. Known continuous intervals let the extractor reject windows crossing cuts. Otherwise the manifest records `cut_check: not_checked`; inspect continuity manually and explain that limit. Separate montage shots are not a continuous rally.

Use fixed source-pixel crops wide enough to retain the player, racket and feet throughout the window. Tracking crops can hide movement. Rotation metadata is explicitly rejected; do not silently normalize or overwrite the original.

## Inspect actual consecutive frames

```text
python -X utf8 <skill-directory>/scripts/analyze.py extract <video> --plan <plan.json> --output <new-evidence-directory>
```

Detailed windows retain actual decoded frames and presentation timing. Do not reconstruct a constant 60-fps sequence, interpolate frames, or infer timing from frame count. Overview/contact sheets are scaled previews; detailed images retain their crop dimensions. JPEG compression affects screenshots only. Use `--format png` for lossless screenshots.

Inspect preparation and recovery in context, then adjacent frames near contact. Refine contact estimates from ball approach, racket motion and outgoing movement. Use `contact_time: null` for unclear contact or `contact_range` for an uncertainty interval. Account for motion blur, occlusion, other-court balls and background players. A ball projected near the chest does not prove inadequate three-dimensional spacing.

State actual review coverage separately from extracted image counts. Do not claim to have manually assessed every generated frame or the entire video when reviewing selected windows. Millisecond labels locate frames, not millisecond-accurate visual contact measurements.

## Form evidence-backed coaching advice

Read [references/coaching-review.md](references/coaching-review.md) when forming conclusions. Distinguish visible observations, tentative interpretations, unobservable details and suggested practice. Compare similar balls before calling a movement a repeatable fault; preserve good movements as personal examples.

Avoid diagnosing no split-step, no hip rotation, incomplete follow-through or slow recovery from one still. Open stances, bent elbows, natural rising, compact emergency swings and waiting between fed balls are not inherently faults. Grip, torque, exact racket angle, spin and landing positions often need other views or footage.

Adapt practice order to experience and reported problems. Suggest a few observable changes and drills that test them. For newer players, coordination, spacing and repeatability often deserve attention before extra power. Link natural follow-through, racket reset and positional recovery to the next ball. Cite primary coaching sources near relevant advice; do not copy manuals.

Use [assets/report-skeleton.md](assets/report-skeleton.md) as an optional writing guide, not a fixed structure or ready-made diagnosis. Include times, evidence IDs, priorities, practice, actual review scope and limitations. Keep substantial analysis in Markdown so subsequent corrections update the same report.

## Deliver and verify

```text
python -X utf8 <skill-directory>/scripts/analyze.py validate <manifest.json>
python -X utf8 <skill-directory>/scripts/analyze.py render --manifest <manifest.json> --report <report.md> --video <video> --output <report.html>
```

By default, use the original compact comparison-first layout: a small heading, then full-width side-by-side continuous frames and playback controls. Keep the complete written review in the expandable section below; it must not precede the viewer. Optional `intro`, `summary_cards` and `comparison_images` carry footage-specific short guidance and phase boards after the viewer. Follow an explicit request for another layout when given.

Data, CSS and JavaScript are embedded; images and original video remain linked files. Keep the layout intact. Use `--overwrite` for an intentional revision of an existing report.

Original playback reads the source file directly. Do not add music or replace audio. Still images have no sound. This analysis workflow does not produce edited long/highlight videos; if editing was separately requested, complete and verify that task too.

Open local HTML or use `serve --directory <directory-containing-report-and-media>`. The optional local server supports byte-range video seeking. Verify image loading, frame stepping, window selection, contact-relative alignment, playback and any out-of-frame limits using available browser tools. Report unperformed checks honestly.

A local analysis request does not authorize public uploads. Share within the user's actual scope. The `demo` command provides synthetic public examples; do not accidentally publish the player's paths, photos or personal report.
