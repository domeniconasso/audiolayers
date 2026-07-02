# audiolayers

Ambiente compositivo dichiarativo per Computer Music. Legge una collezione di
file audio e, seguendo una partitura YAML, dispone frammenti dei file lungo il
tempo — controllando per ciascuno (o per tutti) apertura, punto di lettura,
gain e pan, secondo il modello delle *tendency masks* di Barry Truax
(`base ± range`, entrambi envelope-abili).

## Concetti chiave

- **Layer**: una sequenza indipendente di frammenti; più layer si sommano nel
  mix stereo finale (`solo`/`mute` per layer).
- **fill_factor** (F): governa la spaziatura — `IOI = durata_frammento / F`.
  F=1 concatenazione, F<1 silenzi, F>1 sovrapposizione (con crossfade
  emergenti dagli inviluppi).
- **distribution** ∈ [0,1]: da sincrono (metronomo) ad asincrono (stocastico),
  blend continuo, modello Truax.
- **Riproducibilità**: seed namespaced per componente; seed di sessione
  generato da timestamp e sempre loggato.

## Stato

In sviluppo — vedi [docs/plans/](docs/plans/) per il piano di bootstrap e le
decisioni di design.

## Setup

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows
# .venv/bin/pip install -r requirements.txt     # POSIX
```

## Test

```bash
make tests
# oppure: python -m pytest
```

## Licenza

MIT — vedi [LICENSE](LICENSE).
