"""GUI web di audiolayers: Flask minimale sopra il motore.

Factory `create_app` con dipendenze iniettabili (client Internet Archive
per --dig, cartella output): i test girano offline, la CLI `python -m
src.web` usa i default veri. Il render gira come job in background
(JobManager) e la GUI fa polling.
"""

import tempfile
from pathlib import Path

import yaml
from flask import Flask, jsonify, request, send_file

from src.web.jobs import JobManager
from src.web.score_builder import build_score, parse_score

STATIC_DIR = Path(__file__).parent / "static"


def create_app(*, output_dir: Path | None = None,
               archive_client=None) -> Flask:
    app = Flask("audiolayers_gui", static_folder=str(STATIC_DIR),
                static_url_path="/static")
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="audiolayers_gui_"))
    out.mkdir(parents=True, exist_ok=True)
    jobs = JobManager()

    @app.get("/")
    def index():
        return send_file(STATIC_DIR / "index.html")

    @app.post("/api/render")
    def render():
        payload = request.get_json(force=True)
        score = build_score(payload["state"])
        dig = bool(payload.get("dig"))

        def runner():
            score_path = out / "score.yaml"
            score_path.write_text(
                yaml.safe_dump(score, sort_keys=False, allow_unicode=True),
                encoding="utf-8")
            if dig:
                from src.provisioning.pool_source import provision_score
                provision_score(score_path, client=archive_client)
            from src.engine.render import render_score
            wav_path = out / "render.wav"
            render_score(score_path, wav_path)
            return wav_path

        return jsonify({"job_id": jobs.submit(runner)})

    @app.get("/api/jobs/<job_id>")
    def job_status(job_id):
        return jsonify(jobs.status(job_id))

    @app.get("/api/jobs/<job_id>/audio")
    def job_audio(job_id):
        return send_file(jobs.result(job_id), mimetype="audio/wav")

    @app.post("/api/yaml")
    def export_yaml():
        score = build_score(request.get_json(force=True)["state"])
        text = yaml.safe_dump(score, sort_keys=False, allow_unicode=True)
        return text, 200, {"Content-Type": "text/yaml; charset=utf-8"}

    @app.post("/api/import")
    def import_yaml():
        score = yaml.safe_load(request.get_data(as_text=True))
        return jsonify(parse_score(score))

    return app
