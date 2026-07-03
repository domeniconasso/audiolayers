"""Integration — API della GUI: render asincrono end-to-end, YAML I/O.

Motore vero su partiture minuscole; Internet Archive finto (il client è
iniettabile nella factory, come in CLI e archivedigger).
"""

import time

import yaml

from src.web.app import create_app
from tests.unit.test_pool_source import FakeArchiveClient, write_wav


def make_state(pool, duration=1.0):
    return {
        "global": {"seed": {"enabled": True, "value": 7}},
        "layers": [{
            "layer_id": "uno",
            "pool": str(pool),
            "params": {
                "duration": {"enabled": True, "value": duration},
                "fragment.duration": {"enabled": True, "value": 0.25},
            },
        }],
    }


def wait_done(client, job_id, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = client.get(f"/api/jobs/{job_id}").get_json()
        if status["state"] in ("done", "error"):
            return status
        time.sleep(0.05)
    raise AssertionError("job mai terminato")


class TestWebApi:
    def test_render_asincrono_produce_wav_scaricabile(self, tmp_path):
        pool = tmp_path / "pool"
        pool.mkdir()
        write_wav(pool / "a.wav", 1.0)
        app = create_app(output_dir=tmp_path / "out")
        client = app.test_client()

        job_id = client.post("/api/render",
                             json={"state": make_state(pool)}).get_json()["job_id"]
        assert wait_done(client, job_id)["state"] == "done"

        audio = client.get(f"/api/jobs/{job_id}/audio")
        assert audio.status_code == 200
        assert audio.data[:4] == b"RIFF"

    def test_render_con_dig_popola_il_pool(self, tmp_path):
        pool = tmp_path / "pool"
        app = create_app(output_dir=tmp_path / "out",
                         archive_client=FakeArchiveClient())
        client = app.test_client()
        job_id = client.post("/api/render",
                             json={"state": make_state(pool), "dig": True}
                             ).get_json()["job_id"]
        assert wait_done(client, job_id)["state"] == "done"
        assert list(pool.glob("*.wav"))

    def test_errore_del_render_arriva_alla_gui(self, tmp_path):
        app = create_app(output_dir=tmp_path / "out")
        client = app.test_client()
        job_id = client.post("/api/render",
                             json={"state": make_state(tmp_path / "vuoto")}
                             ).get_json()["job_id"]
        status = wait_done(client, job_id)
        assert status["state"] == "error"
        assert status["detail"]

    def test_yaml_export_e_import_round_trip(self, tmp_path):
        app = create_app(output_dir=tmp_path / "out")
        client = app.test_client()
        state = make_state(tmp_path / "pool")

        exported = client.post("/api/yaml", json={"state": state}).data.decode()
        assert yaml.safe_load(exported)["layers"][0]["fragment"]["duration"] == 0.25

        imported = client.post("/api/import", data=exported,
                               content_type="text/yaml").get_json()
        assert imported["layers"][0]["params"]["fragment.duration"]["value"] == 0.25

    def test_root_serve_la_pagina(self, tmp_path):
        app = create_app(output_dir=tmp_path / "out")
        response = app.test_client().get("/")
        assert response.status_code == 200
        assert b"audiolayers" in response.data.lower()
