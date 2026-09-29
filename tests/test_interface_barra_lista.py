"""Lista de arquivos: a barra de rolagem vertical aparece desde a abertura, mesmo com o painel estreito
(antes, com pack, o Treeview tomava toda a largura e a barra só surgia ao alargar a seção).

Precisa de uma área de trabalho para criar a janela (escondida). Sem ela, os testes são pulados."""
import unittest

from test_interface import BaseInterface


class BarraDaListaDeArquivos(BaseInterface):
    def largura_da_barra(self, largura_do_painel):
        self.root.paned.sashpos(0, largura_do_painel)
        self.root.update()
        return self.root.file_panel.vsb.winfo_width()

    def test_barra_visivel_com_o_painel_estreito(self):
        painel = self.root.file_panel
        for largura in (120, 200, 300):
            with self.subTest(largura=largura):
                self.assertGreater(self.largura_da_barra(largura), 5)
                # a barra fica dentro do painel, à direita da lista
                fim_da_barra = painel.vsb.winfo_x() + painel.vsb.winfo_width()
                self.assertLessEqual(fim_da_barra, painel.vsb.master.winfo_width())
                self.assertGreaterEqual(painel.vsb.winfo_x(), painel.tree.winfo_x() + painel.tree.winfo_width())

    def test_lista_ocupa_o_resto_da_largura(self):
        self.largura_da_barra(300)
        painel = self.root.file_panel
        self.assertEqual(painel.tree.winfo_width() + painel.vsb.winfo_width(), painel.vsb.master.winfo_width())


if __name__ == "__main__":
    unittest.main()
