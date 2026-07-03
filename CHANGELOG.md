# Changelog

Tutte le modifiche rilevanti di audiolayers, nel formato
[Keep a Changelog](https://keepachangelog.com/it/1.1.0/). Il progetto
segue il versionamento semantico.

## [Unreleased]

### Added

- Flag `--dig`: provisioning automatico del pool da Internet Archive via
  [archivedigger](https://github.com/MU-prj/archivedigger). Analizza la
  partitura (stessa sequenza di frammenti del render, stesso seed),
  ricava quanti file servono e le durate min/max richieste, scarica solo
  lo shortfall (idempotente) e poi renderizza. Blocco opzionale
  `provision` nel layer per orientare la ricerca; senza blocco default
  lossless + licenza `cc`.
- Partitura d'esempio `scores/stream-crescente.yaml`: stream singolo
  back-to-back con durate dei frammenti in envelope da 1 ms a 1 s su 60 s.
- Modulo condiviso `src/core/layer_plan.py`: render e analyzer assemblano
  la sequenza di frammenti nello stesso punto (niente divergenze).

## [1.0.0] — 2026-07-02

Bootstrap completo (M1–M10): motore dichiarativo YAML, tendency mask,
envelope, strategies (durata, selezione, overflow, inviluppo), pan
mid/side, mix multilayer con solo/mute, seeding namespaced riproducibile,
golden test e documentazione di riferimento.
