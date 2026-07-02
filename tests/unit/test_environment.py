"""Smoke test dell'ambiente: verifica che le dipendenze core siano
importabili e minimamente funzionanti. Nessuna logica di dominio."""

import numpy as np


def test_numpy_disponibile():
    assert np.zeros(4).shape == (4,)


def test_soundfile_disponibile():
    import soundfile as sf

    assert hasattr(sf, "write") and hasattr(sf, "read")


def test_yaml_disponibile():
    import yaml

    assert yaml.safe_load("a: 1") == {"a": 1}


def test_resampler_disponibile():
    """soxr preferito; scipy come fallback accettato (D13)."""
    try:
        import soxr  # noqa: F401
    except ImportError:
        from scipy.signal import resample_poly  # noqa: F401


def test_seeding_namespaced_riproducibile():
    """Prototipo della derivazione D14: stesso nome → stessa sequenza,
    nomi diversi → sequenze indipendenti."""
    import hashlib

    def rng_for(seed: int, layer_id: str, component: str) -> np.random.Generator:
        digest = hashlib.sha256(f"{seed}:{layer_id}:{component}".encode()).digest()
        return np.random.default_rng(int.from_bytes(digest[:8], "little"))

    a1 = rng_for(42, "l1", "duration").random(5)
    a2 = rng_for(42, "l1", "duration").random(5)
    b = rng_for(42, "l1", "volume").random(5)

    assert np.array_equal(a1, a2)
    assert not np.array_equal(a1, b)
