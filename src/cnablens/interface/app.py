"""Janela principal do CNABLens: escolher a pasta, listar os arquivos, ler o arquivo selecionado e
mostrar o resumo, a grade de lançamentos e o painel de campos, com o seletor de layout.

A janela só organiza a tela: a leitura fica em cnablens.leitura, a formatação em cnablens.formatacao e os
layouts em cnablens.layouts."""
import contextlib
import os
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from cnablens import layouts
from cnablens.formatacao import DATA_KEYWORDS, MOEDA_KEYWORDS, format_data, format_valor_monetario
from cnablens.interface.estilo import configure_zebra_tags, zebra_tags
from cnablens.interface.lista_arquivos import FileListPanel
from cnablens.interface.painel_campos import DetailPanel
from cnablens.interface.sobre import SobreDialog
from cnablens.leitura import CnabFile
from cnablens.version import __version__

TITULO_APP = f"CNABLens v{__version__}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITULO_APP)
        # Nunca abrir maior do que a tela: numa tela menor (ex.: notebook
        # 1366x768), pedir uma janela de 1440x820 faz o Windows posicionar
        # parte de baixo (barra de rolagem horizontal, barra de status) fora
        # da área visível. Limita ao tamanho da tela, com uma margem.
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = min(1440, max(1000, screen_w - 80))
        win_h = min(820, max(650, screen_h - 100))
        self.geometry(f"{win_w}x{win_h}")
        self.minsize(1000, 620)

        self.cnab_file = None
        self._last_lancamento_iid = None
        self._build_menu()
        self._build_layout()

    def _build_menu(self):
        menubar = tk.Menu(self)
        arquivo_menu = tk.Menu(menubar, tearoff=0)
        arquivo_menu.add_command(label="Selecionar pasta...", command=self.abrir_pasta, accelerator="Ctrl+O")
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label="Sair", command=self.destroy)
        menubar.add_cascade(label="Arquivo", menu=arquivo_menu)
        ajuda_menu = tk.Menu(menubar, tearoff=0)
        ajuda_menu.add_command(label="Sobre...", command=self.mostrar_sobre)
        menubar.add_cascade(label="Ajuda", menu=ajuda_menu)
        self.config(menu=menubar)
        self.bind_all("<Control-o>", lambda e: self.abrir_pasta())

    def mostrar_sobre(self):
        SobreDialog(self, TITULO_APP).mostrar()

    def _build_layout(self):
        # A janela toda usa grid (não pack) nas 4 faixas principais, pra
        # controlar com precisão quanto de altura cada uma recebe:
        # 0 barra de ferramentas (fixa) / 1 grade de cima (arquivos+lançamentos,
        # peso 3) / 2 painel de detalhe, largura total (peso 2) / 3 status (fixa).
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=2)

        self._build_toolbar()
        self._build_body()
        self._build_detail_section()
        self._build_status()

        # Posiciona o divisor do PanedWindow a 1/4 da largura (o usuário
        # pode arrastar livremente depois). Só dá pra calcular a largura
        # real depois que o Tk terminou de desenhar a janela.
        self.update_idletasks()
        self._definir_posicao_inicial_paned()

    def _build_toolbar(self):
        """Barra única no topo: TODOS os controles ficam aqui (selecionar
        pasta, escolher/atualizar extensão, escolher layout de campos) mais
        o resumo do arquivo atualmente aberto - nada disso fica espalhado
        pelo resto da tela."""
        top = ttk.Frame(self, padding=(10, 8))
        top.grid(row=0, column=0, sticky="ew")

        self.btn_pasta = ttk.Button(top, text="📁 Selecionar pasta...", command=self.abrir_pasta)
        self.btn_pasta.pack(side="left")

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=12)

        ttk.Label(top, text="Mostrar:").pack(side="left")
        self.pasta_ext_var = tk.StringVar()
        self.ext_combo = ttk.Combobox(
            top, textvariable=self.pasta_ext_var, state="disabled", width=16,
        )
        self.ext_combo.pack(side="left", padx=(6, 6))
        self.ext_combo.bind("<<ComboboxSelected>>", self._on_pasta_ext_change)

        self.pasta_count_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.pasta_count_var, foreground="#777777").pack(side="left", padx=(0, 6))

        self.btn_refresh = ttk.Button(
            top, text="⟳ Atualizar", width=11, command=self._atualizar_pasta, state="disabled")
        self.btn_refresh.pack(side="left")

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=12)

        ttk.Label(top, text="Layout de campos:").pack(side="left")
        self.layout_var = tk.StringVar(value=layouts.LAYOUTS[layouts.DEFAULT_LAYOUT_KEY].label)
        self.layout_combo = ttk.Combobox(
            top, textvariable=self.layout_var, values=layouts.layout_labels(),
            state="disabled", width=24,
        )
        self.layout_combo.pack(side="left", padx=(6, 0))
        self.layout_combo.bind("<<ComboboxSelected>>", self.on_layout_change)

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=12)

        self.info_var = tk.StringVar(value="Nenhum arquivo carregado.")
        ttk.Label(top, textvariable=self.info_var, justify="left").pack(side="left")

    def _build_body(self):
        """Grade de cima: painel esquerdo (arquivos da pasta, ~1/4 da
        largura) e painel direito (lançamentos do arquivo selecionado,
        ~3/4). Só esta faixa é dividida - o painel de detalhe fica de fora,
        em largura total (ver _build_detail_section)."""
        body = ttk.Frame(self, padding=(10, 0))
        body.grid(row=1, column=0, sticky="nsew")

        self.paned = ttk.PanedWindow(body, orient="horizontal")
        self.paned.pack(fill="both", expand=True)

        self.file_panel = FileListPanel(
            self.paned, on_file_selected=self.carregar_arquivo,
            ext_var=self.pasta_ext_var, count_var=self.pasta_count_var,
            on_extensoes_disponiveis=self._on_extensoes_disponiveis,
        )
        self.paned.add(self.file_panel, weight=1)

        # Treeview de lançamentos (registros detalhe) + botões Header/Trailer/Voltar
        mid = ttk.Frame(self.paned)
        self.paned.add(mid, weight=3)

        self.columns = ("seq", "ocorrencia", "documento", "vencimento", "valor", "nosso_numero", "info")
        self.tree = ttk.Treeview(mid, columns=self.columns, show="headings", selectmode="browse")
        headers = {
            "seq": "#",
            "ocorrencia": "Ocorrência",
            "documento": "Nº Documento",
            "vencimento": "Vencimento",
            "valor": "Valor Título (R$)",
            "nosso_numero": "Nosso Número",
            "info": "Sacado / Info",
        }
        widths = {"seq": 40, "ocorrencia": 190, "documento": 110, "vencimento": 90,
                  "valor": 110, "nosso_numero": 120, "info": 200}
        for c in self.columns:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c], anchor="w")
        configure_zebra_tags(self.tree)

        vsb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        mid.grid_rowconfigure(0, weight=1)
        mid.grid_columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_lancamento)
        self.tree.bind("<Control-c>", self._copiar_linha_lancamento)

        btns = ttk.Frame(mid)
        btns.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.btn_header = ttk.Button(btns, text="Ver Header do arquivo", command=self.mostrar_header, state="disabled")
        self.btn_header.pack(side="left")
        self.btn_trailer = ttk.Button(
            btns, text="Ver Trailer do arquivo", command=self.mostrar_trailer, state="disabled")
        self.btn_trailer.pack(side="left", padx=8)
        self.btn_voltar = ttk.Button(
            btns, text="← Voltar aos Lançamentos", command=self.voltar_lancamento, state="disabled",
        )
        self.btn_voltar.pack(side="left", padx=8)

    def _build_detail_section(self):
        """Painel de detalhe (Campo/Posição/Valor/Descrição): largura total
        da janela, embaixo da grade de cima - fica largo de propósito porque
        a coluna Descrição é comprida."""
        section = ttk.Frame(self, padding=(10, 8, 10, 0))
        section.grid(row=2, column=0, sticky="nsew")
        section.grid_rowconfigure(1, weight=1)
        section.grid_columnconfigure(0, weight=1)

        detail_label = ttk.Label(
            section, text="Detalhe do registro selecionado (todos os campos, com posição no layout):",
            font=("Segoe UI", 9, "bold"),
        )
        detail_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.detail_panel = DetailPanel(section)
        self.detail_panel.grid(row=1, column=0, sticky="nsew")

    def _build_status(self):
        status = ttk.Frame(self, padding=(10, 4))
        status.grid(row=3, column=0, sticky="ew")
        self.status_var = tk.StringVar(value="Pronto.")
        ttk.Label(status, textvariable=self.status_var).pack(side="left")

    def _definir_posicao_inicial_paned(self):
        self._paned_after = None
        largura = self.paned.winfo_width()
        if largura > 100:
            self.paned.sashpos(0, largura // 4)
        else:
            self._paned_after = self.after(50, self._definir_posicao_inicial_paned)

    def destroy(self):
        if getattr(self, "_paned_after", None):  # não deixar um after pendente para a janela já fechada
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._paned_after)
        super().destroy()

    def abrir_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta com os arquivos CNAB400")
        if not pasta:
            return
        nome_pasta = os.path.basename(pasta.rstrip("/\\")) or pasta
        self.title(f"{TITULO_APP} — {nome_pasta}")
        self.file_panel.carregar_pasta(pasta)

    def _atualizar_pasta(self):
        self.file_panel.atualizar()

    def _on_pasta_ext_change(self, _event=None):
        self.file_panel.aplicar_extensao_por_rotulo(self.pasta_ext_var.get())

    def _on_extensoes_disponiveis(self, labels, rotulo_selecionado):
        """Callback do FileListPanel: atualiza o combobox 'Mostrar' da barra
        de ferramentas com as extensões encontradas na pasta escaneada."""
        if labels:
            self.ext_combo.config(values=labels, state="readonly")
            self.btn_refresh.config(state="normal")
        else:
            self.ext_combo.config(values=[], state="disabled")
            self.btn_refresh.config(state="disabled")
        self.pasta_ext_var.set(rotulo_selecionado)

    def carregar_arquivo(self, path):
        """Callback chamado pelo FileListPanel quando o usuário clica num
        arquivo da lista à esquerda - carrega esse arquivo no resto da tela."""
        try:
            self.cnab_file = CnabFile(path)
        except Exception as exc:
            traceback.print_exc()
            messagebox.showerror("Erro ao ler arquivo", f"Não foi possível interpretar o arquivo:\n\n{exc}")
            return
        self.layout_combo.config(state="readonly")
        self.layout_var.set(self.cnab_file.layout.label)
        self._popular_ui()

    def on_layout_change(self, _event=None):
        if self.cnab_file is None:
            return
        key = layouts.key_for_label(self.layout_var.get())
        novo = layouts.LAYOUTS[key]
        if novo.width != self.cnab_file.width:
            # layout de 240 posições num arquivo de 400 (ou vice-versa) só daria lixo
            messagebox.showwarning(
                "Layout incompatível",
                f"O arquivo aberto tem linhas de {self.cnab_file.width} posições e o layout "
                f"\"{novo.label}\" é de {novo.width}.\n\nEscolha um layout de "
                f"{self.cnab_file.width} posições, ou abra um arquivo de {novo.width}.",
            )
            self.layout_var.set(self.cnab_file.layout.label)
            return
        self.cnab_file.apply_layout(key)
        self._popular_ui()

    def _popular_ui(self):
        cf = self.cnab_file
        self.tree.delete(*self.tree.get_children())
        self.detail_panel.show_record(None)

        nome_arquivo = os.path.basename(cf.path)
        info_txt = (
            f"Arquivo: {nome_arquivo}    |    Tipo: {cf.tipo_arquivo} (CNAB{cf.width})    |    "
            f"Banco: {cf.banco_codigo} - {cf.banco_nome or '(não identificado)'}    |    "
            f"Empresa: {cf.empresa_nome or '-'}    |    Data geração: {cf.data_geracao or '-'}    |    "
            f"Lançamentos: {len(cf.detalhes)}"
        )
        self.info_var.set(info_txt)
        self.status_var.set(
            f"{len(cf.records)} linha(s) lidas ({cf.encoding_used}). "
            f"{len(cf.detalhes)} registro(s) de detalhe, "
            f"header {'encontrado' if cf.header else 'NÃO encontrado'}, "
            f"trailer {'encontrado' if cf.trailer else 'NÃO encontrado'}    |    "
            f"Layout: {cf.layout.label}."
        )

        self.btn_header.config(state="normal" if cf.header else "disabled")
        self.btn_trailer.config(state="normal" if cf.trailer else "disabled")
        self.btn_voltar.config(state="normal" if cf.detalhes else "disabled")
        self._last_lancamento_iid = None

        is_retorno = cf.tipo_arquivo == "Retorno"
        ocorrencia_codes = cf.layout.ocorrencia_codes if is_retorno else (cf.layout.comando_codes or {})
        self._record_by_iid = {}
        for i, rec in enumerate(cf.detalhes):
            ocorrencia_cod = (
                rec.get("Código da Ocorrência") or rec.get("Identificação da Ocorrência")
                or rec.get("Código de Movimento") or rec.get("Ocorrência") or rec.get("comando")
            )
            ocorrencia_desc = ocorrencia_codes.get(ocorrencia_cod, "")
            ocorrencia_txt = f"{ocorrencia_cod} - {ocorrencia_desc}" if ocorrencia_desc else (ocorrencia_cod or "")

            documento = rec.get("Número do Documento") or rec.get("Seu Número")
            vencimento = format_data(rec.get("Data de Vencimento"))
            valor_raw = rec.get("Valor Nominal") or rec.get("Valor do Título")
            valor_fmt = format_valor_monetario(valor_raw) if valor_raw else ""
            nosso_numero = rec.get_concat("Nosso Número [") or rec.get("Nosso Número")
            if is_retorno:
                pago_raw = rec.get("Pago", "0")
                info = f"Pago: R$ {format_valor_monetario(pago_raw)}" if pago_raw.strip("0") else ""
            else:
                info = rec.get("Nome do Sacado") or rec.get("Nome do Pagador")

            iid = f"rec-{rec.index}"
            self._record_by_iid[iid] = rec
            self.tree.insert(
                "", "end", iid=iid,
                values=(rec.index, ocorrencia_txt, documento, vencimento, valor_fmt, nosso_numero, info),
                tags=zebra_tags(i),
            )

        if cf.detalhes:
            first_iid = f"rec-{cf.detalhes[0].index}"
            self.tree.selection_set(first_iid)
            self.tree.focus(first_iid)

    def on_select_lancamento(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        self._last_lancamento_iid = sel[0]
        rec = self._record_by_iid.get(sel[0])
        self.detail_panel.show_record(rec, MOEDA_KEYWORDS, DATA_KEYWORDS)

    def _copiar_linha_lancamento(self, _event=None):
        """Ctrl+C na grade de lançamentos: copia a linha selecionada (colunas
        separadas por tab, então cola direto numa planilha)."""
        sel = self.tree.selection()
        if not sel:
            return "break"
        valores = self.tree.item(sel[0], "values")
        self.clipboard_clear()
        self.clipboard_append("\t".join(str(v) for v in valores))
        return "break"

    def voltar_lancamento(self):
        """Reseleciona o último lançamento visto antes de abrir Header/Trailer,
        ou o primeiro lançamento do arquivo, e mostra seus campos de novo."""
        if not self.cnab_file or not self.cnab_file.detalhes:
            return
        iid = self._last_lancamento_iid
        if not iid or not self.tree.exists(iid):
            iid = f"rec-{self.cnab_file.detalhes[0].index}"
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self.tree.see(iid)

    def mostrar_header(self):
        if self.cnab_file and self.cnab_file.header:
            self.tree.selection_remove(*self.tree.selection())
            self.detail_panel.show_record(self.cnab_file.header, MOEDA_KEYWORDS, DATA_KEYWORDS)

    def mostrar_trailer(self):
        if self.cnab_file and self.cnab_file.trailer:
            self.tree.selection_remove(*self.tree.selection())
            self.detail_panel.show_record(self.cnab_file.trailer, MOEDA_KEYWORDS, DATA_KEYWORDS)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
