"""Painel de campos: Campo / Posição / Valor / Descrição do registro ou lançamento selecionado, com
seleção e cópia do texto."""
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from cnablens.formatacao import DATA_KEYWORDS, MOEDA_KEYWORDS, formatar_valor_campo
from cnablens.interface.estilo import configure_zebra_tags, zebra_tags


class DetailPanel(ttk.Frame):
    """Painel inferior: Campo / Posição / Valor / Descrição do registro
    selecionado.

    Usa um widget Text somente-leitura em vez de um Treeview porque o Treeview
    não deixa selecionar texto: aqui o usuário seleciona qualquer trecho com o
    mouse e copia com Ctrl+C. Duplo clique seleciona a célula inteira (o valor
    de um campo, o nome, a descrição...). O cabeçalho das colunas é um segundo
    Text de uma linha, alinhado com o corpo e rolado junto na horizontal."""

    HEADERS = ("Campo", "Posição", "Valor", "Descrição")
    PADDING_COLUNA = 26  # px entre o fim do texto de uma coluna e o início da próxima
    COR_CABECALHO = "#e6e9ee"
    COR_SEPARADOR = "#d5e2f7"
    TABS_PADRAO = (300, 380, 700, 1300)  # antes de haver um registro para medir

    def __init__(self, master):
        super().__init__(master)
        base = tkfont.nametofont("TkDefaultFont")
        self.font = base.copy()
        self.font_bold = base.copy()
        self.font_bold.configure(weight="bold")
        self._cells = {}  # nº da linha no Text -> [(col_inicio, col_fim), ...] de cada célula

        self.head = tk.Text(
            self, height=1, wrap="none", font=self.font_bold, background=self.COR_CABECALHO,
            relief="flat", borderwidth=1, highlightthickness=0, padx=4, pady=3,  # borda 1 = mesmo recuo do corpo
            insertwidth=0, cursor="arrow", takefocus=0,
        )
        self.text = tk.Text(
            self, wrap="none", font=self.font, height=10, relief="solid", borderwidth=1,
            highlightthickness=0, padx=4, pady=2, insertwidth=0, undo=False,
            selectbackground="#3a86ff", selectforeground="#ffffff",
            inactiveselectbackground="#3a86ff",  # a seleção continua visível ao clicar em outro lugar
        )
        configure_zebra_tags(self.text)
        self.text.tag_configure("sep", background=self.COR_SEPARADOR, foreground="#0a2a66", font=self.font_bold)

        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self._on_hscroll)
        self.text.configure(yscrollcommand=self.vsb.set, xscrollcommand=self._on_text_xscroll)
        self.head.grid(row=0, column=0, sticky="ew")
        self.text.grid(row=1, column=0, sticky="nsew")
        self.vsb.grid(row=1, column=1, sticky="ns")
        self.hsb.grid(row=2, column=0, sticky="ew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Somente leitura, mas com seleção e cópia: em vez de state="disabled"
        # (que em alguns casos não deixa nem focar/selecionar), o Text fica
        # editável e toda tecla que alteraria o conteúdo é bloqueada.
        self.text.bind("<Key>", self._on_key)
        self.text.bind("<Button-2>", lambda e: "break")  # colar com botão do meio
        self.text.bind("<Control-a>", self._select_all)
        self.text.bind("<Control-A>", self._select_all)
        self.text.bind("<Double-Button-1>", self._on_double_click)
        for seq in ("<Button-1>", "<B1-Motion>", "<Double-Button-1>", "<Triple-Button-1>"):
            self.head.bind(seq, lambda e: "break")
        self._render_header(self.TABS_PADRAO)

    # -- comportamento somente leitura -------------------------------------

    _TECLAS_LIVRES = {
        "Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next",
        "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
    }

    def _on_key(self, event):
        if event.keysym in self._TECLAS_LIVRES:
            return None
        ctrl = bool(event.state & 0x4)
        if ctrl and event.keysym.lower() in ("c", "insert"):
            return None
        return "break"

    def _select_all(self, _event=None):
        self.text.tag_add("sel", "1.0", "end-1c")
        return "break"

    def _on_double_click(self, event):
        """Duplo clique seleciona a célula inteira sob o cursor."""
        linha, coluna = (int(p) for p in self.text.index(f"@{event.x},{event.y}").split("."))
        for inicio, fim in self._cells.get(linha, ()):
            if inicio <= coluna < fim:
                self.text.tag_remove("sel", "1.0", "end")
                self.text.tag_add("sel", f"{linha}.{inicio}", f"{linha}.{fim}")
                self.text.mark_set("insert", f"{linha}.{inicio}")
                self.text.focus_set()
                return "break"
        return None

    # -- rolagem horizontal (corpo e cabeçalho juntos) ---------------------

    def _on_hscroll(self, *args):
        self.text.xview(*args)
        self.head.xview_moveto(self.text.xview()[0])

    def _on_text_xscroll(self, first, last):
        self.hsb.set(first, last)
        self.head.xview_moveto(first)

    # -- desenho -----------------------------------------------------------

    def _render_header(self, tabs):
        self.head.configure(state="normal", tabs=tabs)
        self.head.delete("1.0", "end")
        self.head.insert("end", "\t".join(self.HEADERS) + "\t")
        self.head.configure(state="disabled")

    def show_record(self, record, moeda_fields=MOEDA_KEYWORDS, data_fields=DATA_KEYWORDS):
        """`record` é um CnabRecord ou CnabGroup (qualquer coisa com .fields)."""
        self.text.delete("1.0", "end")
        self._cells = {}
        if record is None:
            self.text.configure(tabs=self.TABS_PADRAO)
            self._render_header(self.TABS_PADRAO)
            return

        medidas = [[], [], []]
        campos = []
        for f in record.fields:
            if f.get("separador"):
                campos.append(f)
                continue
            valor = formatar_valor_campo(f["nome"], f["valor"], moeda_fields, data_fields)
            posicao = f"{f['inicio']}-{f['fim']}"
            campos.append({**f, "_valor": valor, "_posicao": posicao})
            medidas[0].append(self.font.measure(f["nome"]))
            medidas[1].append(self.font.measure(posicao))
            medidas[2].append(self.font.measure(valor))

        pad = self.PADDING_COLUNA
        larguras = [
            max([self.font_bold.measure(self.HEADERS[i])] + medidas[i]) + pad for i in range(3)
        ]
        x1 = larguras[0]
        x2 = x1 + larguras[1]
        x3 = x2 + larguras[2]
        largura_descr = max(
            [self.font_bold.measure(self.HEADERS[3])]
            + [self.font.measure(f.get("descricao", "")) for f in campos if not f.get("separador")]
        )
        largura_total = x3 + largura_descr + pad
        tabs = (x1, x2, x3, largura_total)
        self.text.configure(tabs=tabs)
        self._render_header(tabs)

        n_linha = 0
        for i, f in enumerate(campos):
            n_linha += 1
            if f.get("separador"):
                texto = f["nome"]
                self.text.insert("end", texto + "\n", ("sep",))
                self._cells[n_linha] = [(0, len(texto))]
                continue
            partes = (f["nome"], f["_posicao"], f["_valor"], f.get("descricao", ""))
            texto = "\t".join(partes) + "\t"  # o último \t iguala a largura de todas as linhas
            celulas, col = [], 0
            for p in partes:
                celulas.append((col, col + len(p)))
                col += len(p) + 1
            nome_lower = f["nome"].lower()
            is_filler = "uso reservado" in nome_lower or "filler" in nome_lower
            self.text.insert("end", texto + "\n", zebra_tags(i, is_filler))
            self._cells[n_linha] = celulas
        self.text.tag_raise("sel")
        self.text.xview_moveto(0)
        self.head.xview_moveto(0)
