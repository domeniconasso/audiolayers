"""Analyzer dei requisiti di pool (plan 002, D-P2/D-P3).

Non stima: replica esattamente la costruzione della sequenza di frammenti
del render (stesse Strategy, stesso seed namespaced), quindi il conteggio
e la durata massima coincidono con quello che il render produrrà.
"""

from dataclasses import dataclass

from src.core.fragment_sequence import build_fragment_sequence
from src.parameters.parser import create_layer_parameters
from src.shared.seeding import rng_for
from src.strategies.duration_strategy import build_duration_strategy

#: Tetto (secondi) alla durata dei file da scaricare (D-P3, per ora fisso).
MAX_FILE_DURATION = 10.0


@dataclass(frozen=True)
class PoolRequirements:
    """Cosa serve al pool perché il layer suoni come da partitura."""

    files_needed: int
    min_file_duration: float
    max_file_duration: float


def analyze_layer(layer: dict, seed) -> PoolRequirements:
    """Requisiti di pool per un layer: 1 file per frammento (D-P2),
    ogni file lungo almeno quanto il frammento più lungo (D-P3)."""
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
    return PoolRequirements(
        files_needed=len(fragments),
        min_file_duration=max(f.duration for f in fragments),
        max_file_duration=MAX_FILE_DURATION,
    )
