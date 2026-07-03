"""Unit — analyzer dei requisiti di pool (plan 002, D-P2/D-P3).

L'analyzer replica la costruzione della sequenza di frammenti del render
(stesso seed, stesso namespacing) e ne ricava i requisiti per il pool:
quanti file servono e quanto devono durare.
"""

import pytest

from src.provisioning.analyzer import analyze_layer


class TestAnalyzeLayer:
    def test_layer_deterministico_conta_frammenti_e_durata_massima(self):
        """duration 2 s, frammenti fissi da 0.5 s back-to-back → 4 file,
        ogni file deve durare almeno 0.5 s."""
        layer = {
            "layer_id": "det",
            "duration": 2.0,
            "fill_factor": 1.0,
            "fragment": {"duration": 0.5},
        }
        req = analyze_layer(layer, seed=1)
        assert req.files_needed == 4
        assert req.min_file_duration == pytest.approx(0.5)
