"""Gerarchia degli errori di audiolayers.

Tutti gli errori rivolti al compositore derivano da ScoreError, così la
CLI può catturarli e stampare solo il messaggio (niente traceback).
"""


class ScoreError(Exception):
    """Errore nella partitura o nei dati che essa referenzia."""


class InvalidFieldValueError(ScoreError):
    """Valore di un campo YAML non valido (forma o contenuto)."""
