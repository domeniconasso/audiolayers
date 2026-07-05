"""Avvio GUI: python -m audiolayers.web [--port 8000]."""

import argparse

from audiolayers.web.app import create_app

parser = argparse.ArgumentParser(prog="audiolayers-gui")
parser.add_argument("--port", type=int, default=8000)
args = parser.parse_args()

print(f"audiolayers GUI su http://localhost:{args.port}")
create_app(output_dir=None).run(port=args.port, debug=False)
