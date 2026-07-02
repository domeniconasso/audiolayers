"""Pipeline di rendering: partitura YAML → buffer stereo → file audio.

Dal M5 il layer è cablato sul sistema dichiarativo: parametri con
tendency mask (D5), durate da Strategy (D8), onset da fill_factor +
distribution con stop senza mozzatura (D2, D3, D7), seeding namespaced
con seed di sessione da timestamp sempre loggato (D14).
"""

import time as _time
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

from src.core.fragment_sequence import build_fragment_sequence
from src.parameters.parser import create_layer_parameters
from src.shared.seeding import rng_for
from src.strategies.duration_strategy import build_duration_strategy
from src.strategies.selection_strategy import build_selection_strategy

DEFAULT_SAMPLE_RATE = 48000

AUDIO_EXTENSIONS = (".wav", ".aif", ".aiff", ".flac")


def render_score(score_path: Path, output_path: Path) -> None:
    """Renderizza la partitura e scrive il file di output (WAV float32)."""
    data = yaml.safe_load(Path(score_path).read_text(encoding="utf-8"))
    sample_rate = int(data.get("sample_rate", DEFAULT_SAMPLE_RATE))
    seed = _resolve_seed(data)

    layer_buffers = [
        _render_layer(layer, sample_rate, seed) for layer in data["layers"]
    ]

    total_frames = max(len(buf) for buf in layer_buffers)
    mix = np.zeros((total_frames, 2), dtype=np.float64)
    for buf in layer_buffers:
        mix[: len(buf)] += buf

    sf.write(str(output_path), mix.astype(np.float32), sample_rate,
             subtype="FLOAT")


def _resolve_seed(data: dict):
    """Seed dalla partitura; assente → da timestamp, SEMPRE loggato (D14)."""
    if "seed" in data and data["seed"] is not None:
        return data["seed"]
    seed = _time.time_ns()
    # Solo ASCII nell'output CLI: le console Windows in pipe si strozzano
    # su caratteri non-ASCII (stessa lezione dei messaggi d'errore).
    print(f"seed di sessione (generato): {seed} "
          f"-- aggiungi 'seed: {seed}' alla partitura per riprodurre")
    return seed


def _render_layer(layer: dict, sample_rate: int, seed) -> np.ndarray:
    """Renderizza un layer: sequenza di frammenti → timeline stereo."""
    layer_id = layer.get("layer_id", "layer")
    target_duration = float(layer["duration"])
    time_mode = layer.get("time_mode", "absolute")

    params = create_layer_parameters(
        layer, layer_id=layer_id, duration=target_duration, seed=seed,
        time_mode=time_mode,
    )
    duration_strategy = build_duration_strategy(
        layer.get("fragment", {}), layer_id=layer_id,
        duration=target_duration, seed=seed, time_mode=time_mode,
    )
    fragments = build_fragment_sequence(
        duration_strategy=duration_strategy,
        fill_factor=params["fill_factor"],
        distribution=params["distribution"],
        target_duration=target_duration,
        rng=rng_for(seed, layer_id, "onset"),
    )

    pool_files = _scan_pool(Path(layer["pool"]))
    # Precarica il pool una volta sola (mono, al SR di progetto).
    sources = [_load_mono(p, sample_rate) for p in pool_files]
    selection = build_selection_strategy(
        layer.get("selection", {}), pool_size=len(sources),
        layer_id=layer_id, seed=seed,
    )

    extent = max(f.onset + f.duration for f in fragments)
    buffer = np.zeros((round(extent * sample_rate), 2), dtype=np.float64)

    for index, frag in enumerate(fragments):
        # Quale file suona questo frammento lo decide la Strategy (D6).
        source = sources[selection.select(index)]
        segment = source[: round(frag.duration * sample_rate)]

        # Pan mid/side a 0° (D12): centro → L = R = s/√2.
        start = round(frag.onset * sample_rate)
        end = min(start + len(segment), len(buffer))
        panned = segment[: end - start] / np.sqrt(2.0)
        buffer[start:end, 0] += panned
        buffer[start:end, 1] += panned

    return buffer


def _scan_pool(pool_dir: Path) -> list[Path]:
    """File audio del pool, in ordine alfabetico stabile."""
    files = sorted(
        p for p in pool_dir.iterdir()
        if p.suffix.lower() in AUDIO_EXTENSIONS
    )
    if not files:
        raise FileNotFoundError(f"Nessun file audio nel pool: {pool_dir}")
    return files


def _load_mono(path: Path, sample_rate: int) -> np.ndarray:
    """Carica un file audio come mono float64 al sample rate di progetto."""
    data, file_sr = sf.read(str(path), dtype="float64", always_2d=True)
    if file_sr != sample_rate:
        # Il resampling arriva con M7 (D13): per ora fallire è onesto.
        raise NotImplementedError(
            f"Resampling non ancora supportato: {path} è a {file_sr} Hz, "
            f"il progetto a {sample_rate} Hz"
        )
    return data.mean(axis=1)  # downmix a mono (D12)
