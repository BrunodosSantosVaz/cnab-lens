"""Roda do mouse: rola a lista de arquivos e o painel de campos (Windows/macOS: <MouseWheel>; Linux X11:
botões 4 e 5), ligada explicitamente em cnablens.interface.rolagem.

A conta dos passos não precisa de tela. Os testes com a janela precisam de uma área de trabalho (escondida);
sem ela, são pulados. Rolar com a roda física no Windows continua sendo conferido à mão na homologação."""
import unittest
from unittest import mock

from test_interface import BaseInterface

from cnablens.interface.rolagem import LINHAS_POR_CLIQUE, passos_da_roda


class PassosDaRoda(unittest.TestCase):
    def test_windows_um_clique_rola_tres_linhas(self):
        self.assertEqual(LINHAS_POR_CLIQUE, 3)
        self.assertEqual(passos_da_roda(-120), 3)   # roda para baixo
        self.assertEqual(passos_da_roda(120), -3)   # roda para cima
        self.assertEqual(passos_da_roda(-360), 9)   # três cliques de uma vez

    def test_macos_delta_pequeno_ainda_rola_um_clique(self):
        self.assertEqual(passos_da_roda(-1), 3)
        self.assertEqual(passos_da_roda(2), -3)

    def test_sem_delta_nao_rola(self):
        self.assertEqual(passos_da_roda(0), 0)


class RodaNosPaineis(BaseInterface):
    def painel_de_campos(self):
        texto = self.abrir("santander240_retorno.ret").text
        texto.yview_moveto(0)
        self.root.update()
        return texto

    def gerar(self, widget, evento, **opcoes):
        widget.event_generate(evento, **opcoes)
        self.root.update()

    def test_painel_de_campos_windows_desce_e_sobe(self):
        texto = self.painel_de_campos()
        self.gerar(texto, "<MouseWheel>", delta=-120)
        self.assertGreater(texto.yview()[0], 0)
        self.gerar(texto, "<MouseWheel>", delta=120)
        self.assertEqual(texto.yview()[0], 0)

    def test_painel_de_campos_linux_botoes_5_e_4(self):
        texto = self.painel_de_campos()
        self.gerar(texto, "<Button-5>")
        self.assertGreater(texto.yview()[0], 0)
        self.gerar(texto, "<Button-4>")
        self.assertEqual(texto.yview()[0], 0)

    def test_um_clique_rola_so_uma_vez(self):
        # o bind devolve "break": o binding padrão do Tk não rola de novo (rolagem dobrada)
        texto = self.painel_de_campos()
        self.gerar(texto, "<MouseWheel>", delta=-120)
        uma_vez = texto.index("@0,0")
        texto.yview_moveto(0)
        texto.yview_scroll(LINHAS_POR_CLIQUE, "units")
        self.root.update()
        self.assertEqual(uma_vez, texto.index("@0,0"))

    def test_lista_de_arquivos_rola_pela_roda(self):
        # o Treeview só calcula a rolagem com a janela visível (aqui ela fica escondida): confere que a
        # roda chama a rolagem vertical com o passo certo, uma vez por evento
        tree = self.root.file_panel.tree
        eventos = (("<MouseWheel>", {"delta": -120}, 3), ("<MouseWheel>", {"delta": 240}, -6),
                   ("<Button-5>", {}, 3), ("<Button-4>", {}, -3))
        for evento, opcoes, passos in eventos:
            with self.subTest(evento=evento, **opcoes), mock.patch.object(tree, "yview_scroll") as rolar:
                self.gerar(tree, evento, **opcoes)
                rolar.assert_called_once_with(passos, "units")


if __name__ == "__main__":
    unittest.main()
