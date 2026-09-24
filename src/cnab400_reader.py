"""
CNABLens: lente para arquivos CNAB (padrão bancário brasileiro - remessa/retorno de cobrança).

Abra um arquivo CNAB400 (400 colunas por linha) ou CNAB240 (240 colunas) e veja
os lançamentos com cada campo identificado pelo nome correto, segundo o layout
escolhido no seletor "Layout de campos" (FEBRABAN, Sicredi e Sicoob 400; Sicoob 240).
Os valores do painel de campos podem ser selecionados com o mouse e copiados (Ctrl+C).
"""

import os
import sys
import traceback
from collections import Counter
from datetime import datetime
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox

import cnab400_layout as layout
import cnab400_layouts as layouts
from version import __version__

TITULO_APP = f"CNABLens v{__version__}"


def safe_slice(line, start, end):
    """Extrai posicoes 1-indexadas [start, end] (inclusive) de uma linha, com padding."""
    padded = line.ljust(400)
    return padded[start - 1:end].strip()


def parse_fields(line, field_defs):
    result = []
    for name, start, end, descricao in field_defs:
        value = safe_slice(line, start, end)
        result.append({"nome": name, "inicio": start, "fim": end, "valor": value, "descricao": descricao})
    return result


def format_valor_monetario(raw):
    """Campos de valor no CNAB400 vem sem separador decimal, 2 casas implicitas."""
    digits = "".join(c for c in raw if c.isdigit())
    if not digits:
        return raw
    digits = digits.zfill(3)
    inteiro, centavos = digits[:-2], digits[-2:]
    inteiro = str(int(inteiro))
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return f'{".".join(grupos)},{centavos}'


def _valid_ymd(ano, mes, dia):
    if not (1 <= mes <= 12):
        return False
    if not (1 <= dia <= 31):
        return False
    if not (1900 <= ano <= 2100):
        return False
    return True


def format_data(raw):
    """Formata datas do CNAB400. Layout padrão é DDMMAA (6 dígitos), mas alguns
    bancos (ex.: Sicredi) gravam AAAAMMDD (8 dígitos) no mesmo campo. Tenta as
    variações conhecidas e só retorna algo formatado se a data for plausível;
    caso contrário devolve o valor bruto, sem inventar uma data inválida."""
    raw = raw.strip()
    digits = raw

    if len(digits) == 6 and digits.isdigit() and digits != "000000":
        dd, mm, aa = int(digits[0:2]), int(digits[2:4]), int(digits[4:6])
        ano = aa + (2000 if aa <= 69 else 1900)
        if _valid_ymd(ano, mm, dd):
            return f"{dd:02d}/{mm:02d}/{ano}"

    if len(digits) == 8 and digits.isdigit() and digits != "00000000":
        aa, mm, dd = int(digits[0:4]), int(digits[4:6]), int(digits[6:8])
        if _valid_ymd(aa, mm, dd):
            return f"{dd:02d}/{mm:02d}/{aa}"
        dd2, mm2, aa2 = int(digits[0:2]), int(digits[2:4]), int(digits[4:8])
        if _valid_ymd(aa2, mm2, dd2):
            return f"{dd2:02d}/{mm2:02d}/{aa2}"

    return raw


# CNAB240: o tipo de registro fica na posição 8 (e não na 1, como no CNAB400) e
# os detalhes (tipo 3) se dividem em segmentos identificados por uma letra na
# posição 14 (P, Q, R... na remessa de cobrança; T, U... no retorno).
CNAB240_TIPOS = {
    "0": ("header_arquivo", "Header de Arquivo (Registro 0)"),
    "1": ("header_lote", "Header de Lote (Registro 1)"),
    "3": ("detalhe", "Detalhe (Registro 3)"),
    "5": ("trailer_lote", "Trailer de Lote (Registro 5)"),
    "9": ("trailer_arquivo", "Trailer de Arquivo (Registro 9)"),
}


class CnabRecord:
    def __init__(self, index, raw_line, width=400):
        self.index = index
        self.raw = raw_line
        self.width = width
        self.segmento = ""
        if width == 240:
            self.tipo_char = raw_line[7:8] if raw_line else ""
            if self.tipo_char in CNAB240_TIPOS:
                self.tipo, self.tipo_label = CNAB240_TIPOS[self.tipo_char]
            else:
                self.tipo = "desconhecido"
                self.tipo_label = f"Desconhecido (código '{self.tipo_char}')"
            if self.tipo == "detalhe":
                self.segmento = raw_line[13:14].strip().upper()
                self.tipo_label = f"Detalhe (Registro 3) - Segmento {self.segmento or '?'}"
        else:
            self.tipo_char = raw_line[0:1] if raw_line else ""
            if self.tipo_char == "0":
                self.tipo = "header"
                self.tipo_label = "Header (Registro 0)"
            elif self.tipo_char == "9":
                self.tipo = "trailer"
                self.tipo_label = "Trailer (Registro 9)"
            elif self.tipo_char == "1":
                self.tipo = "detalhe"
                self.tipo_label = "Detalhe (Registro 1)"
            else:
                self.tipo = "desconhecido"
                self.tipo_label = f"Desconhecido (código '{self.tipo_char}')"
        self.rotulo_padrao = self.tipo_label
        self.fields = []
        self.field_map = {}

    def set_fields(self, field_defs):
        self.fields = parse_fields(self.raw, field_defs)
        self.field_map = {f["nome"]: f["valor"] for f in self.fields}

    def get(self, name_substring, default=""):
        for nome, valor in self.field_map.items():
            if name_substring.lower() in nome.lower():
                return valor
        return default

    def get_concat(self, name_substring, default=""):
        """Concatena, na ordem do layout, o valor de TODOS os campos cujo
        nome contenha name_substring. Útil para campos que um layout quebra
        em várias sub-posições (ex.: "Nosso Número [Ano]" + "[...Byte]" +
        "[...Sequencial]" + "[...DV]"), reconstituindo o valor completo."""
        partes = [valor for nome, valor in self.field_map.items() if name_substring.lower() in nome.lower()]
        return "".join(partes) if partes else default


class CnabGroup:
    """Vários registros CNAB240 exibidos como uma unidade só: um título
    (segmentos P+Q+R... na remessa, T+U... no retorno) ou os registros de
    cabeçalho/rodapé (arquivo + lote). Tem a mesma interface de CnabRecord que
    a tela usa (index, fields, get, get_concat), então o resto do app trata
    os dois igual. Em `fields`, cada registro do grupo vem precedido de uma
    linha separadora com o nome do registro/segmento."""

    def __init__(self, records):
        self.records = records
        self.index = records[0].index
        self.raw = "\n".join(r.raw for r in records)

    @property
    def fields(self):
        campos = []
        for rec in self.records:
            campos.append({
                "nome": f"{rec.tipo_label}   ·   linha {rec.index}",
                "inicio": "", "fim": "", "valor": "", "descricao": "", "separador": True,
            })
            campos.extend(rec.fields)
        return campos

    def get(self, name_substring, default=""):
        """Primeiro valor não vazio, entre os registros do grupo, de um campo
        cujo nome contenha name_substring (o mesmo nome pode existir em mais de
        um segmento)."""
        achou_vazio = False
        for rec in self.records:
            for nome, valor in rec.field_map.items():
                if name_substring.lower() in nome.lower():
                    if valor:
                        return valor
                    achou_vazio = True
        return "" if achou_vazio else default

    def get_concat(self, name_substring, default=""):
        for rec in self.records:
            valor = rec.get_concat(name_substring, None)
            if valor is not None:
                return valor
        return default


class CnabFile:
    """Lê as linhas cruas do arquivo uma única vez. A rotulagem dos campos
    (nomes/posições) é feita à parte, em apply_layout(), para que o mesmo
    arquivo possa ser reexibido sob diferentes layouts (FEBRABAN, Sicredi,
    ...) sem reler o disco - só quando o usuário troca o seletor de layout."""

    def __init__(self, path):
        self.path = path
        self.records = []
        self.width = 400  # 400 ou 240 posições por linha (detectado no arquivo)
        self.tipo_arquivo = "?"  # Remessa / Retorno
        self.banco_codigo = ""
        self.banco_nome = ""
        self.empresa_nome = ""
        self.data_geracao = ""
        self.header = None
        self.trailer = None
        self.detalhes = []
        self.layout_key = None
        self.layout = None
        self._load()
        self.apply_layout(layouts.auto_layout_key(self.banco_codigo, self.width))

    def _read_lines(self):
        for enc in ("latin-1", "cp1252", "utf-8"):
            try:
                with open(self.path, "r", encoding=enc, newline="") as fh:
                    content = fh.read()
                return content.splitlines(), enc
            except (UnicodeDecodeError, LookupError):
                continue
        with open(self.path, "rb") as fh:
            content = fh.read()
        return content.decode("latin-1", errors="replace").splitlines(), "latin-1 (fallback)"

    @staticmethod
    def _parse_data_geracao(header_line):
        """A data de geração/gravação do Header fica sempre a partir da
        posição 95, mas o tamanho varia por layout: DDMMAA (6 posições) no
        padrão FEBRABAN genérico, AAAAMMDD (8 posições) no Sicredi e em
        alguns outros bancos. Tenta as duas variações nessa mesma posição
        inicial e só formata se a data for válida."""
        six = format_data(safe_slice(header_line, 95, 100))
        if "/" in six:
            return six
        eight = format_data(safe_slice(header_line, 95, 102))
        if "/" in eight:
            return eight
        return six or eight

    def _load(self):
        raw_lines, self.encoding_used = self._read_lines()
        raw_lines = [ln for ln in raw_lines if ln.strip("\x1a\x00 ") != ""]
        if not raw_lines:
            raise ValueError("Arquivo vazio ou sem linhas reconhecíveis.")

        self.width = self._detect_width(raw_lines)
        for i, line in enumerate(raw_lines, start=1):
            rec = CnabRecord(i, line, self.width)
            self.records.append(rec)

        if self.width == 240:
            self._load_file_info_240()
            return

        header_rec = next((r for r in self.records if r.tipo == "header"), None)
        self.header = header_rec
        self.trailer = next((r for r in self.records if r.tipo == "trailer"), None)
        self.detalhes = [r for r in self.records if r.tipo == "detalhe"]

        if header_rec is not None:
            tipo_arq_code = safe_slice(header_rec.raw, 2, 2)
            if tipo_arq_code == "1":
                self.tipo_arquivo = "Remessa"
            elif tipo_arq_code == "2":
                self.tipo_arquivo = "Retorno"
            else:
                self.tipo_arquivo = "Remessa" if "REMESSA" in header_rec.raw.upper() else \
                    ("Retorno" if "RETORNO" in header_rec.raw.upper() else "Desconhecido")
            self.banco_codigo = safe_slice(header_rec.raw, 77, 79)
            banco_literal = safe_slice(header_rec.raw, 80, 94)
            self.banco_nome = layout.BANK_NAMES.get(self.banco_codigo, banco_literal)
            self.empresa_nome = safe_slice(header_rec.raw, 47, 76)
            self.data_geracao = self._parse_data_geracao(header_rec.raw)
        else:
            self.tipo_arquivo = "Desconhecido (sem header)"

    @staticmethod
    def _detect_width(lines):
        """400 ou 240 posições: pelo tamanho de linha mais comum (linhas de
        arquivos CNAB240 têm ~240 caracteres; CNAB400, ~400). Tolera arquivos
        com espaços finais cortados: qualquer coisa até 300 é tratada como 240."""
        mais_comum = Counter(len(ln) for ln in lines).most_common(1)[0][0]
        return 240 if mais_comum <= 300 else 400

    def _load_file_info_240(self):
        """Banco, empresa, tipo e data de geração, lidos do Header de Arquivo
        (registro tipo 0) nas posições padrão FEBRABAN CNAB240."""
        header_rec = next((r for r in self.records if r.tipo == "header_arquivo"), None)
        if header_rec is None:
            self.tipo_arquivo = "Desconhecido (sem header)"
            return
        codigo = safe_slice(header_rec.raw, 143, 143)  # 1 = Remessa, 2 = Retorno
        if codigo == "1":
            self.tipo_arquivo = "Remessa"
        elif codigo == "2":
            self.tipo_arquivo = "Retorno"
        else:
            segmentos = {r.segmento for r in self.records if r.tipo == "detalhe"}
            if segmentos & {"T", "U"}:
                self.tipo_arquivo = "Retorno"
            elif segmentos & {"P", "Q", "R"}:
                self.tipo_arquivo = "Remessa"
            else:
                self.tipo_arquivo = "Desconhecido"
        self.banco_codigo = safe_slice(header_rec.raw, 1, 3)
        banco_literal = safe_slice(header_rec.raw, 103, 132)
        self.banco_nome = layout.BANK_NAMES.get(self.banco_codigo, banco_literal)
        self.empresa_nome = safe_slice(header_rec.raw, 73, 102)
        self.data_geracao = format_data(safe_slice(header_rec.raw, 144, 151))

    def _agrupar_detalhes_240(self):
        """Um "lançamento" no CNAB240 é um título, que ocupa vários registros
        (segmentos). O primeiro segmento de cada lote (P na remessa, T no
        retorno) abre um título novo; os demais (Q, R, S, U...) entram nele."""
        grupos, atual, primeiro_segmento = [], None, None
        for rec in self.records:
            if rec.tipo == "header_lote":
                primeiro_segmento = None
                atual = None
            elif rec.tipo == "detalhe":
                if primeiro_segmento is None:
                    primeiro_segmento = rec.segmento
                if atual is None or rec.segmento == primeiro_segmento:
                    atual = []
                    grupos.append(atual)
                atual.append(rec)
        return [CnabGroup(g) for g in grupos]

    def _apply_layout_240(self, active):
        estrutura = active.structure
        tipo = self.tipo_arquivo
        for rec in self.records:
            if rec.tipo == "header_arquivo":
                campos = estrutura.header_arquivo(tipo)
            elif rec.tipo == "header_lote":
                campos = estrutura.header_lote(tipo)
            elif rec.tipo == "detalhe":
                # o segmento pode se subdividir (Santander: Y-03, Y-53, Y-04 e S-1, S-2); sem a função
                # `chave_segmento` do layout, a chave é a letra da posição 14
                chave = rec.segmento
                if estrutura.chave_segmento:
                    chave = estrutura.chave_segmento(tipo, rec.segmento, rec.raw)
                rec.tipo_label = f"Detalhe (Registro 3) - Segmento {chave or '?'}"
                campos = estrutura.segmento(tipo, chave)
            elif rec.tipo == "trailer_lote":
                campos = estrutura.trailer_lote(tipo)
            elif rec.tipo == "trailer_arquivo":
                campos = estrutura.trailer_arquivo(tipo)
            else:
                campos = None
            rec.set_fields(campos or layouts.unmapped_fields(240))

        cabecalho = [r for r in self.records if r.tipo in ("header_arquivo", "header_lote")]
        rodape = [r for r in self.records if r.tipo in ("trailer_lote", "trailer_arquivo")]
        self.header = CnabGroup(cabecalho) if cabecalho else None
        self.trailer = CnabGroup(rodape) if rodape else None
        self.detalhes = self._agrupar_detalhes_240()

    def apply_layout(self, layout_key):
        """Reaplica nomes/posições de campo a todos os registros já lidos,
        segundo o layout escolhido (não relê o arquivo)."""
        active = layouts.LAYOUTS.get(layout_key)
        if active is None or active.width != self.width:
            active = layouts.LAYOUTS[layouts.default_key_for_width(self.width)]
        self.layout_key = active.key
        self.layout = active

        if self.width == 240:
            self._apply_layout_240(active)
            return

        detail_fields = active.detail_fields(self.tipo_arquivo)
        if self.header is not None:
            self.header.set_fields(active.header_fields(self.tipo_arquivo))
        if self.trailer is not None:
            self.trailer.set_fields(active.trailer_fields(self.tipo_arquivo))
        registros = active.record_types or {}
        for rec in self.records:
            rec.tipo_label = rec.rotulo_padrao  # desfaz o rótulo de um layout anterior
            if rec.tipo == "detalhe":
                rec.set_fields(detail_fields)
            elif rec.tipo == "desconhecido":
                # registro além de 0/1/9: se o layout o descreve (ex.: dados de QR Code), usa os campos dele
                info = registros.get(rec.tipo_char, lambda _tipo: None)(self.tipo_arquivo)
                if info:
                    rec.tipo_label, campos = info
                    rec.set_fields(campos)
                else:
                    rec.set_fields(detail_fields)
        if registros:
            self.detalhes = self._agrupar_detalhes_400(registros)
        else:
            self.detalhes = [r for r in self.records if r.tipo == "detalhe"]

    def _agrupar_detalhes_400(self, registros):
        """Nos layouts com registros opcionais (ex.: Santander), cada Detalhe (tipo 1) abre um
        lançamento e os registros seguintes que o layout descreve (QR Code, mensagens) entram nele,
        como os segmentos do CNAB240. Registros que o layout não descreve ficam de fora, como antes."""
        grupos, atual = [], None
        for rec in self.records:
            if rec.tipo == "detalhe":
                atual = [rec]
                grupos.append(atual)
            elif rec.tipo == "desconhecido" and atual is not None and rec.tipo_char in registros:
                if registros[rec.tipo_char](self.tipo_arquivo):  # descrito para este tipo de arquivo
                    atual.append(rec)
            else:
                atual = None
        return [CnabGroup(g) for g in grupos]


# Zebra striping: linhas alternadas branca/cinza-claro para facilitar a
# leitura de tabelas longas.
ROW_COLOR_EVEN = "#ffffff"
ROW_COLOR_ODD = "#f1f3f6"
ROW_COLOR_FILLER = "#c7cbd1"  # texto acinzentado para campos "Uso Reservado/Filler"


def configure_zebra_tags(tree):
    tree.tag_configure("even", background=ROW_COLOR_EVEN)
    tree.tag_configure("odd", background=ROW_COLOR_ODD)
    tree.tag_configure("even-filler", background=ROW_COLOR_EVEN, foreground=ROW_COLOR_FILLER)
    tree.tag_configure("odd-filler", background=ROW_COLOR_ODD, foreground=ROW_COLOR_FILLER)


def zebra_tags(index, is_filler=False):
    base = "even" if index % 2 == 0 else "odd"
    return (f"{base}-filler",) if is_filler else (base,)


# Campos cujo nome tem uma dessas palavras são valores monetários (2 casas
# decimais implícitas) ... exceto se o nome também indicar que é outra coisa
# (uma data de desconto, o código do tipo de juros etc.).
MOEDA_KEYWORDS = ("valor", "juros", "mora", "desconto", "abatimento", "iof", "tarifa", "despesa")
NAO_MOEDA_KEYWORDS = (
    "data", "código", "codigo", "tipo", "indicador", "prazo", "percentual", "taxa",
    "número", "numero", "identificação", "identificacao", "quantidade",
)
DATA_KEYWORDS = ("data",)


def formatar_valor_campo(nome, valor, moeda_fields=MOEDA_KEYWORDS, data_fields=DATA_KEYWORDS):
    """Valor como aparece na coluna "Valor" do painel de campos: o bruto do
    arquivo e, quando o nome do campo indica moeda ou data, também o valor
    convertido ("0000015000  →  R$ 150,00")."""
    nome_lower = nome.lower()
    bruto = valor.strip()
    if not bruto:
        return valor
    eh_moeda = (
        any(k in nome_lower for k in moeda_fields)
        and not any(k in nome_lower for k in NAO_MOEDA_KEYWORDS)
    )
    if eh_moeda and bruto.isdigit():
        return f"{valor}  →  R$ {format_valor_monetario(valor)}"
    if any(k in nome_lower for k in data_fields):
        data = format_data(valor)
        if data and data != bruto:
            return f"{valor}  →  {data}"
    return valor


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


SEM_EXTENSAO = "(sem extensão)"


def escanear_pasta(folder_path):
    """Lista os arquivos (não-recursivo) de uma pasta, com metadados básicos
    (extensão, tamanho, data de modificação). O 'tipo' (Remessa/Retorno) só é
    calculado sob demanda (é preciso abrir o arquivo), então começa como None."""
    arquivos = []
    with os.scandir(folder_path) as it:
        entradas = sorted(it, key=lambda e: e.name.lower())
        for entry in entradas:
            if not entry.is_file():
                continue
            ext = os.path.splitext(entry.name)[1].lower() or SEM_EXTENSAO
            try:
                stat = entry.stat()
                tamanho = stat.st_size
                modificado = datetime.fromtimestamp(stat.st_mtime)
            except OSError:
                tamanho = 0
                modificado = None
            arquivos.append({
                "path": entry.path, "nome": entry.name, "ext": ext,
                "tamanho": tamanho, "modificado": modificado, "tipo": None,
            })
    return arquivos


def peek_tipo_arquivo(path):
    """Espia só a primeira linha do arquivo (rápido, não lê o arquivo
    inteiro) para descobrir se é Remessa ou Retorno, para mostrar na lista."""
    try:
        with open(path, "r", encoding="latin-1", errors="replace") as fh:
            primeira_linha = fh.readline()
    except OSError:
        return "?"
    primeira_linha = primeira_linha.rstrip("\r\n")
    if len(primeira_linha) <= 300 and primeira_linha[7:8] == "0":
        # CNAB240: Header de Arquivo (tipo de registro 0 na posição 8);
        # posição 143 = 1 (Remessa) ou 2 (Retorno).
        return {"1": "REM", "2": "RET"}.get(safe_slice(primeira_linha, 143, 143), "?")
    if primeira_linha[0:1] != "0":
        return "?"
    codigo = safe_slice(primeira_linha, 2, 2)
    if codigo == "1":
        return "REM"
    if codigo == "2":
        return "RET"
    upper = primeira_linha.upper()
    if "REMESSA" in upper:
        return "REM"
    if "RETORNO" in upper:
        return "RET"
    return "?"


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

        pad = {"padx": 18, "pady": 4}
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
        self.config(menu=menubar)
        self.bind_all("<Control-o>", lambda e: self.abrir_pasta())

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

        self.btn_refresh = ttk.Button(top, text="⟳ Atualizar", width=11, command=self._atualizar_pasta, state="disabled")
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
        self.btn_trailer = ttk.Button(btns, text="Ver Trailer do arquivo", command=self.mostrar_trailer, state="disabled")
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
            try:
                self.after_cancel(self._paned_after)
            except tk.TclError:
                pass
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
