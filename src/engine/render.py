"""Pipeline di rendering: partitura YAML → buffer stereo → file audio.

Walking skeleton (M1): caso deterministico — selezione sequenziale,
durata frammento fissa, fill_factor, nessuna componente stocastica.
"""

from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

DEFAULT_SAMPLE_RATE = 48000

AUDIO_EXTENSIONS = (".wav", ".aif", ".aiff", ".flac")


def render_score(score_path: Path, output_path: Path) -> None:
    """Renderizza la partitura e scrive il file di output (WAV float32)."""
    data = yaml.safe_load(Path(score_path).read_text(encoding="utf-8"))
    sample_rate = int(data.get("sample_rate", DEFAULT_SAMPLE_RATE))

    layer_buffers = [
        _render_layer(layer, sample_rate) for layer in data["layers"]
    ]

    total_frames = max(len(buf) for buf in layer_buffers)
    mix = np.zeros((total_frames, 2), dtype=np.float64)
    for buf in layer_buffers:
        mix[: len(buf)] += buf

    sf.write(str(output_path), mix.astype(np.float32), sample_rate,
             subtype="FLOAT")


def _render_layer(layer: dict, sample_rate: int) -> np.ndarray:
    """Renderizza un layer: dispone i frammenti sulla timeline stereo."""
    target_duration = float(layer["duration"])
    fragment_duration = float(layer["fragment"]["duration"])
    fill_factor = float(layer.get("fill_factor", 1.0))

    pool_files = _scan_pool(Path(layer["pool"]))

    # Onset da fill_factor (D2): IOI = durata_frammento / F.
    # Stop (D7): ci si ferma quando il prossimo onset supererebbe la
    # durata-obiettivo; l'ultimo frammento suona per intero.
    onsets = []
    t = 0.0
    while t < target_duration:
        onsets.append(t)
        t += fragment_duration / fill_factor

    fragment_frames = round(fragment_duration * sample_rate)
    total_frames = round(onsets[-1] * sample_rate) + fragment_frames
    buffer = np.zeros((total_frames, 2), dtype=np.float64)

    for index, onset in enumerate(onsets):
        # Selezione sequenziale (D6): i file del pool in ordine, ciclando.
        source = _load_mono(pool_files[index % len(pool_files)], sample_rate)
        segment = source[:fragment_frames]

        # Pan mid/side a 0° (D12): centro → L = R = s/√2.
        start = round(onset * sample_rate)
        left = right = segment / np.sqrt(2.0)
        buffer[start:start + len(segment), 0] += left
        buffer[start:start + len(segment), 1] += right

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
