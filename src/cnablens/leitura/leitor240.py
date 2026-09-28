# -*- coding: utf-8 -*-
"""Regras do CNAB 240: o tipo do registro na posição 8 e os detalhes (tipo 3) divididos em segmentos,
identificados pela letra da posição 14 (P, Q, R... na remessa; T, U... no retorno). Um título ocupa vários
segmentos e é mostrado como um lançamento."""
from cnablens import layouts
from cnablens.formatacao import format_data
from cnablens.layouts.bancos import NOMES_DOS_BANCOS
from cnablens.leitura.registro import CnabGroup, CnabRecord, safe_slice

REMESSA, RETORNO = "Remessa", "Retorno"


class Leitor240:
    largura = 240
    TIPOS = {
        "0": ("header_arquivo", "Header de Arquivo (Registro 0)"),
        "1": ("header_lote", "Header de Lote (Registro 1)"),
        "3": ("detalhe", "Detalhe (Registro 3)"),
        "5": ("trailer_lote", "Trailer de Lote (Registro 5)"),
        "9": ("trailer_arquivo", "Trailer de Arquivo (Registro 9)"),
    }

    def registro(self, indice, linha):
        """Classifica a linha pela posição 8 e, no Detalhe, guarda a letra do segmento (posição 14)."""
        tipo_char = linha[7:8] if linha else ""
        tipo, rotulo = self.TIPOS.get(tipo_char, ("desconhecido", f"Desconhecido (código '{tipo_char}')"))
        segmento = ""
        if tipo == "detalhe":
            segmento = linha[13:14].strip().upper()
            rotulo = f"Detalhe (Registro 3) - Segmento {segmento or '?'}"
        return CnabRecord(indice, linha, tipo_char, tipo, rotulo, segmento)

    def identificar(self, arquivo):
        """Pelo Header de Arquivo (posições padrão FEBRABAN): tipo do arquivo, banco, empresa e data.
        Header, Trailer e lançamentos dependem do layout e são montados em aplicar_layout()."""
        header = next((r for r in arquivo.records if r.tipo == "header_arquivo"), None)
        if header is None:
            arquivo.tipo_arquivo = "Desconhecido (sem header)"
            return
        linha = header.raw
        arquivo.tipo_arquivo = self._tipo_do_arquivo(linha, arquivo.records)
        arquivo.banco_codigo = safe_slice(linha, 1, 3)
        arquivo.banco_nome = NOMES_DOS_BANCOS.get(arquivo.banco_codigo, safe_slice(linha, 103, 132))
        arquivo.empresa_nome = safe_slice(linha, 73, 102)
        arquivo.data_geracao = format_data(safe_slice(linha, 144, 151))

    def aplicar_layout(self, arquivo, layout):
        """Campos de cada registro pela estrutura do layout; Header e Trailer juntam os de arquivo e de lote;
        cada título vira um lançamento."""
        for registro in arquivo.records:
            campos = self._campos(registro, layout.structure, arquivo.tipo_arquivo)
            registro.set_fields(campos or layouts.campos_nao_mapeados(self.largura))
        cabecalho = [r for r in arquivo.records if r.tipo in ("header_arquivo", "header_lote")]
        rodape = [r for r in arquivo.records if r.tipo in ("trailer_lote", "trailer_arquivo")]
        arquivo.header = CnabGroup(cabecalho) if cabecalho else None
        arquivo.trailer = CnabGroup(rodape) if rodape else None
        arquivo.detalhes = self._agrupar_titulos(arquivo.records)

    @staticmethod
    def _campos(registro, estrutura, tipo):
        """Lista de campos do registro na estrutura do layout (None se o layout não o descreve)."""
        if registro.tipo == "detalhe":
            # o segmento pode se subdividir (Santander: Y-03, Y-53, Y-04 e S-1, S-2); sem `chave_segmento`
            # no layout, a chave é a letra da posição 14
            chave = registro.segmento
            if estrutura.chave_segmento:
                chave = estrutura.chave_segmento(tipo, registro.segmento, registro.raw)
            registro.tipo_label = f"Detalhe (Registro 3) - Segmento {chave or '?'}"
            return estrutura.segmento(tipo, chave)
        por_tipo_de_registro = {
            "header_arquivo": estrutura.header_arquivo,
            "header_lote": estrutura.header_lote,
            "trailer_lote": estrutura.trailer_lote,
            "trailer_arquivo": estrutura.trailer_arquivo,
        }
        campos = por_tipo_de_registro.get(registro.tipo)
        return campos(tipo) if campos else None

    @staticmethod
    def _agrupar_titulos(registros):
        """O primeiro segmento de cada lote (P na remessa, T no retorno) abre um título; os demais (Q, R, S,
        U...) entram nele."""
        grupos, atual, primeiro_segmento = [], None, None
        for registro in registros:
            if registro.tipo == "header_lote":
                primeiro_segmento, atual = None, None
            elif registro.tipo == "detalhe":
                if primeiro_segmento is None:
                    primeiro_segmento = registro.segmento
                if atual is None or registro.segmento == primeiro_segmento:
                    atual = []
                    grupos.append(atual)
                atual.append(registro)
        return [CnabGroup(g) for g in grupos]

    @staticmethod
    def _tipo_do_arquivo(linha_do_header, registros):
        """Posição 143 do Header de Arquivo: 1 = Remessa, 2 = Retorno; sem ela, deduz pelos segmentos."""
        codigo = safe_slice(linha_do_header, 143, 143)
        if codigo == "1":
            return REMESSA
        if codigo == "2":
            return RETORNO
        segmentos = {r.segmento for r in registros if r.tipo == "detalhe"}
        if segmentos & {"T", "U"}:
            return RETORNO
        if segmentos & {"P", "Q", "R"}:
            return REMESSA
        return "Desconhecido"
