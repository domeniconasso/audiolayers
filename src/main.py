"""CLI di audiolayers: renderizza una partitura YAML in un file audio.

Uso: python -m src.main SCORE.yaml -o OUT.wav
"""

import argparse
from pathlib import Path

from src.engine.render import render_score


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="audiolayers",
        description="Renderizza una partitura YAML in un file audio.",
    )
    parser.add_argument("score", type=Path, help="partitura YAML")
    parser.add_argument("-o", "--output", type=Path, required=True,
                        help="file audio di output")
    args = parser.parse_args(argv)

    render_score(args.score, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
