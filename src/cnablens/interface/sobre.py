"""Janela "Sobre o CNABLens" (menu Ajuda → Sobre): nome e versão, descrição, autor, licença e os links do
repositório, sem abrir navegador nem acessar a rede (o programa é 100% local).

Os textos são os do pyproject.toml. Ficam aqui porque o executável não leva o pyproject.toml; o teste
tests/test_interface_sobre.py confere que continuam iguais aos de lá."""
import tkinter as tk
from tkinter import ttk

DESCRICAO = ("Uma lente para arquivos CNAB: leitor de remessa e retorno CNAB400/240 (FEBRABAN, Sicredi, "
             "Sicoob, Santander) para Windows e Linux")
AUTOR = "Bruno dos Santos Vaz"
LICENCA = "MIT"
REPOSITORIO = "https://github.com/BrunodosSantosVaz/cnab-lens"
ISSUES = "https://github.com/BrunodosSantosVaz/cnab-lens/issues"


class SobreDialog(tk.Toplevel):
    """Modal pequeno, no padrão do ExtensionDialog: centralizado sobre a janela principal, sem redimensionar,
    fecha com Esc, Enter ou o botão Fechar. Os links ficam em campos só de leitura, para selecionar e copiar."""

    LARGURA_TEXTO = 380  # px: quebra da descrição

    def __init__(self, master, titulo_app):
        super().__init__(master)
        self.title("Sobre o CNABLens")
        self.resizable(False, False)
        self.transient(master)

        corpo = ttk.Frame(self, padding=(20, 16, 20, 8))
        corpo.pack(fill="both", expand=True)
        ttk.Label(corpo, text=titulo_app, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(corpo, text=DESCRICAO, wraplength=self.LARGURA_TEXTO, justify="left").pack(
            anchor="w", pady=(6, 10))
        ttk.Label(corpo, text=f"Autor: {AUTOR}").pack(anchor="w")
        ttk.Label(corpo, text=f"Licença: {LICENCA}").pack(anchor="w", pady=(0, 10))
        self.links = [self._link(corpo, rotulo, url) for rotulo, url in (
            ("Repositório (código, downloads e documentação):", REPOSITORIO),
            ("Dúvidas, sugestões e problemas (abrir uma issue):", ISSUES),
        )]

        botoes = ttk.Frame(self, padding=(20, 4, 20, 16))
        botoes.pack(fill="x")
        ttk.Button(botoes, text="Fechar", command=self.destroy, default="active").pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self.destroy())

        self.tk.call("tk::PlaceWindow", self._w, "widget", master._w)  # centraliza sobre a janela principal

    @staticmethod
    def _link(master, rotulo, url):
        ttk.Label(master, text=rotulo).pack(anchor="w")
        campo = ttk.Entry(master, width=len(url) + 2)
        campo.insert(0, url)
        campo.configure(state="readonly")  # dá para selecionar e copiar, não para editar
        campo.pack(anchor="w", fill="x", pady=(2, 8))
        return campo

    def mostrar(self):
        """Abre como modal: bloqueia a janela principal até fechar."""
        self.grab_set()
        self.focus_set()
        self.wait_window(self)
