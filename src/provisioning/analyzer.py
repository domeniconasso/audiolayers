"""Analyzer dei requisiti di pool (plan 002, D-P2/D-P3).

Non stima: costruisce lo stesso LayerPlan del render (stesse Strategy,
stesso seed namespaced), quindi il conteggio e la durata massima
coincidono con quello che il render produrrà.
"""

from dataclasses import dataclass

from src.core.layer_plan import build_layer_plan

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
    fragments = build_layer_plan(layer, seed).fragments
    return PoolRequirements(
        files_needed=len(fragments),
        min_file_duration=max(f.duration for f in fragments),
        max_file_duration=MAX_FILE_DURATION,
    )
