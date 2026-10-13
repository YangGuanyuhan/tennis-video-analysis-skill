# Contributing / 贡献

Install with `python -m pip install -e ".[dev]"`, ensure FFmpeg/ffprobe are on PATH,
then run `python -m pytest -q` and `python tools/validate_skill.py`.

Preserve these invariants:

- Do not rewrite source video/audio or synthesize constant-rate evidence.
- Keep timestamps tied to actual decoded frames and reject known cross-cut windows.
- Keep unknown contact and unchecked continuity explicit.
- Separate visual coaching from deterministic media handling.
- Include useful behavior tests for changes involving timing, preservation or rendering.
- Keep generated reports local and offline; use synthetic assets for public examples.

Describe the observable problem, change and validation in a pull request. For bugs,
include platform, Python/FFmpeg versions, commands and a minimal synthetic example.
Avoid uploading private footage or logs containing personal file paths.

贡献时请保留实际帧时间、原视频和原声；把人工动作判断与工具取帧分开。
提交说明写清问题、变化和验证方式。尽量用生成素材复现，不上传私人影像。
