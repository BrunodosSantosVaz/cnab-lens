"""Descrições do CNAB 240 Santander: Headers de Arquivo e de Lote (remessa e retorno) e os segmentos da
remessa (P, Q, R, S, Y-03 e Y-53). Cada campo explica o que é, a partir do manual H7815, em vez de só
remeter a uma nota (épico #85)."""
import re
import unittest

import _caminho  # noqa: F401  (põe src/ no caminho)

from cnablens.layouts import santander240 as s

REGISTROS = ("HEADER_ARQUIVO_REMESSA_FIELDS", "HEADER_LOTE_REMESSA_FIELDS", "SEGMENTO_P_REMESSA_FIELDS",
             "SEGMENTO_Q_REMESSA_FIELDS", "SEGMENTO_R_REMESSA_FIELDS", "SEGMENTO_S_1_REMESSA_FIELDS",
             "SEGMENTO_S_2_REMESSA_FIELDS", "SEGMENTO_Y03_REMESSA_FIELDS", "SEGMENTO_Y53_REMESSA_FIELDS",
             "HEADER_ARQUIVO_RETORNO_FIELDS", "HEADER_LOTE_RETORNO_FIELDS")


def campos():
    for registro in REGISTROS:
        for nome, inicio, _fim, texto in getattr(s, registro):
            yield registro, nome, inicio, texto


def descricao(registro, inicio):
    return next(t for r, _n, i, t in campos() if r == registro and i == inicio)


class DescricoesSantander240Remessa(unittest.TestCase):
    def test_nenhum_campo_so_remete_ao_manual(self):
        for registro, nome, inicio, texto in campos():
            with self.subTest(registro=registro, campo=nome, inicio=inicio):
                self.assertNotIn("ver nota", texto)
                self.assertNotIn("conteúdo no manual", texto)
                if "Uso Reservado" not in nome:
                    self.assertGreaterEqual(len(texto), 25)

    def test_tabelas_citadas_existem(self):
        for registro, nome, _inicio, texto in campos():
            for tabela in re.findall(r"\b[A-Z_]+_CODES\b", texto):
                with self.subTest(registro=registro, campo=nome, tabela=tabela):
                    self.assertTrue(hasattr(s, tabela))

    def test_especie_embute_todos_os_codigos(self):
        texto = descricao("SEGMENTO_P_REMESSA_FIELDS", 107)
        for codigo in s.ESPECIE_BOLETO_CODES:
            with self.subTest(codigo=codigo):
                self.assertIn(f"'{codigo}'", texto)

    def test_codigos_curtos_embutidos(self):
        casos = {
            ("SEGMENTO_P_REMESSA_FIELDS", 118): ("'1'", "'2'", "'3'", "'4'", "'5'", "'6'"),  # juros (nota 21)
            ("SEGMENTO_P_REMESSA_FIELDS", 142): ("'0'", "'1'", "'2'", "'3'", "'4'"),  # desconto (nota 23)
            ("SEGMENTO_P_REMESSA_FIELDS", 221): ("'0'", "'1'", "'2'", "'3'", "'9'"),  # protesto (nota 25)
            ("SEGMENTO_P_REMESSA_FIELDS", 224): ("'1'", "'2'", "'3'"),  # baixa (nota 26)
            ("SEGMENTO_P_REMESSA_FIELDS", 58): ("'1'", "'3'", "'4'", "'5'", "'6'", "'7'", "'8'", "'9'", "'B'"),
            ("SEGMENTO_Y53_REMESSA_FIELDS", 20): ("'01'", "'02'", "'03'"),  # tipo de pagamento (nota 46)
            ("SEGMENTO_Y03_REMESSA_FIELDS", 81): ("'1' CPF", "'2' CNPJ", "'3' celular", "'4' e-mail", "'5' EVP"),
        }
        for (registro, inicio), codigos in casos.items():
            for codigo in codigos:
                with self.subTest(registro=registro, inicio=inicio, codigo=codigo):
                    self.assertIn(codigo, descricao(registro, inicio))

    def test_conteudo_fixo_nao_vira_nota(self):
        # a extração tinha lido o conteúdo fixo ("01" do tipo de serviço) como número de nota
        self.assertIn("'01' = Cobrança", descricao("HEADER_LOTE_RETORNO_FIELDS", 10))
        self.assertIn("'P'", descricao("SEGMENTO_P_REMESSA_FIELDS", 14))


if __name__ == "__main__":
    unittest.main()
