"""Dica (tooltip) com o texto inteiro de uma célula cortada numa coluna do Treeview: passar o mouse sobre o
nome comprido de um arquivo mostra o nome completo."""
import tkinter as tk
import tkinter.font as tkfont

ATRASO_MS = 400        # espera antes de mostrar, para a dica não piscar ao passar o mouse de relance
MARGEM_CELULA = 12     # px que o Treeview usa de recuo dentro da célula
COR_FUNDO = "#ffffe1"  # amarelo claro, o padrão de dica do Windows


class DicaDaColuna:
    """Mostra, sobre `tree`, o texto inteiro da coluna `coluna` quando ele não cabe na largura da coluna."""

    def __init__(self, tree, coluna):
        self.tree = tree
        self.coluna = coluna
        self.fonte = tkfont.nametofont("TkDefaultFont")
        self.janela = None
        self._agendada = None
        self._linha = None
        tree.bind("<Motion>", self._ao_mover, add="+")
        tree.bind("<Leave>", lambda e: self.esconder(), add="+")
        tree.bind("<ButtonPress>", lambda e: self.esconder(), add="+")

    def texto_cortado(self, linha):
        """O texto da coluna na `linha` se ele não cabe na coluna; None se cabe inteiro."""
        texto = str(self.tree.set(linha, self.coluna))
        cabe = self.tree.column(self.coluna, "width") - MARGEM_CELULA
        return texto if self.fonte.measure(texto) > cabe else None

    def _ao_mover(self, evento):
        linha = self.tree.identify_row(evento.y)
        na_coluna = self.tree.identify_column(evento.x) == self._id_da_coluna()
        if not linha or not na_coluna:
            self.esconder()
            return
        if linha == self._linha:
            return
        self.esconder()
        texto = self.texto_cortado(linha)
        if texto:
            self._linha = linha
            self._agendada = self.tree.after(
                ATRASO_MS, lambda: self.mostrar(texto, evento.x_root + 12, evento.y_root + 18))

    def _id_da_coluna(self):
        """identify_column devolve "#1", "#2"... na ordem das colunas exibidas."""
        return f"#{list(self.tree['columns']).index(self.coluna) + 1}"

    def mostrar(self, texto, x, y):
        self._agendada = None
        self.janela = tk.Toplevel(self.tree)
        self.janela.wm_overrideredirect(True)
        self.janela.wm_geometry(f"+{x}+{y}")
        tk.Label(self.janela, text=texto, background=COR_FUNDO, relief="solid", borderwidth=1,
                 padx=4, pady=2).pack()

    def esconder(self):
        self._linha = None
        if self._agendada:
            self.tree.after_cancel(self._agendada)
            self._agendada = None
        if self.janela is not None:
            self.janela.destroy()
            self.janela = None
