"""Strategy di provisioning del pool (plan 002, D-P4/D-P5/D-P7).

ArchiveDiggerSource analizza il layer e scarica da Internet Archive i
file mancanti via archivedigger (client iniettabile per i test). Senza
--dig il provisioning semplicemente non viene invocato: il pool è una
normale cartella locale, non serve una strategy no-op per dirlo.
"""

from pathlib import Path

from archivedigger.api import dig
from archivedigger.config import Config

from src.audio.pool import count_suitable_files
from src.provisioning.analyzer import analyze_layer

#: Default di ricerca quando la partitura non dice nulla (D-P4).
#: Solo formati che il loader sa leggere: niente mp3.
_DEFAULT_PROVISION = {
    "search": {"license": "cc"},
    "files": {"prefer": [["Flac", "WAVE", "AIFF"]]},
}

#: Giri di ricerca al massimo: a ogni giro max_items raddoppia (D-P5).
_MAX_ROUNDS = 3


class ArchiveDiggerSource:
    """Popola il pool da Internet Archive via archivedigger (D-P7).

    Idempotente: conta i file già idonei e scarica solo la differenza.
    Se Internet Archive non copre il fabbisogno, avvisa e lascia
    proseguire il render (la selezione sequential cicla).
    """

    def __init__(self, client=None):
        self._client = client

    def ensure(self, layer: dict, seed) -> None:
        requirements = analyze_layer(layer, seed)
        pool = Path(layer["pool"])
        pool.mkdir(parents=True, exist_ok=True)

        shortfall = self._shortfall(pool, requirements)
        if shortfall <= 0:
            return

        for round_index in range(_MAX_ROUNDS):
            before = shortfall
            config = self._build_config(layer, requirements, pool,
                                        max_items=shortfall * (2 ** round_index))
            dig(config, client=self._client)
            shortfall = self._shortfall(pool, requirements)
            if shortfall <= 0:
                return
            if shortfall == before:
                break  # nessun progresso: inutile allargare ancora

        print(f"ATTENZIONE: pool '{pool}' ha "
              f"{requirements.files_needed - shortfall} file idonei su "
              f"{requirements.files_needed} richiesti -- il render procede, "
              f"la selezione ciclera' sui file disponibili")

    def _shortfall(self, pool: Path, requirements) -> int:
        suitable = count_suitable_files(
            pool, min_duration=requirements.min_file_duration)
        return requirements.files_needed - suitable

    def _build_config(self, layer: dict, requirements, pool: Path,
                      *, max_items: int) -> Config:
        """Config archivedigger: default ← blocco `provision` del layer,
        con filtri e conteggi calcolati dall'analyzer (non dichiarabili)."""
        provision = layer.get("provision") or {}
        computed = {
            "search": {"max_items": max_items},
            "filters": {
                "min_duration": requirements.min_file_duration,
                "max_duration": requirements.max_file_duration,
                "max_files_per_item": 1,
            },
            "download": {"destdir": str(pool)},
        }
        job: dict = {}
        _merge(job, _DEFAULT_PROVISION)
        _merge(job, provision)
        _merge(job, computed)
        return Config.build(job=job)


def provision_score(score_path, client=None) -> None:
    """Assicura il pool di ogni layer attivo della partitura (flag --dig).

    Il seed dell'analisi è quello della partitura; se assente si usa 0:
    per i layer deterministici non cambia nulla, per quelli casuali il
    conteggio è comunque una fotografia valida quanto un'altra.
    """
    import yaml

    from src.core.layer_plan import active_layers

    data = yaml.safe_load(Path(score_path).read_text(encoding="utf-8"))
    seed = data.get("seed") if data.get("seed") is not None else 0
    source = ArchiveDiggerSource(client=client)
    for layer in active_layers(data["layers"]):
        source.ensure(layer, seed)


def _merge(base: dict, overlay: dict) -> None:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
