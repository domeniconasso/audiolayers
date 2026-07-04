"""Unit — strategy di provisioning del pool (plan 002, D-P4/D-P5/D-P7).

Il pool può essere una semplice cartella locale (default) o venire
popolato da Internet Archive via archivedigger. La strategy è idempotente:
conta i file già idonei e scarica solo la differenza.
"""

import numpy as np
import soundfile as sf
from archivedigger.models import IAFile, IAItem

from src.audio.pool import count_suitable_files
from src.provisioning.pool_source import ArchiveDiggerSource


def write_wav(path, seconds, sample_rate=48000):
    frames = round(seconds * sample_rate)
    sf.write(str(path), np.zeros(frames, dtype=np.float32), sample_rate)


class FakeArchiveClient:
    """Client Internet Archive finto: cataloghi in memoria, download che
    scrive wav reali. Registra query e max_items ricevuti."""

    def __init__(self, n_items=50, length=5.0):
        self._length = length
        self._ids = [f"item-{i:03d}" for i in range(n_items)]
        self.queries: list[str] = []
        self.max_items_seen: list[int] = []

    def search(self, query, sort="downloads desc", max_items=100):
        self.queries.append(query)
        self.max_items_seen.append(max_items)
        yield from self._ids[:max_items]

    def get_item(self, identifier):
        file = IAFile(name=f"{identifier}.wav", format="WAVE",
                      size=1000, length=self._length, source="original")
        return IAItem(identifier=identifier, metadata={}, files=[file])

    def download_file(self, item, file, local_path):
        local_path.parent.mkdir(parents=True, exist_ok=True)
        write_wav(local_path, self._length)


DET_LAYER = {
    "layer_id": "det",
    "duration": 2.0,
    "fill_factor": 1.0,
    "fragment": {"duration": 0.5},
}


class TestArchiveDiggerSource:
    def test_pool_vuoto_scarica_un_file_per_frammento(self, tmp_path):
        """Layer da 4 frammenti, pool vuoto → 4 file idonei scaricati."""
        pool = tmp_path / "pool"
        layer = dict(DET_LAYER, pool=str(pool))
        client = FakeArchiveClient()
        ArchiveDiggerSource(client=client).ensure(layer, seed=1)
        assert count_suitable_files(pool, min_duration=0.5) == 4

    def test_pool_gia_pieno_non_tocca_internet_archive(self, tmp_path):
        """Idempotenza (D-P5): file idonei già sufficienti → zero ricerche."""
        pool = tmp_path / "pool"
        pool.mkdir()
        for i in range(4):
            write_wav(pool / f"gia_{i}.wav", 2.0)
        layer = dict(DET_LAYER, pool=str(pool))
        client = FakeArchiveClient()
        ArchiveDiggerSource(client=client).ensure(layer, seed=1)
        assert client.queries == []

    def test_pool_parziale_chiede_solo_la_differenza(self, tmp_path):
        """3 file idonei su 4 → alla ricerca si chiede 1 solo item."""
        pool = tmp_path / "pool"
        pool.mkdir()
        for i in range(3):
            write_wav(pool / f"gia_{i}.wav", 2.0)
        layer = dict(DET_LAYER, pool=str(pool))
        client = FakeArchiveClient()
        ArchiveDiggerSource(client=client).ensure(layer, seed=1)
        assert client.max_items_seen[0] == 1
        assert count_suitable_files(pool, min_duration=0.5) == 4

    def test_blocco_provision_finisce_nella_query(self, tmp_path):
        """La partitura orienta la ricerca; senza blocco valgono i default
        (license cc). La collection dichiarata deve comparire nella query."""
        layer = dict(DET_LAYER, pool=str(tmp_path / "pool"),
                     provision={"search": {"collection": ["field-recordings"]}})
        client = FakeArchiveClient()
        ArchiveDiggerSource(client=client).ensure(layer, seed=1)
        assert "field-recordings" in client.queries[0]
        assert "license" in client.queries[0].lower()

    def test_archivio_insufficiente_avvisa_e_non_cicla_per_sempre(
            self, tmp_path, capsys):
        """Solo 2 item disponibili per 4 frammenti → warning esplicito,
        il metodo termina e il pool tiene quello che c'è."""
        pool = tmp_path / "pool"
        layer = dict(DET_LAYER, pool=str(pool))
        client = FakeArchiveClient(n_items=2)
        ArchiveDiggerSource(client=client).ensure(layer, seed=1)
        assert count_suitable_files(pool, min_duration=0.5) == 2
        assert "ATTENZIONE" in capsys.readouterr().out


class FakeArchiveClient:
    """Client Internet Archive finto: cataloghi in memoria, download che
    scrive wav reali. Registra query e max_items ricevuti."""

    def __init__(self, n_items=50, length=5.0):
        self._length = length
        self._ids = [f"item-{i:03d}" for i in range(n_items)]
        self.queries: list[str] = []
        self.max_items_seen: list[int] = []

    def search(self, query, sort="downloads desc", max_items=100):
        self.queries.append(query)
        self.max_items_seen.append(max_items)
        yield from self._ids[:max_items]

    def get_item(self, identifier):
        file = IAFile(name=f"{identifier}.wav", format="WAVE",
                      size=1000, length=self._length, source="original")
        return IAItem(identifier=identifier, metadata={}, files=[file])

    def download_file(self, item, file, local_path):
        local_path.parent.mkdir(parents=True, exist_ok=True)
        write_wav(local_path, self._length)


DET_LAYER = {
    "layer_id": "det",
    "duration": 2.0,
    "fill_factor": 1.0,
    "fragment": {"duration": 0.5},
}


class TestArchiveDiggerSource:
    def test_pool_vuoto_scarica_un_file_per_frammento(self, tmp_path):
        """Layer da 4 frammenti, pool vuoto → 4 file idonei scaricati."""
        pool = tmp_path / "pool"
        layer = dict(DET_LAYER, pool=str(pool))
        client = FakeArchiveClient()
        ArchiveDiggerSource(client=client).ensure(layer, seed=1)
        assert count_suitable_files(pool, min_duration=0.5) == 4

    def test_pool_gia_pieno_non_tocca_internet_archive(self, tmp_path):
        """Idempotenza (D-P5): file idonei già sufficienti → zero ricerche."""
        pool = tmp_path / "pool"
        pool.mkdir()
        for i in range(4):
            write_wav(pool / f"gia_{i}.wav", 2.0)
        layer = dict(DET_LAYER, pool=str(pool))
        client = FakeArchiveClient()
        ArchiveDiggerSource(client=client).ensure(layer, seed=1)
        assert client.queries == []

    def test_pool_parziale_chiede_solo_la_differenza(self, tmp_path):
        """3 file idonei su 4 → alla ricerca si chiede 1 solo item."""
        pool = tmp_path / "pool"
        pool.mkdir()
        for i in range(3):
            write_wav(pool / f"gia_{i}.wav", 2.0)
        layer = dict(DET_LAYER, pool=str(pool))
        client = FakeArchiveClient()
        ArchiveDiggerSource(client=client).ensure(layer, seed=1)
        assert client.max_items_seen[0] == 1
        assert count_suitable_files(pool, min_duration=0.5) == 4

    def test_blocco_provision_finisce_nella_query(self, tmp_path):
        """La partitura orienta la ricerca; senza blocco valgono i default
        (license cc). La collection dichiarata deve comparire nella query."""
        layer = dict(DET_LAYER, pool=str(tmp_path / "pool"),
                     provision={"search": {"collection": ["field-recordings"]}})
        client = FakeArchiveClient()
        ArchiveDiggerSource(client=client).ensure(layer, seed=1)
        assert "field-recordings" in client.queries[0]
        assert "license" in client.queries[0].lower()

    def test_archivio_insufficiente_avvisa_e_non_cicla_per_sempre(
            self, tmp_path, capsys):
        """Solo 2 item disponibili per 4 frammenti → warning esplicito,
        il metodo termina e il pool tiene quello che c'è."""
        pool = tmp_path / "pool"
        layer = dict(DET_LAYER, pool=str(pool))
        client = FakeArchiveClient(n_items=2)
        ArchiveDiggerSource(client=client).ensure(layer, seed=1)
        assert count_suitable_files(pool, min_duration=0.5) == 2
        assert "ATTENZIONE" in capsys.readouterr().out


class TestCountSuitableFiles:
    def test_conta_solo_i_file_abbastanza_lunghi(self, tmp_path):
        write_wav(tmp_path / "corto.wav", 0.2)
        write_wav(tmp_path / "lungo.wav", 2.0)
        write_wav(tmp_path / "esatto.wav", 1.0)
        (tmp_path / "non_audio.txt").write_text("x")
        assert count_suitable_files(tmp_path, min_duration=1.0) == 2

    def test_cartella_mancante_conta_zero(self, tmp_path):
        assert count_suitable_files(tmp_path / "inesistente",
                                    min_duration=1.0) == 0
