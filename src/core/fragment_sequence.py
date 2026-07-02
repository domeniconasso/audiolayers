"""Costruzione della sequenza di frammenti (M5): onset + durata.

Il modello (D2, D3, D7):
- durata del frammento i → DurationStrategy (tendency o rhythmic)
- IOI sincrono = durata / fill_factor(t)
- `distribution` (Truax): 0 = metronomo, 1 = async uniforme 0..2×IOI,
  valori intermedi = miscela lineare
- stop: quando il prossimo onset supererebbe la durata-obiettivo;
  l'ultimo frammento suona per intero (mai mozzato)

La costruzione è sinistra→destra: gli envelope dei parametri sono
campionati al tempo di posa di ciascun frammento.
"""

from dataclasses import dataclass

from src.parameters.parameter import Parameter
from src.strategies.duration_strategy import DurationStrategy


@dataclass(frozen=True)
class FragmentSpec:
    """Un frammento posato sulla timeline: quando e per quanto."""

    onset: float
    duration: float


def build_fragment_sequence(*, duration_strategy: DurationStrategy,
                            fill_factor: Parameter,
                            distribution: Parameter,
                            target_duration: float,
                            rng) -> list[FragmentSpec]:
    """Genera la sequenza di FragmentSpec per un layer."""
    fragments: list[FragmentSpec] = []
    t = 0.0
    index = 0
    while t < target_duration:
        dur = duration_strategy.duration(index, t)
        fragments.append(FragmentSpec(onset=t, duration=dur))

        ioi_sync = dur / fill_factor.get_value(t)
        d = distribution.get_value(t)
        if d > 0.0:
            ioi_async = rng.uniform(0.0, 2.0 * ioi_sync)
            ioi = (1.0 - d) * ioi_sync + d * ioi_async
        else:
            ioi = ioi_sync

        t += ioi
        index += 1
    return fragments
