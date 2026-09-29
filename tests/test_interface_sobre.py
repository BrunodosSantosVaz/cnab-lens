"""Menu Ajuda → Sobre: janela com nome e versão, descrição, autor, licença e links do repositório, com os
mesmos textos do pyproject.toml (o executável não leva o pyproject.toml, por isso os textos ficam no módulo).

Os testes com a janela precisam de uma área de trabalho (escondida); sem ela, são pulados."""
import os
import unittest
from unittest import mock

import _caminho
from test_interface import BaseInterface

from cnablens.interface import app, sobre
from cnablens.version import __version__

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 (job de compatibilidade): o CI principal roda o teste
    tomllib = None


@unittest.skipIf(tomllib is None, "tomllib precisa do Python 3.11+")
class TextosIguaisAoPyproject(unittest.TestCase):
    def test_descricao_autor_licenca_e_links(self):
        with open(os.path.join(_caminho.RAIZ, "pyproject.toml"), "rb") as f:
            projeto = tomllib.load(f)["project"]
        self.assertEqual(sobre.DESCRICAO, projeto["description"])
        self.assertEqual(sobre.AUTOR, projeto["authors"][0]["name"])
        self.assertEqual(sobre.LICENCA, projeto["license"])
        self.assertEqual(sobre.REPOSITORIO, projeto["urls"]["Código"])
        self.assertEqual(sobre.ISSUES, projeto["urls"]["Issues"])


class MenuSobre(BaseInterface):
    def menu(self, rotulo):
        barra = self.root.nametowidget(self.root["menu"])
        for i in range(barra.index("end") + 1):
            if barra.type(i) == "cascade" and barra.entrycget(i, "label") == rotulo:
                return self.root.nametowidget(barra.entrycget(i, "menu"))
        self.fail(f"menu '{rotulo}' não está na barra")

    def abrir_sobre(self):
        dialogo = sobre.SobreDialog(self.root, app.TITULO_APP)
        dialogo.withdraw()  # como a janela principal nos testes: existe, mas não aparece na tela
        self.addCleanup(lambda: dialogo.winfo_exists() and dialogo.destroy())
        dialogo.update()
        return dialogo

    @staticmethod
    def textos(widget):
        """Todo texto de rótulos e campos dentro de `widget`."""
        for filho in widget.winfo_children():
            if filho.winfo_class() == "TLabel":
                yield str(filho.cget("text"))
            elif filho.winfo_class() == "TEntry":
                yield filho.get()
            yield from MenuSobre.textos(filho)

    def test_menu_ajuda_tem_o_item_sobre(self):
        ajuda = self.menu("Ajuda")
        self.assertEqual(ajuda.entrycget(0, "label"), "Sobre...")
        with mock.patch.object(sobre.SobreDialog, "mostrar") as mostrar:
            ajuda.invoke(0)
        mostrar.assert_called_once_with()
        for janela in self.root.winfo_children():  # a janela criada pelo teste
            if isinstance(janela, sobre.SobreDialog):
                janela.destroy()

    def test_janela_mostra_versao_descricao_autor_licenca_e_links(self):
        textos = "\n".join(self.textos(self.abrir_sobre()))
        for trecho in (f"CNABLens v{__version__}", sobre.DESCRICAO, sobre.AUTOR, f"Licença: {sobre.LICENCA}",
                       sobre.REPOSITORIO, sobre.ISSUES):
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, textos)

    def test_links_sao_so_leitura(self):
        for campo in self.abrir_sobre().links:
            with self.subTest(campo=campo.get()):
                self.assertEqual(str(campo.cget("state")), "readonly")

    @staticmethod
    def botao(widget, texto):
        for filho in widget.winfo_children():
            if filho.winfo_class() == "TButton" and filho.cget("text") == texto:
                return filho
            achado = MenuSobre.botao(filho, texto)
            if achado:
                return achado
        return None

    def test_janela_fixa_e_fecha_pelo_botao_esc_ou_enter(self):
        dialogo = self.abrir_sobre()
        self.assertEqual(dialogo.title(), "Sobre o CNABLens")
        self.assertEqual(dialogo.resizable(), (False, False))
        # com a janela escondida o Tk não entrega teclas: confere que Esc e Enter estão ligados
        self.assertTrue(dialogo.bind("<Escape>"))
        self.assertTrue(dialogo.bind("<Return>"))
        self.botao(dialogo, "Fechar").invoke()
        self.root.update()
        self.assertFalse(dialogo.winfo_exists())


if __name__ == "__main__":
    unittest.main()
