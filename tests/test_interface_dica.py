"""Lista de arquivos: passar o mouse sobre um nome comprido (cortado na coluna) mostra o nome completo numa
dica; nome que cabe inteiro não mostra nada.

Precisa de uma área de trabalho para criar a janela (escondida). Sem ela, os testes são pulados."""
import unittest
from unittest import mock

from test_interface import BaseInterface

from cnablens.interface import dica

NOME_CURTO = "a.ret"
NOME_COMPRIDO = "remessa_cobranca_santander_carteira_101_lote_000123_2026-09-29_versao_final.rem"


class Evento:
    def __init__(self, x=10, y=10):
        self.x, self.y, self.x_root, self.y_root = x, y, 100 + x, 100 + y


class DicaDoNomeDoArquivo(BaseInterface):
    def setUp(self):
        self.painel = self.root.file_panel
        self.tree = self.painel.tree
        self.tree.delete(*self.tree.get_children())
        self.tree.insert("", "end", iid="curto", values=(NOME_CURTO, "Remessa", "01/01 00:00"))
        self.tree.insert("", "end", iid="comprido", values=(NOME_COMPRIDO, "Remessa", "01/01 00:00"))
        self.addCleanup(self.painel.dica.esconder)

    def mover_sobre(self, linha, coluna="#1"):
        with mock.patch.object(self.tree, "identify_row", return_value=linha), \
                mock.patch.object(self.tree, "identify_column", return_value=coluna), \
                mock.patch.object(dica, "ATRASO_MS", 0):
            self.painel.dica._ao_mover(Evento())
            self.root.update()

    def texto_da_dica(self):
        janela = self.painel.dica.janela
        return janela.winfo_children()[0].cget("text") if janela else None

    def test_so_o_nome_cortado_vira_dica(self):
        self.assertEqual(self.painel.dica.texto_cortado("comprido"), NOME_COMPRIDO)
        self.assertIsNone(self.painel.dica.texto_cortado("curto"))

    def test_mouse_sobre_nome_comprido_mostra_o_nome_inteiro(self):
        self.mover_sobre("comprido")
        self.assertEqual(self.texto_da_dica(), NOME_COMPRIDO)

    def test_mouse_sobre_nome_curto_nao_mostra_dica(self):
        self.mover_sobre("curto")
        self.assertIsNone(self.texto_da_dica())

    def test_outra_coluna_ou_sair_da_lista_esconde(self):
        self.mover_sobre("comprido")
        self.mover_sobre("comprido", coluna="#2")  # coluna Tipo
        self.assertIsNone(self.texto_da_dica())
        self.mover_sobre("comprido")
        self.tree.event_generate("<Leave>")
        self.root.update()
        self.assertIsNone(self.texto_da_dica())

    def test_coluna_mais_larga_nao_corta(self):
        largura = self.tree.column("nome", "width")
        self.addCleanup(self.tree.column, "nome", width=largura)
        self.tree.column("nome", width=2000)
        self.assertIsNone(self.painel.dica.texto_cortado("comprido"))


if __name__ == "__main__":
    unittest.main()
