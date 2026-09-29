"""Descrições do CNAB 400 Santander (Header, Movimento e Trailer, remessa e retorno): cada campo explica o que
é, no padrão dos outros bancos, em vez de só remeter a uma nota do manual H7800 (épico #85)."""
import re
import unittest

import _caminho  # noqa: F401  (põe src/ no caminho)

from cnablens.layouts import santander400 as s

REGISTROS = ("HEADER_REMESSA_FIELDS", "DETAIL_REMESSA_FIELDS", "TRAILER_REMESSA_FIELDS",
             "HEADER_RETORNO_FIELDS", "DETAIL_RETORNO_FIELDS", "TRAILER_RETORNO_FIELDS")


def campos():
    for registro in REGISTROS:
        for nome, inicio, fim, descricao in getattr(s, registro):
            yield registro, nome, inicio, fim, descricao


def descricao(registro, inicio):
    return next(d for r, _n, i, _f, d in campos() if r == registro and i == inicio)


class DescricoesSantander400(unittest.TestCase):
    def test_nenhum_campo_so_remete_ao_manual(self):
        for registro, nome, inicio, _fim, texto in campos():
            with self.subTest(registro=registro, campo=nome, inicio=inicio):
                self.assertNotIn("ver nota", texto)
                self.assertNotIn("conteúdo no manual", texto)
                if "Uso Reservado" not in nome:
                    self.assertGreaterEqual(len(texto), 25, "descrição curta demais para explicar o campo")

    def test_tabelas_citadas_existem(self):
        for registro, nome, _inicio, _fim, texto in campos():
            for tabela in re.findall(r"\b[A-Z_]+_CODES\b", texto):
                with self.subTest(registro=registro, campo=nome, tabela=tabela):
                    self.assertTrue(hasattr(s, tabela))

    def test_codigos_embutidos_batem_com_as_tabelas(self):
        casos = (
            (descricao("DETAIL_REMESSA_FIELDS", 157), s.INSTRUCAO_CODES),
            (descricao("DETAIL_REMESSA_FIELDS", 159), s.INSTRUCAO_CODES),
            (descricao("DETAIL_REMESSA_FIELDS", 148), s.ESPECIE_BOLETO_CODES),
            (descricao("DETAIL_RETORNO_FIELDS", 174), s.ESPECIE_BOLETO_CODES),
        )
        for texto, tabela in casos:
            for codigo in tabela:
                with self.subTest(codigo=codigo, texto=texto[:40]):
                    self.assertIn(f"'{codigo}'", texto)

    def test_conteudo_fixo_nao_vira_nota(self):
        # a extração automática tinha confundido o conteúdo fixo ("0", "1", "01", "00", "9") com notas do manual
        self.assertIn("'0' identifica o Header", descricao("HEADER_REMESSA_FIELDS", 1))
        self.assertIn("'1' identifica o Registro de Movimento", descricao("DETAIL_REMESSA_FIELDS", 1))
        self.assertIn("'9' identifica o Trailer", descricao("TRAILER_RETORNO_FIELDS", 1))
        self.assertIn("'2' = arquivo de retorno", descricao("HEADER_RETORNO_FIELDS", 2))
        self.assertIn("'00'", descricao("DETAIL_REMESSA_FIELDS", 83))


if __name__ == "__main__":
    unittest.main()
