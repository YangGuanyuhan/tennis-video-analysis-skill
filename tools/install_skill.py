"""Install a standalone skill without overwriting an existing installation."""
import argparse
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--skills-dir", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills")
args = parser.parse_args()
parent = args.skills_dir.resolve()
target = (parent / "tennis-video-analysis").resolve()
if not target.is_relative_to(parent) or target.exists():
    parser.error("Skill already exists or target is unsafe; choose a different skills directory")
source = ROOT / "skills" / "tennis-video-analysis"
if not (source / "SKILL.md").is_file():
    parser.error("SKILL.md is missing")
parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"))
shutil.copy2(ROOT / "LICENSE", target / "LICENSE")
print(target)
