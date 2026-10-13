# Workflow / 操作流程

## Before extraction / 取帧前

Read `inspect` metadata. Choose timestamps from the actual file used for review.
For a montage, do not reuse raw-camera times: map them through the edit list or
locate them directly in the edited video. Check continuity and select windows
that retain preparation and recovery, including consecutive shots when useful.

Use `overview` for scouting. Its snapshots are scaled and sparse, so they cannot
establish impact details. Crops in an extraction plan are encoded-source pixels;
omit `crop` for full frames, and use a wider crop for running shots.

先检查参数，再按实际成片定位。概览图用于寻找动作，不用它判断触球细节。
有剪辑表时填写连续区间；没有时保留 `not_checked` 状态并实际核查接点。

## Windows example / Windows 示例

These example paths are generic. Adjust them to your own files:

```powershell
tennis-analysis inspect "C:\Videos\tennis.mp4"
tennis-analysis overview "C:\Videos\tennis.mp4" --output "C:\Reviews\scouting"
tennis-analysis extract "C:\Videos\tennis.mp4" --plan "C:\Reviews\plan.json" --output "C:\Reviews\evidence"
tennis-analysis validate "C:\Reviews\evidence\manifest.json"
tennis-analysis render --manifest "C:\Reviews\evidence\manifest.json" --report "C:\Reviews\review.md" --video "C:\Videos\tennis.mp4" --output "C:\Reviews\review.html"
```

The direct skill script supports the same arguments, using `python -X utf8`.

## Review and refine / 观察与修订

Inspect sequence sheets to understand the complete action, then actual adjacent
frames near estimated contact. Update `contact_time`, optional `contact_range`,
`observation` and `confidence` in the manifest. `null` contacts remain explicit
in the viewer. Keep observations separate from proposed explanations and drills.

Use the optional report-writing guide in the skill's `assets/`. The HTML opens
with the compact continuous-frame comparison. The complete written review is
embedded in an expandable section below the viewer and source-video player.
For later corrections, update the Markdown/manifest and render with `--overwrite`.

先看整段动作，再核对触球附近相邻帧。修正的是观察和估计，不能把拍摄角度
看不见的内容写成确定事实。报告可以保留正手、反拍和连续两拍的对比。

## Playback / 回看

The frame viewer works as a local HTML file; images must remain in their relative
locations. The original video player uses the linked source, not a re-encoded
copy. An optional `serve` command supports byte ranges for large-file seeking.
Serve a directory containing both report and linked media when using HTTP.

If the browser cannot decode the source codec, use the provided original-video
link with a local player. Source-audio preservation means no replacement track;
still screenshots do not contain sound.

## Troubleshooting / 常见问题

| Symptom | Check |
|---|---|
| Missing FFmpeg/ffprobe | Install the tools and verify they are on PATH. |
| Output directory exists | Choose a new extraction directory; old frames must not contaminate timing. |
| Window rejected across cut | Split/reselect the window inside a verified continuous interval. |
| Rotation metadata rejected | Review displayed orientation and crop coordinates; prepare a separate normalized copy only if needed. |
| Broken images | Keep the generated HTML and evidence layout together. |
| Contact unclear | Use `null`, retain context, and avoid a precise-impact claim. |
| HDR preview looks different | Evaluate color/exposure in the original player; the toolkit has no dedicated tone mapping. |

Extraction failures can leave a partial new directory and FFmpeg logs for
inspection. It is not a validated deliverable until a manifest validates.
