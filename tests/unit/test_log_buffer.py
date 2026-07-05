"""Unit — LogBuffer della GUI: terminale con timestamp e lettura
incrementale, cap sulle righe tenute in memoria.
"""

from src.web.app import LogBuffer


class TestScrittura:
    def test_write_scarta_le_righe_vuote(self):
        log = LogBuffer()
        log.write("prima\n\n   \nseconda\n")
        lines = [line for _, line in log.since(0)["lines"]]
        assert lines == ["prima", "seconda"]

    def test_flush_e_un_no_op_file_like(self):
        # interfaccia file-like per redirect_stdout: non deve sollevare.
        log = LogBuffer()
        log.write("x")
        assert log.flush() is None


class TestCapDelleRighe:
    def test_supero_del_massimo_scarta_le_piu_vecchie(self):
        log = LogBuffer(max_lines=2)
        log.add("uno")
        log.add("due")
        log.add("tre")          # sfora: "uno" cade
        result = log.since(0)
        assert [line for _, line in result["lines"]] == ["due", "tre"]
        # l'indice assoluto avanza col numero di righe scartate
        assert result["next"] == 3

    def test_lettura_incrementale_dopo_lo_scarto(self):
        log = LogBuffer(max_lines=2)
        for word in ("a", "b", "c", "d"):
            log.add(word)
        # chi aveva già letto fino a next=2 riprende senza duplicati né buchi
        result = log.since(2)
        assert [line for _, line in result["lines"]] == ["c", "d"]
        assert result["next"] == 4
