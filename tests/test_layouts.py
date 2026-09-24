# -*- coding: utf-8 -*-
"""Consistência das tabelas de layout e do registro de layouts."""
import unittest

import _caminho  # noqa: F401
import cnab240_layout_santander as santander240
import cnab240_layout_sicoob as sicoob240
import cnab400_layout as febraban
import cnab400_layout_santander as santander400
import cnab400_layout_sicoob as sicoob400
import cnab400_layout_sicredi as sicredi
import cnab400_layouts as layouts

MODULOS = [(febraban, 400), (sicredi, 400), (sicoob400, 400), (santander400, 400), (sicoob240, 240), (santander240, 240)]


def listas_de_campos(modulo):
    return [(nome, valor) for nome, valor in vars(modulo).items()
            if nome.endswith("_FIELDS") and isinstance(valor, list)]


class TabelasDeCampos(unittest.TestCase):
    def test_todas_as_listas_cobrem_todas_as_posicoes_sem_lacuna(self):
        for modulo, largura in MODULOS:
            for nome, campos in listas_de_campos(modulo):
                with self.subTest(modulo=modulo.__name__, lista=nome):
                    esperado = 1
                    for campo in campos:
                        self.assertEqual(len(campo), 4, campo)
                        titulo, inicio, fim, descricao = campo
                        self.assertTrue(titulo and descricao, campo)
                        self.assertEqual(inicio, esperado, f"{titulo}: começa em {inicio}, esperado {esperado}")
                        self.assertGreaterEqual(fim, inicio, titulo)
                        esperado = fim + 1
                    self.assertEqual(esperado, largura + 1, f"termina em {esperado - 1}")

    def test_ha_listas_em_cada_modulo(self):
        for modulo, _ in MODULOS:
            self.assertTrue(listas_de_campos(modulo), modulo.__name__)

    def test_segmentos_240_apontam_para_listas_existentes(self):
        for (tipo, letra), campos in sicoob240.SEGMENTOS.items():
            with self.subTest(tipo=tipo, segmento=letra):
                self.assertIn(tipo, ("Remessa", "Retorno"))
                self.assertEqual(len(letra), 1)
                self.assertEqual(campos[0][1], 1)


class ResumoDaGrade(unittest.TestCase):
    """A grade de lançamentos localiza colunas por trecho do nome do campo:
    todo layout precisa ter vencimento, valor e ocorrência/comando."""

    def detalhes(self):
        yield "febraban/Remessa", febraban.DETAIL_REMESSA_FIELDS
        yield "febraban/Retorno", febraban.DETAIL_RETORNO_FIELDS
        yield "sicredi/Remessa", sicredi.DETAIL_REMESSA_FIELDS
        yield "sicredi/Retorno", sicredi.DETAIL_RETORNO_FIELDS
        yield "sicoob400/Remessa", sicoob400.DETAIL_REMESSA_FIELDS
        yield "sicoob400/Retorno", sicoob400.DETAIL_RETORNO_FIELDS
        yield "santander400/Remessa", santander400.DETAIL_REMESSA_FIELDS
        yield "santander400/Retorno", santander400.DETAIL_RETORNO_FIELDS
        yield "sicoob240/Remessa", sicoob240.SEGMENTO_P_REMESSA_FIELDS
        yield "sicoob240/Retorno", sicoob240.SEGMENTO_T_RETORNO_FIELDS
        yield "santander240/Remessa", santander240.SEGMENTO_P_REMESSA_FIELDS
        yield "santander240/Retorno", santander240.SEGMENTO_T_RETORNO_FIELDS

    def test_campos_essenciais_presentes(self):
        for rotulo, campos in self.detalhes():
            nomes = " | ".join(c[0].lower() for c in campos)
            with self.subTest(layout=rotulo):
                self.assertIn("data de vencimento", nomes)
                self.assertTrue("valor nominal" in nomes or "valor do título" in nomes)
                self.assertTrue(any(k in nomes for k in ("ocorrência", "movimento", "comando")))
                self.assertIn("nosso número", nomes)


class RegistroDeLayouts(unittest.TestCase):
    def test_ordem_e_chaves_coerentes(self):
        self.assertEqual(sorted(layouts.LAYOUT_ORDER), sorted(layouts.LAYOUTS))
        rotulos = layouts.layout_labels()
        self.assertEqual(len(set(rotulos)), len(rotulos))
        for chave in layouts.LAYOUT_ORDER:
            self.assertEqual(layouts.key_for_label(layouts.LAYOUTS[chave].label), chave)

    def test_selecao_automatica_por_banco_e_largura(self):
        self.assertEqual(layouts.auto_layout_key("748", 400), "sicredi")
        self.assertEqual(layouts.auto_layout_key("033", 400), "santander400")
        self.assertEqual(layouts.auto_layout_key("353", 400), "santander400")  # código legado no Header
        self.assertEqual(layouts.auto_layout_key("756", 400), "sicoob400")
        self.assertEqual(layouts.auto_layout_key("756", 240), "sicoob240")
        self.assertEqual(layouts.auto_layout_key("341", 400), "febraban")
        self.assertEqual(layouts.auto_layout_key("001", 240), "sicoob240")  # único layout de 240
        for (banco, largura), chave in layouts.AUTO_LAYOUT_BY_BANK.items():
            self.assertEqual(layouts.LAYOUTS[chave].width, largura)

    def test_layouts_400_e_240(self):
        larguras = {chave: layouts.LAYOUTS[chave].width for chave in layouts.LAYOUT_ORDER}
        self.assertEqual(larguras, {"febraban": 400, "sicredi": 400, "sicoob400": 400, "santander400": 400, "sicoob240": 240,
                                     "santander240": 240})
        self.assertIsNotNone(layouts.LAYOUTS["sicoob240"].structure)
        self.assertIsNotNone(layouts.LAYOUTS["santander240"].structure)

    def test_registros_opcionais_do_santander_400(self):
        registros = layouts.LAYOUTS["santander400"].record_types
        self.assertEqual(sorted(registros), ["2", "4", "5", "6", "7", "8"])
        self.assertIn("QR Code", registros["8"]("Remessa")[0])
        self.assertIsNone(registros["8"]("Retorno"))  # o registro 8 não existe no retorno
        self.assertIn("Mensagem", registros["2"]("Remessa")[0])
        self.assertIn("QR Code", registros["2"]("Retorno")[0])  # o mesmo tipo 2 muda de significado no retorno
        self.assertIsNone(registros["4"]("Retorno"))
        self.assertTrue(registros["7"]("Remessa")[0].startswith("Registro 7"))
        for chave in ("febraban", "sicredi", "sicoob400", "sicoob240"):
            self.assertIsNone(layouts.LAYOUTS[chave].record_types, chave)

    def test_chave_do_segmento_no_santander_240(self):
        chave = layouts.LAYOUTS["santander240"].structure.chave_segmento
        y03 = " " * 17 + "03" + " " * 221
        self.assertEqual(chave("Remessa", "Y", y03), "Y-03")
        self.assertEqual(chave("Retorno", "Y", " " * 17 + "04" + " " * 221), "Y-04")
        self.assertEqual(chave("Remessa", "S", " " * 17 + "2" + " " * 222), "S-2")
        self.assertEqual(chave("Remessa", "P", y03), "P")  # só Y e S se subdividem
        self.assertEqual(chave("Remessa", "Y", "curta"), "Y-")  # linha curta não quebra
        self.assertIsNone(layouts.LAYOUTS["sicoob240"].structure.chave_segmento)

    def test_bancos_conhecidos(self):
        self.assertEqual(febraban.BANK_NAMES["756"], "Sicoob (Bancoob)")
        self.assertEqual(febraban.BANK_NAMES["748"], "Sicredi")
        self.assertEqual(febraban.BANK_NAMES["033"], "Santander")


if __name__ == "__main__":
    unittest.main()
