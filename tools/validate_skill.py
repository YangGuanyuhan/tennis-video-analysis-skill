"""Portable skill structure and reference validation for CI."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "tennis-video-analysis"
text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
assert text.startswith("---\n"), "Missing frontmatter"
front = yaml.safe_load(text.split("---", 2)[1])
assert front["name"] == SKILL.name
assert isinstance(front["description"], str) and len(front["description"]) > 20
assert not re.search(r"\bTODO\b|\[TODO", text), "Unfinished scaffold"
for target in re.findall(r"\]\(([^)]+)\)", text):
    if not target.startswith("http"):
        assert (SKILL / target).is_file(), f"Missing reference: {target}"
ui = yaml.safe_load((SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8"))
assert "$" + front["name"] in ui["interface"]["default_prompt"]
assert 25 <= len(ui["interface"]["short_description"]) <= 64
assert (SKILL / "scripts" / "analyze.py").is_file()
print("Skill frontmatter, UI metadata and referenced resources: PASS")
