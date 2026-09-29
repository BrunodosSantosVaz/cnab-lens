"""Descrições do CNAB 240 Santander: Segmentos T, U, Y-03 e Y-04 do retorno e os Trailers de Lote e de Arquivo.
Fecha o épico #85: nenhum campo dos layouts do Santander (400 e 240) só remete a uma nota do manual."""
import re
import unittest

import _caminho  # noqa: F401  (põe src/ no caminho)

from cnablens.layouts import santander240 as s
from cnablens.layouts import santander400

REGISTROS = ("SEGMENTO_T_RETORNO_FIELDS", "SEGMENTO_U_RETORNO_FIELDS", "SEGMENTO_Y03_RETORNO_FIELDS",
             "SEGMENTO_Y04_RETORNO_FIELDS", "TRAILER_LOTE_REMESSA_FIELDS", "TRAILER_ARQUIVO_REMESSA_FIELDS",
             "TRAILER_LOTE_RETORNO_FIELDS", "TRAILER_ARQUIVO_RETORNO_FIELDS")


def descricao(registro, inicio):
    return next(t for _n, i, _f, t in getattr(s, registro) if i == inicio)


class DescricoesSantander240Retorno(unittest.TestCase):
    def test_nenhum_campo_so_remete_ao_manual(self):
        for registro in REGISTROS:
            for nome, inicio, _fim, texto in getattr(s, registro):
                with self.subTest(registro=registro, campo=nome, inicio=inicio):
                    self.assertNotIn("ver nota", texto)
                    self.assertNotIn("conteúdo no manual", texto)
                    if "Uso Reservado" not in nome:
                        self.assertGreaterEqual(len(texto), 25)

    def test_codigos_do_segmento_t_citam_as_tabelas_certas(self):
        motivos = descricao("SEGMENTO_T_RETORNO_FIELDS", 209)
        for tabela in ("REJEICAO_CODES", "LIQUIDACAO_CODES", "BAIXA_CODES"):
            self.assertIn(tabela, motivos)
        for codigo in ("'61'", "'92'", "'P1'", "'P2'"):  # Pix e QR Code
            self.assertIn(codigo, motivos)
        self.assertIn("MOVIMENTO_RETORNO_CODES", descricao("SEGMENTO_T_RETORNO_FIELDS", 16))

    def test_carteira_do_retorno_tem_todos_os_codigos(self):
        texto = descricao("SEGMENTO_T_RETORNO_FIELDS", 54)
        for codigo in ("'1'", "'2'", "'3'", "'4'", "'5'", "'6'", "'7'", "'8'", "'9'", "'B'"):
            with self.subTest(codigo=codigo):
                self.assertIn(codigo, texto)


class EpicoSantanderCompleto(unittest.TestCase):
    def test_nenhum_campo_do_santander_so_remete_ao_manual(self):
        for modulo in (santander400, s):
            for lista in (n for n in dir(modulo) if n.endswith("_FIELDS")):
                for nome, inicio, _fim, texto in getattr(modulo, lista):
                    with self.subTest(modulo=modulo.__name__, lista=lista, campo=nome, inicio=inicio):
                        self.assertNotIn("ver nota", texto)
                        self.assertNotIn("conteúdo no manual", texto)
                        self.assertTrue(texto.endswith("."), texto[-30:])

    def test_tabelas_citadas_existem(self):
        for modulo in (santander400, s):
            for lista in (n for n in dir(modulo) if n.endswith("_FIELDS")):
                for nome, _inicio, _fim, texto in getattr(modulo, lista):
                    for tabela in re.findall(r"\b[A-Z_]+_CODES\b", texto):
                        with self.subTest(modulo=modulo.__name__, campo=nome, tabela=tabela):
                            self.assertTrue(hasattr(modulo, tabela))


if __name__ == "__main__":
    unittest.main()
