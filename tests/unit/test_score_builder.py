"""Unit — score_builder della GUI web: stato dei controlli ↔ partitura.

Ogni controllo è {enabled, value}; disattivato → la chiave non compare
nello YAML e il motore usa i suoi default. I percorsi sono in dot
notation (fragment.duration, pointer.start, selection.strategy).
"""

from src.web.score_builder import build_score, parse_score


def stato_minimo():
    return {
        "global": {
            "seed": {"enabled": True, "value": 42},
            "master_volume": {"enabled": False, "value": -6.0},
        },
        "layers": [{
            "layer_id": "uno",
            "pool": "audio/pool/",
            "params": {
                "duration": {"enabled": True, "value": 20.0},
                "fragment.duration": {"enabled": True, "value": 0.05},
                "volume": {"enabled": False, "value": -3.0},
            },
        }],
    }


class TestBuildScore:
    def test_parametri_attivi_entrano_disattivi_spariscono(self):
        score = build_score(stato_minimo())
        assert score["seed"] == 42
        assert "master_volume" not in score
        layer = score["layers"][0]
        assert layer["layer_id"] == "uno"
        assert layer["pool"] == "audio/pool/"
        assert layer["duration"] == 20.0
        assert layer["fragment"]["duration"] == 0.05
        assert "volume" not in layer

    def test_envelope_breakpoint_passa_come_lista(self):
        stato = stato_minimo()
        stato["layers"][0]["params"]["fragment.duration"]["value"] = \
            [[0, 0.01], [20, 0.5]]
        layer = build_score(stato)["layers"][0]
        assert layer["fragment"]["duration"] == [[0, 0.01], [20, 0.5]]


class TestParseScore:
    def test_round_trip_partitura_torna_nei_controlli(self):
        score = build_score(stato_minimo())
        stato = parse_score(score)
        assert stato["global"]["seed"] == {"enabled": True, "value": 42}
        params = stato["layers"][0]["params"]
        assert params["duration"] == {"enabled": True, "value": 20.0}
        assert params["fragment.duration"]["value"] == 0.05
        assert "volume" not in params or not params["volume"]["enabled"]
