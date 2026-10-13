"""Build a portable skill ZIP with license, without runtime caches or private data."""
import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "tennis-video-analysis" / "scripts"))
from tennis_analysis import __version__
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=ROOT / "dist" / f"tennis-video-analysis-{__version__}.zip")
args = parser.parse_args()
output = args.output.resolve()
source = ROOT / "skills" / "tennis-video-analysis"
if output.is_relative_to(source):
    parser.error("ZIP output must be outside the skill source")
output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(source.rglob("*")):
        relative = file.relative_to(source)
        if file.is_file() and "__pycache__" not in relative.parts and not any(p.endswith('.egg-info') for p in relative.parts) and file.suffix != ".pyc":
            archive.write(file, "tennis-video-analysis/" + relative.as_posix())
    archive.write(ROOT / "LICENSE", "tennis-video-analysis/LICENSE")
print(output)
