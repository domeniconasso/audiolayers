"""Integration — pipeline di render (M5): il YAML dichiarativo arriva
fino al buffer attraverso parametri, strategy di durata e sequenza.
"""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from src.engine.render import render_score

SR = 48000


@pytest.fixture
def pool(tmp_path: Path) -> Path:
    pool_dir = tmp_path / "pool"
    pool_dir.mkdir()
    t = np.arange(SR) / SR
    sf.write(pool_dir / "sine.wav",
             (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), SR)
    return pool_dir


def render(tmp_path: Path, score_text: str) -> np.ndarray:
    score = tmp_path / "score.yaml"
    score.write_text(score_text, encoding="utf-8")
    out = tmp_path / "out.wav"
    render_score(score, out)
    audio, _ = sf.read(str(out), always_2d=True)
    return audio


def test_fill_factor_sotto_uno_lascia_silenzio_tra_i_frammenti(tmp_path, pool):
    audio = render(tmp_path, f"""\
layers:
  - layer_id: "rado"
    duration: 2.0
    pool: "{pool.as_posix()}"
    fill_factor: 0.5          # IOI = 1.0: frammenti a 0.0 e 1.0
    fragment: {{duration: 0.5}}
""")
    assert len(audio) == round(1.5 * SR)  # estensione = 1.0 + 0.5 (D7)
    gap = audio[round(0.6 * SR):round(0.9 * SR)]
    assert np.abs(gap).max() == 0.0      # silenzio vero nel buco
    frag2 = audio[round(1.1 * SR):round(1.4 * SR)]
    assert np.abs(frag2).max() > 0.1     # il secondo frammento suona


def test_seed_fissato_rende_il_render_stocastico_riproducibile(tmp_path, pool):
    score = f"""\
seed: 1234
layers:
  - layer_id: "nuvola"
    duration: 3.0
    pool: "{pool.as_posix()}"
    distribution: 1.0
    volume: -6.0
    volume_range: 6.0
    fragment: {{duration: 0.2, duration_range: 0.1}}
"""
    a = render(tmp_path, score)
    b = render(tmp_path, score)
    assert np.array_equal(a, b)          # bit-identici (D14)


def test_seed_diverso_produce_render_diverso(tmp_path, pool):
    def score(seed):
        return f"""\
seed: {seed}
layers:
  - layer_id: "nuvola"
    duration: 3.0
    pool: "{pool.as_posix()}"
    distribution: 1.0
    fragment: {{duration: 0.2, duration_range: 0.1}}
"""
    a = render(tmp_path, score(1))
    b = render(tmp_path, score(2))
    assert a.shape != b.shape or not np.array_equal(a, b)
