# -*- coding: utf-8 -*-
"""Seletor de layout e grade da tela com arquivos Santander (sintéticos, dados fictícios)."""
import os
import tempfile
import tkinter as tk
import unittest
from unittest import mock

import _caminho  # noqa: F401
import cnab400_reader as app
import test_leitura_santander240 as t240
import test_leitura_santander400 as t400


class TelaSantander(unittest.TestCase):
    root = None

    @classmethod
    def setUpClass(cls):
        try:
            cls.root = app.App()
        except tk.TclError as exc:  # sem display (ex.: CI Linux sem xvfb)
            raise unittest.SkipTest(f"sem ambiente gráfico: {exc}")
        cls.root.withdraw()
        cls.root.geometry("1200x700+0+0")
        cls.root.update()

    @classmethod
    def tearDownClass(cls):
        if cls.root is not None:
            cls.root.destroy()

    def abrir(self, linhas):
        fd, caminho = tempfile.mkstemp(suffix=".rem")
        with os.fdopen(fd, "w", encoding="latin-1", newline="") as f:
            f.write("\r\n".join(linhas) + "\r\n")
        self.addCleanup(os.remove, caminho)
        self.root.carregar_arquivo(caminho)
        self.root.update()
        return [self.root.tree.item(i, "values") for i in self.root.tree.get_children()]

    def remessa400(self):
        return [t400.header("Remessa"), t400.movimento(2, "NF-1001"), t400.registro8(3, "TXID" * 8),
                t400.registro("2", 4, p50="MENSAGEM FICTICIA"), t400.movimento(5, "NF-1002"), t400.trailer(6)]

    def test_seletor_lista_os_dois_layouts_do_santander(self):
        valores = list(self.root.layout_combo["values"])
        self.assertIn("CNAB400 Santander", valores)
        self.assertIn("CNAB240 Santander", valores)
        self.assertEqual(valores[-1], "CNAB240 Santander")

    def test_arquivo_400_abre_com_o_layout_do_santander_e_uma_linha_por_boleto(self):
        linhas = self.abrir(self.remessa400())
        self.assertEqual(self.root.layout_var.get(), "CNAB400 Santander")
        self.assertEqual(len(linhas), 2)  # os registros 8 e 2 não viram linhas
        self.assertEqual(linhas[0][1], "01 - Entrada do boleto")
        self.assertEqual(linhas[0][2:5], ("NF-1001", "25/10/2026", "159,90"))
        self.assertEqual(linhas[0][5], "00001234")
        self.assertEqual(linhas[0][6], "CLIENTE FICTICIO")

    def test_painel_mostra_os_tres_registros_do_boleto(self):
        self.abrir(self.remessa400())
        primeiro = self.root.tree.get_children()[0]
        self.root.tree.selection_set(primeiro)
        self.root.update()
        painel = self.root.detail_panel
        texto = painel.text.get("1.0", "end")
        for trecho in ("Detalhe (Registro 1)", "Registro 8 - Tipo de pagamento", "Registro 2 - Mensagem", "TXID"):
            self.assertIn(trecho, texto)

    def test_retorno_400_mostra_ocorrencia_e_valor_pago(self):
        linhas = self.abrir([t400.header("Retorno"),
                             t400.movimento(2, "NF-1001", tipo="Retorno", movimento_cod="06", pago="0000000015990"),
                             t400.trailer(3)])
        self.assertEqual(linhas[0][1], "06 - Liquidação do Boleto Efetivada")
        self.assertIn("Pago: R$ 159,90", linhas[0][6])

    def test_arquivo_240_abre_com_o_layout_do_santander(self):
        linhas = self.abrir([t240.header_arquivo("Remessa"), t240.header_lote("Remessa"),
                             t240.segmento("P", 1, (16, "01"), (63, "NF-1001"), (78, "25102026"), (86, "000000000015990")),
                             t240.segmento("Q", 2, (34, "CLIENTE FICTICIO")),
                             t240.segmento("Y", 3, (18, "03"), (159, t240.RemessaSantander240.TXID)),
                             t240.trailer_lote(5), t240.trailer_arquivo(7)])
        self.assertEqual(self.root.layout_var.get(), "CNAB240 Santander")
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0][1], "01 - Entrada de boleto")
        self.assertEqual(linhas[0][2:5], ("NF-1001", "25/10/2026", "159,90"))
        self.assertEqual(linhas[0][6], "CLIENTE FICTICIO")

    def test_retorno_240_mostra_movimento_e_valor_pago(self):
        linhas = self.abrir([t240.header_arquivo("Retorno"), t240.header_lote("Retorno"),
                             t240.segmento("T", 1, (16, "06"), (55, "NF-1001"), (70, "25102026"), (78, "000000000015990")),
                             t240.segmento("U", 2, (16, "06"), (78, "000000000015990")),
                             t240.trailer_lote(4), t240.trailer_arquivo(6)])
        self.assertEqual(linhas[0][1], "06 - Liquidação do Boleto Efetivada")
        self.assertIn("Pago: R$ 159,90", linhas[0][6])

    def test_trocar_para_layout_de_outra_largura_avisa(self):
        self.abrir(self.remessa400())
        with mock.patch.object(app.messagebox, "showwarning") as aviso:
            self.root.layout_var.set("CNAB240 Santander")
            self.root.on_layout_change()
        aviso.assert_called_once()
        self.assertEqual(self.root.layout_var.get(), "CNAB400 Santander")

    def test_trocar_de_santander_para_febraban_e_voltar(self):
        self.abrir(self.remessa400())
        self.root.layout_var.set("CNAB400 FEBRABAN (Padrão)")
        self.root.on_layout_change()
        self.assertEqual(len(self.root.tree.get_children()), 2)
        self.root.layout_var.set("CNAB400 Santander")
        self.root.on_layout_change()
        self.assertEqual(self.root.cnab_file.layout_key, "santander400")
        self.assertEqual(len(self.root.tree.get_children()), 2)


if __name__ == "__main__":
    unittest.main()
