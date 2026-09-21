# -*- coding: utf-8 -*-
"""Formatação de valores, datas e campos exibidos no painel."""
import unittest

import _caminho  # noqa: F401
import cnab400_reader as app


class Datas(unittest.TestCase):
    def test_ddmmaa(self):
        self.assertEqual(app.format_data("250826"), "25/08/2026")
        self.assertEqual(app.format_data("010199"), "01/01/1999")

    def test_aaaammdd_do_sicredi(self):
        self.assertEqual(app.format_data("20260820"), "20/08/2026")

    def test_ddmmaaaa_do_cnab240(self):
        self.assertEqual(app.format_data("25102026"), "25/10/2026")
        self.assertEqual(app.format_data("20122026"), "20/12/2026")

    def test_data_invalida_devolve_o_bruto(self):
        # regressão: "202608" já foi lido como 20/26/2008 (mês 26)
        self.assertEqual(app.format_data("202608"), "202608")
        self.assertEqual(app.format_data("000000"), "000000")
        self.assertEqual(app.format_data("00000000"), "00000000")
        self.assertEqual(app.format_data("ABC"), "ABC")
        self.assertEqual(app.format_data(""), "")


class Valores(unittest.TestCase):
    def test_centavos_implicitos(self):
        self.assertEqual(app.format_valor_monetario("0000015990"), "159,90")
        self.assertEqual(app.format_valor_monetario("5"), "0,05")
        self.assertEqual(app.format_valor_monetario("000123456789"), "1.234.567,89")
        self.assertEqual(app.format_valor_monetario("0000000000000"), "0,00")


class CampoDoPainel(unittest.TestCase):
    def test_valor_monetario_mostra_bruto_e_convertido(self):
        self.assertEqual(app.formatar_valor_campo("Valor Nominal do Título", "0000015990"),
                         "0000015990  →  R$ 159,90")

    def test_data_mostra_bruto_e_convertido(self):
        self.assertEqual(app.formatar_valor_campo("Data de Vencimento do Título", "25102026"),
                         "25102026  →  25/10/2026")

    def test_data_de_desconto_e_data_nao_dinheiro(self):
        # regressão: "Data do Desconto" tem a palavra desconto mas é uma data
        self.assertEqual(app.formatar_valor_campo("Data do Desconto 1", "25102026"), "25102026  →  25/10/2026")

    def test_codigo_ou_tipo_de_desconto_nao_e_dinheiro(self):
        self.assertEqual(app.formatar_valor_campo("Código do Desconto 1", "1"), "1")
        self.assertEqual(app.formatar_valor_campo("Tipo de Juros (A = Valor Monetário)", "A"), "A")
        self.assertEqual(app.formatar_valor_campo("Taxa de Multa (%)", "000200"), "000200")

    def test_campo_vazio_e_texto_ficam_como_estao(self):
        self.assertEqual(app.formatar_valor_campo("Valor Pago", ""), "")
        self.assertEqual(app.formatar_valor_campo("Nome do Pagador", "MARIA"), "MARIA")


if __name__ == "__main__":
    unittest.main()
