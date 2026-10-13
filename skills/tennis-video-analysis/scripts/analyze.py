"""Run without package installation: python -X utf8 scripts/analyze.py --help."""
from tennis_analysis.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
