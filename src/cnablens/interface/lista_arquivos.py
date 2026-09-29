"""Lista de arquivos da pasta (com filtro por extensão e o tipo de cada arquivo) e o diálogo que pergunta
qual extensão listar."""
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from cnablens.interface.dica import DicaDaColuna
from cnablens.interface.estilo import configure_zebra_tags, zebra_tags
from cnablens.leitura.pasta import escanear_pasta, peek_tipo_arquivo


class ExtensionDialog(tk.Toplevel):
    """Modal exibido ao selecionar uma pasta com mais de um tipo de arquivo:
    pergunta qual extensão listar. Só some depois de OK/Cancelar - o usuário
    também pode trocar de extensão depois, sem reabrir este modal, pelo
    combobox "Mostrar" do painel de arquivos."""

    def __init__(self, master, opcoes):
        # opcoes: lista de (rotulo, valor, contagem); valor=None = "Todos os arquivos"
        super().__init__(master)
        self.title("Formato dos arquivos")
        self.resizable(False, False)
        self.transient(master)
        self.confirmado = False
        self.resultado = None

        ttk.Label(
            self, text="Esta pasta tem mais de um tipo de arquivo.\nQual formato você quer listar?",
            font=("Segoe UI", 9, "bold"), justify="left",
        ).pack(anchor="w", padx=18, pady=(16, 10))

        opcoes_frame = ttk.Frame(self)
        opcoes_frame.pack(fill="both", expand=True, padx=18)

        self.var = tk.StringVar(value=opcoes[0][1] if opcoes else "")
        for rotulo, valor, contagem in opcoes:
            texto = f"{rotulo}   ({contagem} arquivo{'s' if contagem != 1 else ''})"
            ttk.Radiobutton(opcoes_frame, text=texto, value=valor, variable=self.var).pack(
                anchor="w", pady=3,
            )

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=18, pady=(14, 16))
        ttk.Button(btns, text="OK", command=self._confirmar, default="active").pack(side="right")
        ttk.Button(btns, text="Cancelar", command=self._cancelar).pack(side="right", padx=(0, 8))

        self.bind("<Return>", lambda e: self._confirmar())
        self.bind("<Escape>", lambda e: self._cancelar())
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

        self.update_idletasks()
        self._centralizar(master)
        self.grab_set()
        self.focus_set()
        self.wait_window(self)

    def _centralizar(self, master):
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _confirmar(self):
        self.confirmado = True
        self.resultado = self.var.get() or None
        self.destroy()

    def _cancelar(self):
        self.confirmado = False
        self.destroy()


class FileListPanel(ttk.Frame):
    """Painel esquerdo (1/4 da grade de cima): só a grade de arquivos CNAB400
    de uma pasta, filtrados por extensão. Os controles (selecionar pasta,
    escolher extensão, atualizar) ficam todos juntos na barra de ferramentas
    do App, no topo da janela - este painel só cuida da lista em si e do
    estado por trás dela (pasta atual, extensão atual, ordenação). Clicar num
    arquivo carrega ele no restante da tela (via o callback on_file_selected)."""

    def __init__(self, master, on_file_selected, ext_var, count_var, on_extensoes_disponiveis):
        super().__init__(master, padding=(0, 0, 10, 0))
        self.on_file_selected = on_file_selected
        self.ext_var = ext_var
        self.count_var = count_var
        self.on_extensoes_disponiveis = on_extensoes_disponiveis

        self.folder = None
        self.arquivos = []
        self.extensao_atual = None
        self._label_para_ext = {}
        self._current_path = None
        self._sort_col = "modificado"
        self._sort_reverse = True

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        columns = ("nome", "tipo", "modificado")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("nome", text="Arquivo", command=lambda: self._sort_by("nome"))
        self.tree.heading("tipo", text="Tipo", command=lambda: self._sort_by("tipo"))
        self.tree.heading("modificado", text="Modificado", command=lambda: self._sort_by("modificado"))
        self.tree.column("nome", width=170, anchor="w")
        self.tree.column("tipo", width=56, anchor="center", stretch=False)
        self.tree.column("modificado", width=96, anchor="center", stretch=False)
        configure_zebra_tags(self.tree)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)
        self.dica = DicaDaColuna(self.tree, "nome")  # nome comprido, cortado na coluna: mostra inteiro

    # -- carregamento -----------------------------------------------------

    def carregar_pasta(self, folder_path):
        self.folder = folder_path
        self._current_path = None
        self._rescan(mostrar_dialog=True)

    def atualizar(self):
        if self.folder:
            self._rescan(mostrar_dialog=False)

    def aplicar_extensao_por_rotulo(self, rotulo):
        """Chamado pelo App quando o usuário troca o combobox 'Mostrar' da
        barra de ferramentas - reaplica o filtro sem reler a pasta do disco."""
        self.extensao_atual = self._label_para_ext.get(rotulo)
        self._render_lista()

    def _rescan(self, mostrar_dialog):
        try:
            arquivos = escanear_pasta(self.folder)
        except OSError as exc:
            messagebox.showerror("Erro ao abrir pasta", f"Não foi possível ler a pasta:\n\n{exc}")
            return

        self.arquivos = arquivos

        contagem = {}
        for a in arquivos:
            contagem[a["ext"]] = contagem.get(a["ext"], 0) + 1
        extensoes_ordenadas = sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0]))

        if not extensoes_ordenadas:
            self._label_para_ext = {}
            self.extensao_atual = None
            self.on_extensoes_disponiveis([], "")
            self._render_lista()
            return

        label_todos = f"Todos os arquivos  ({len(arquivos)})"
        self._label_para_ext = {label_todos: None}
        labels = []
        for ext, n in extensoes_ordenadas:
            rotulo = f"{ext}  ({n})"
            self._label_para_ext[rotulo] = ext
            labels.append(rotulo)
        labels.append(label_todos)

        escolha = self.extensao_atual
        ext_ainda_existe = any(escolha == ext for ext, _ in extensoes_ordenadas)

        if mostrar_dialog:
            if len(extensoes_ordenadas) == 1:
                # só um tipo de arquivo na pasta: nada para perguntar, aplica direto.
                escolha = extensoes_ordenadas[0][0]
            else:
                opcoes = [(ext, ext, n) for ext, n in extensoes_ordenadas]
                opcoes.append(("Todos os arquivos", None, len(arquivos)))
                dialog = ExtensionDialog(self.winfo_toplevel(), opcoes)
                escolha = dialog.resultado if dialog.confirmado else None
        elif not ext_ainda_existe:
            # "Atualizar": a extensão escolhida antes sumiu da pasta -> mostra tudo.
            escolha = None

        self.extensao_atual = escolha
        rotulo_atual = next((lbl for lbl, ext in self._label_para_ext.items() if ext == escolha), label_todos)
        self.on_extensoes_disponiveis(labels, rotulo_atual)
        self._render_lista()

    def _filtrados(self):
        if self.extensao_atual is None:
            return list(self.arquivos)
        return [a for a in self.arquivos if a["ext"] == self.extensao_atual]

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = col == "modificado"
        self._render_lista()

    def _render_lista(self):
        self.tree.delete(*self.tree.get_children())
        itens = self._filtrados()
        for item in itens:
            if item["tipo"] is None:
                item["tipo"] = peek_tipo_arquivo(item["path"])

        key_funcs = {
            "nome": lambda a: a["nome"].lower(),
            "tipo": lambda a: a["tipo"] or "",
            "modificado": lambda a: a["modificado"] or datetime.min,
        }
        itens.sort(key=key_funcs[self._sort_col], reverse=self._sort_reverse)

        for i, item in enumerate(itens):
            mod_txt = item["modificado"].strftime("%d/%m %H:%M") if item["modificado"] else "-"
            self.tree.insert(
                "", "end", iid=item["path"],
                values=(item["nome"], item["tipo"], mod_txt),
                tags=zebra_tags(i),
            )

        total = len(self.arquivos)
        if self.extensao_atual and len(itens) != total:
            self.count_var.set(f"{len(itens)} de {total} arquivo(s)")
        else:
            self.count_var.set(f"{len(itens)} arquivo(s)")

        if self._current_path and self.tree.exists(self._current_path):
            self.tree.selection_set(self._current_path)
            self.tree.see(self._current_path)
        elif itens:
            primeiro = itens[0]["path"]
            self.tree.selection_set(primeiro)
            self.tree.see(primeiro)

    def _on_row_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        self._current_path = sel[0]
        self.on_file_selected(sel[0])
