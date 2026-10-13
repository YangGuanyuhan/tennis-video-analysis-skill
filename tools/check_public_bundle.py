"""Check the Git index for oversized files, private-data paths and credential strings."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
raw = subprocess.run(["git", "ls-files", "--cached", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
paths = [p.decode("utf-8") for p in raw.split(b"\0") if p]
assert paths, "Stage the public repository before checking the bundle"
errors = []
credentials = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{25,}|AKIA[A-Z0-9]{16})\b")
for path in paths:
    file = ROOT / path
    if file.stat().st_size > 8_000_000:
        errors.append(path + ": unexpectedly large public file")
    if file.suffix.lower() in {".mp4", ".jpg", ".png"}:
        if not (path.startswith("examples/demo/") or path == "docs/images/demo.png"):
            errors.append(path + ": media outside the synthetic example")
    else:
        content = file.read_text(encoding="utf-8", errors="ignore")
        if credentials.search(content):
            errors.append(path + ": possible credential")
        # Keep literal signatures out of the scanner itself.
        signatures = ["C:" + "\\Users\\" + "15235", "VID_" + "20261005", "接球长视频_" + "4K60_原声"]
        if any(s in content for s in signatures):
            errors.append(path + ": private session data")
assert not errors, "\n".join(errors)
print(f"Public bundle: {len(paths)} files checked; no private-session paths, oversized files or credential matches")
