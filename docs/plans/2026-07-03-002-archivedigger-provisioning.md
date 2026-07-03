# Plan 002 — Provisioning automatico del pool via archivedigger

Data: 2026-07-03 · Branch: `feat/archivedigger-provisioning`

## Obiettivo

`python -m src.main score.yaml -o out.wav --dig` analizza la partitura,
scarica da Internet Archive i file che mancano al pool (via archivedigger
come libreria) e poi renderizza. Senza `--dig` il comportamento resta
identico a oggi: il pool è una cartella locale.

## Decisioni (dal grill 2026-07-03)

- **D-P1** Partitura di riferimento: `scores/stream-crescente.yaml` — un
  layer, 60 s, `fill_factor 1.0`, `distribution 0.0`, `selection
  sequential`, `fragment.duration` envelope lineare 1 ms → 1 s.
- **D-P2** Criterio "abbastanza file": 1 file per frammento stimato
  (nessun riuso). Modalità alternative → issue dedicata.
- **D-P3** Durate richieste ai sorgenti: `min_duration` = durata massima
  di frammento raggiunta dall'envelope (+ range); `max_duration` = 10 s
  fisso per ora. Automazione dei margini → stessa issue.
- **D-P4** Provisioning **opzionale**: si attiva solo col flag `--dig`.
  Config di ricerca dal blocco `provision:` del layer se presente,
  altrimenti default (license `cc`, prefer `[Flac, WAVE, AIFF]` — il
  loader non legge mp3).
- **D-P5** Idempotente: conta i file idonei già nel pool, scarica solo la
  differenza. Se Internet Archive non copre il fabbisogno: warning
  chiaro, il render parte comunque (sequential cicla).
- **D-P6** Dipendenza: `archivedigger @ git+https://github.com/MU-prj/archivedigger`
  in `requirements.txt`.
- **D-P7** Architettura a strategy: `PoolSource` con varianti
  `LocalPoolSource` (no-op, default) e `ArchiveDiggerSource` (analizza +
  scarica). Il client Internet Archive è iniettabile (fake nei test,
  come previsto da `archivedigger.api`).

## Moduli

```
src/provisioning/
  analyzer.py      # PoolRequirements: min/max durata file, n. file necessari
  pool_source.py   # strategy LocalPoolSource / ArchiveDiggerSource + factory
```

- `analyzer`: valuta l'envelope di `fragment.duration` (+`_range`) sulla
  durata del layer → durata massima frammento; integra le durate base con
  `fill_factor` → stima del numero di frammenti (= file necessari, D-P2).
- `pool_source`: `ArchiveDiggerSource` costruisce `archivedigger.Config`
  (blocco `provision` del layer stratificato sui default, filtri e
  `max_items` iniettati dall'analyzer, `destdir` = pool) e chiama `dig()`.
- `main.py`: flag `--dig`; per ogni layer attivo esegue la strategy prima
  di `render_score`.

## Test (TDD, red-green-refactor)

- unit: analyzer (max envelope con/senza range, conteggio frammenti,
  layer deterministico della partitura di riferimento ≈ 120 file);
- unit: mapping blocco `provision` → `Config` (default, override, filtri
  calcolati, formati lossless);
- unit: idempotenza (pool parzialmente pieno → scarica solo shortfall;
  pool pieno → nessuna chiamata a `dig`);
- integration: `--dig` end-to-end con client fake che "scarica" wav
  sintetici nel pool → il wav di output esiste.

## Fuori scope (issue)

Selezione della modalità "quanti file" (per-frammento / soglia / fisso),
automazione margini min/max, ponte generico audiolayers↔archivedigger.
