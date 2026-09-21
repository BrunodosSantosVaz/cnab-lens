# -*- coding: utf-8 -*-
"""Interface (Tkinter): painel de campos copiável, alinhamento, layouts incompatíveis e grade.

Precisa de uma área de trabalho para criar a janela (escondida). Sem ela, os testes são pulados."""
import tkinter as tk
import unittest
from unittest import mock

import _caminho
import cnab400_reader as app


class Evento:
    """Evento mínimo para chamar os handlers diretamente."""

    def __init__(self, x=0, y=0, keysym="", state=0):
        self.x, self.y, self.keysym, self.state = x, y, keysym, state


class BaseInterface(unittest.TestCase):
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

    def abrir(self, nome):
        self.root.carregar_arquivo(_caminho.exemplo(nome))
        self.root.update()
        primeiro = self.root.tree.get_children()[0]
        self.root.tree.selection_set(primeiro)
        self.root.update()
        return self.root.detail_panel

    @staticmethod
    def linhas(painel):
        return int(painel.text.index("end-1c").split(".")[0])

    def linha_do_campo(self, painel, prefixo):
        for n in range(1, self.linhas(painel) + 1):
            if painel.text.get(f"{n}.0", f"{n}.end").startswith(prefixo):
                return n
        self.fail(f"campo '{prefixo}' não está no painel")


class Titulo(BaseInterface):
    def test_titulo_da_janela_mostra_a_versao(self):
        from version import __version__
        self.assertIn("CNABLens", self.root.title())
        self.assertIn(__version__, self.root.title())


class CopiarValores(BaseInterface):
    def test_duplo_clique_seleciona_a_celula_do_valor(self):
        painel = self.abrir("sicredi_retorno.ret")
        n = self.linha_do_campo(painel, "Seu Número")
        inicio, fim = painel._cells[n][2]
        esperado = painel.text.get(f"{n}.{inicio}", f"{n}.{fim}")
        self.assertEqual(esperado, "NF-1001")
        x, y, *_ = painel.text.bbox(f"{n}.{inicio}")
        self.assertEqual(painel._on_double_click(Evento(x + 2, y + 2)), "break")
        self.assertEqual(painel.text.get("sel.first", "sel.last"), esperado)

    def test_ctrl_c_coloca_a_selecao_na_area_de_transferencia(self):
        painel = self.abrir("sicredi_retorno.ret")
        n = self.linha_do_campo(painel, "Seu Número")
        inicio, fim = painel._cells[n][2]
        painel.text.tag_add("sel", f"{n}.{inicio}", f"{n}.{fim}")
        try:
            self.root.clipboard_clear()
            painel.text.event_generate("<<Copy>>")
            self.root.update()
            copiado = self.root.clipboard_get()
        except tk.TclError as exc:
            self.skipTest(f"área de transferência indisponível: {exc}")
        self.assertEqual(copiado, "NF-1001")

    def test_ctrl_a_seleciona_tudo(self):
        painel = self.abrir("sicredi_retorno.ret")
        painel._select_all()
        self.assertGreater(len(painel.text.get("sel.first", "sel.last")), 500)

    def test_painel_e_somente_leitura(self):
        painel = self.abrir("sicredi_retorno.ret")
        self.assertEqual(painel._on_key(Evento(keysym="a")), "break")
        self.assertEqual(painel._on_key(Evento(keysym="BackSpace")), "break")
        self.assertEqual(painel._on_key(Evento(keysym="Delete")), "break")
        self.assertEqual(painel._on_key(Evento(keysym="v", state=4)), "break")  # Ctrl+V
        self.assertEqual(painel._on_key(Evento(keysym="x", state=4)), "break")  # Ctrl+X
        self.assertIsNone(painel._on_key(Evento(keysym="c", state=4)))          # Ctrl+C livre
        self.assertIsNone(painel._on_key(Evento(keysym="Down")))

    def test_ctrl_c_na_grade_copia_a_linha(self):
        self.abrir("sicredi_retorno.ret")
        self.assertEqual(self.root._copiar_linha_lancamento(), "break")
        try:
            linha = self.root.clipboard_get()
        except tk.TclError as exc:
            self.skipTest(f"área de transferência indisponível: {exc}")
        self.assertEqual(linha.count("\t"), 6)
        self.assertIn("NF-1001", linha)


class Alinhamento(BaseInterface):
    def test_colunas_alinhadas_e_cabecalho_junto_com_o_corpo(self):
        for nome in ("sicoob240_remessa.rem", "sicoob400_retorno.ret"):
            with self.subTest(arquivo=nome):
                painel = self.abrir(nome)
                x = {1: set(), 2: set(), 3: set()}
                for n in range(1, self.linhas(painel) + 1):
                    celulas = painel._cells.get(n)
                    if celulas and len(celulas) == 4:
                        for k in (1, 2, 3):
                            inicio, fim = celulas[k]
                            caixa = painel.text.bbox(f"{n}.{inicio}") if fim > inicio else None
                            if caixa:
                                x[k].add(caixa[0])
                self.assertTrue(all(len(v) == 1 for v in x.values()), x)
                col, cab = 0, {}
                for k, titulo in enumerate(painel.head.get("1.0", "1.end").split("\t")[:4]):
                    caixa = painel.head.bbox(f"1.{col}")
                    cab[k] = caixa[0] if caixa else None
                    col += len(titulo) + 1
                for k in (1, 2, 3):
                    self.assertIn(cab[k], x[k])

    def test_rolagem_horizontal_sincronizada(self):
        painel = self.abrir("sicoob240_remessa.rem")
        painel._on_hscroll("moveto", 0.4)
        self.root.update()
        self.assertAlmostEqual(painel.text.xview()[0], painel.head.xview()[0], delta=0.002)


class Cnab240NaTela(BaseInterface):
    def test_titulo_mostra_um_separador_por_segmento(self):
        painel = self.abrir("sicoob240_remessa.rem")
        separadores = [n for n in range(1, self.linhas(painel) + 1) if "sep" in painel.text.tag_names(f"{n}.0")]
        self.assertEqual(len(separadores), 2)

    def test_header_e_trailer(self):
        self.abrir("sicoob240_retorno.ret")
        for acao, esperado in ((self.root.mostrar_header, ("Header de Arquivo", "Header de Lote")),
                               (self.root.mostrar_trailer, ("Trailer de Lote", "Trailer de Arquivo"))):
            acao()
            self.root.update()
            painel = self.root.detail_panel
            titulos = [painel.text.get(f"{n}.0", f"{n}.end") for n in range(1, self.linhas(painel) + 1)
                       if "sep" in painel.text.tag_names(f"{n}.0")]
            for parte, titulo in zip(esperado, titulos):
                self.assertIn(parte, titulo)

    def test_grade_resume_o_titulo(self):
        self.abrir("sicoob240_retorno.ret")
        linhas = [self.root.tree.item(i, "values") for i in self.root.tree.get_children()]
        self.assertEqual(len(linhas), 2)
        self.assertTrue(linhas[0][1].startswith("06 - "))
        self.assertEqual(linhas[0][2:5], ("NF-1001", "25/10/2026", "159,90"))
        self.assertIn("Pago: R$ 159,90", linhas[0][6])


class TrocaDeLayout(BaseInterface):
    def test_layout_de_outro_tamanho_avisa_e_mantem_o_atual(self):
        self.abrir("sicoob240_remessa.rem")
        with mock.patch.object(app.messagebox, "showwarning") as aviso:
            self.root.layout_var.set("CNAB400 Sicredi")
            self.root.on_layout_change()
        aviso.assert_called_once()
        self.assertEqual(self.root.layout_var.get(), "CNAB240 Sicoob")
        self.assertEqual(self.root.cnab_file.layout_key, "sicoob240")

    def test_troca_valida_reaplica_o_layout(self):
        self.abrir("sicoob400_remessa.rem")
        self.root.layout_var.set("CNAB400 FEBRABAN (Padrão)")
        self.root.on_layout_change()
        self.assertEqual(self.root.cnab_file.layout_key, "febraban")
        self.assertTrue(self.root.tree.get_children())


if __name__ == "__main__":
    unittest.main()
