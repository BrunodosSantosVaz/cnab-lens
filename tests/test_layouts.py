# -*- coding: utf-8 -*-
"""Consistência das tabelas de layout e do registro de layouts."""
import unittest

import _caminho  # noqa: F401
from cnablens.layouts import santander240
from cnablens.layouts import sicoob240
from cnablens.layouts import febraban400 as febraban
from cnablens.layouts import santander400
from cnablens.layouts import sicoob400
from cnablens.layouts import sicredi400 as sicredi
from cnablens import layouts
from cnablens.layouts import bancos
from cnablens.layouts.__main__ import MODULOS, listas_de_campos
from cnablens.layouts.base import PorTipo, RegistroOpcional, validar_contiguidade



class TabelasDeCampos(unittest.TestCase):
    def test_todas_as_listas_cobrem_todas_as_posicoes_sem_lacuna(self):
        for modulo, largura in MODULOS:
            for nome, campos in listas_de_campos(modulo):
                with self.subTest(modulo=modulo.__name__, lista=nome):
                    validar_contiguidade(campos, largura, nome)  # levanta ValueError dizendo onde está o problema

    def test_validacao_aponta_lacuna_e_sobreposicao(self):
        campos = [("A", 1, 10, "a"), ("B", 12, 400, "b")]
        with self.assertRaisesRegex(ValueError, "'B' começa em 12, esperado 11"):
            validar_contiguidade(campos, 400)
        with self.assertRaisesRegex(ValueError, "termina em 10, esperado 400"):
            validar_contiguidade([("A", 1, 10, "a")], 400)
        with self.assertRaisesRegex(ValueError, "sem nome ou descrição"):
            validar_contiguidade([("A", 1, 400, "")], 400)

    def test_sem_validacao_repetida_nos_modulos_de_dados(self):
        for modulo, _ in MODULOS:
            with self.subTest(modulo=modulo.__name__):
                self.assertFalse(hasattr(modulo, "_validate_contiguous"))

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
        self.assertEqual(layouts.auto_layout_key("033", 240), "santander240")
        self.assertEqual(layouts.auto_layout_key("341", 400), "febraban")
        self.assertEqual(layouts.auto_layout_key("001", 240), "sicoob240")  # padrão para bancos de 240 sem layout próprio
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
        self.assertEqual(bancos.NOMES_DOS_BANCOS["756"], "Sicoob (Bancoob)")
        self.assertEqual(bancos.NOMES_DOS_BANCOS["748"], "Sicredi")
        self.assertEqual(bancos.NOMES_DOS_BANCOS["033"], "Santander")
        self.assertFalse(hasattr(febraban, "BANK_NAMES"))  # a tabela de bancos vale para todos os layouts


class BlocosDosLayouts(unittest.TestCase):
    def test_por_tipo(self):
        remessa, retorno = [("R", 1, 400, "r")], [("T", 1, 400, "t")]
        self.assertIs(PorTipo(remessa, retorno)("Remessa"), remessa)
        self.assertIs(PorTipo(remessa, retorno)("Retorno"), retorno)
        self.assertIs(PorTipo(remessa, retorno)("Desconhecido"), remessa)  # como antes: só "Retorno" muda
        self.assertIs(PorTipo.igual(remessa)("Retorno"), remessa)

    def test_registro_opcional(self):
        registro = RegistroOpcional(remessa=("Registro 8", []))
        self.assertEqual(registro("Remessa"), ("Registro 8", []))
        self.assertIsNone(registro("Retorno"))

    def test_todo_layout_tem_a_mesma_interface(self):
        for chave, layout in layouts.LAYOUTS.items():
            with self.subTest(layout=chave):
                for atributo in ("key", "label", "width", "ocorrencia_codes", "comando_codes", "structure", "record_types"):
                    self.assertTrue(hasattr(layout, atributo), atributo)


if __name__ == "__main__":
    unittest.main()
