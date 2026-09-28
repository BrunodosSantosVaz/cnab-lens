# -*- coding: utf-8 -*-
"""Leitura dos arquivos CNAB (400 e 240): `CnabFile` lê o arquivo uma vez e aplica o layout escolhido.
Não depende da interface: pode ser usada em scripts e testes sem Tkinter."""
from collections import Counter

from cnablens import layouts
from cnablens.formatacao import format_data
from cnablens.layouts.bancos import NOMES_DOS_BANCOS
from cnablens.leitura.registro import CnabGroup, CnabRecord, safe_slice


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
            self.banco_nome = NOMES_DOS_BANCOS.get(self.banco_codigo, banco_literal)
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
        self.banco_nome = NOMES_DOS_BANCOS.get(self.banco_codigo, banco_literal)
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
            rec.set_fields(campos or layouts.campos_nao_mapeados(240))

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


__all__ = ["CnabFile", "CnabGroup", "CnabRecord"]
