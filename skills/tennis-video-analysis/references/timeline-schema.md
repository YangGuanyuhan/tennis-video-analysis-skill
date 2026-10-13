# Timeline and evidence schema

Times are seconds on the input file's seek/playback timeline, not wall-clock times or camera times before montage editing. Verify unusual start timestamps against the actual source player. Use presentation timing, not frame numbers multiplied by a nominal period.

## Plan, version 1

```json
{
  "version": 1,
  "title": "My tennis review",
  "language": "en",
  "profile": {"experience_months": 3},
  "continuous_segments": [{"id": "clip-1", "start": 0, "end": 10}],
  "windows": [{
    "id": "S01", "start": 2.4, "end": 6.8,
    "contact_time": 4.1, "contact_range": [4.07, 4.13],
    "crop": [600, 400, 1600, 1100],
    "kind": "Forehand",
    "observation": "Write after viewing consecutive frames.",
    "confidence": "medium"
  }]
}
```

- Required: `version`, nonempty `windows`, safe unique window `id`, `start`, `end`. Bounds are `[start, end)` and must fit the source.
- `crop`: `[x,y,width,height]`, integer encoded-source pixels, without scaling. Omit for full frames. Adapt the example to actual dimensions.
- `contact_time`: optional or `null` when unconfirmed. Optional `contact_range` must contain the estimate when present.
- `continuous_segments`: optional, nonoverlapping verified intervals. A window must fit one interval. Do not claim a montage is continuous by declaring a whole-video interval.
- `language`: `zh` or `en`, for the interface. The report retains its written language.
- Notes and profile are human-authored context, not automated scores.
- Optional presentation fields: `intro` (brief text), `summary_cards` (`title`/`text` objects), and `comparison_images` (`src`/`alt` objects referencing local images beside the manifest). These appear around or after the primary frame viewer; the full written report expands below. Image references must exist when rendering.

## Manifest

`manifest.json` records source dimensions, nominal/average fps, audio metadata, window bounds/crops, cut-check status and ordered `frames` with `{time,src}`. Image paths are relative to its directory. Scaled sequence/contact sheets accompany each window. `observations.csv` uses UTF-8 with BOM.

`validate` checks finite increasing times, bounds, existing frame files, paths and declared cut verification. It does not establish visual completeness, correct subject selection, exact contact or audio synchrony.

Extraction uses `trim` before `showinfo`, PTS ticks/time base and `-fps_mode passthrough`. Every logged frame must correspond to one saved image. Filtering the interval before logging avoids version-dependent extra frames at an output-duration gate. Fractional seeks can round to a stream time-base tick. See [showinfo](https://ffmpeg.org/ffmpeg-filters.html#showinfo) and [FFmpeg options](https://ffmpeg.org/ffmpeg.html).

## Import old evidence

`import-legacy` accepts an older list containing `id`, `start`, `end`, `crop`, `frame_times`, optional `contact_estimate`/`time`, `note`, `kind` and `contact_uncertain`. It reuses `<id>/frames/*.jpg`. Keep the imported manifest beside the original index; cut verification remains `not_checked` until boundaries are supplied and validated.

## Media preservation and limits

Sources are read-only. Extraction checks file size/mtime; integration tests additionally compare source-byte hashes. Screenshots have no audio; `--video` links the original video/audio to the report. JPEG previews are compressed; PNG retains decoded screenshot pixels. Neither modifies the source file.

Metadata rotation is currently rejected to prevent silently changing crop coordinates. HDR screenshot conversion has no dedicated tone-mapping pipeline; inspect source playback for color/exposure-sensitive work. These helpers support visual stroke review, not measurement-grade biomechanics.
