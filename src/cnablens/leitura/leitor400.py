# -*- coding: utf-8 -*-
"""Regras do CNAB 400: o tipo do registro na posição 1 (0 Header, 1 Detalhe, 9 Trailer) e, em alguns
layouts, registros opcionais que ficam agrupados sob o Detalhe que os precede."""
from cnablens.formatacao import format_data
from cnablens.layouts.bancos import NOMES_DOS_BANCOS
from cnablens.leitura.registro import CnabGroup, CnabRecord, safe_slice

REMESSA, RETORNO = "Remessa", "Retorno"


class Leitor400:
    largura = 400
    TIPOS = {
        "0": ("header", "Header (Registro 0)"),
        "1": ("detalhe", "Detalhe (Registro 1)"),
        "9": ("trailer", "Trailer (Registro 9)"),
    }

    def registro(self, indice, linha):
        """Classifica a linha pelo caractere da posição 1."""
        tipo_char = linha[0:1] if linha else ""
        tipo, rotulo = self.TIPOS.get(tipo_char, ("desconhecido", f"Desconhecido (código '{tipo_char}')"))
        return CnabRecord(indice, linha, tipo_char, tipo, rotulo)

    def identificar(self, arquivo):
        """Header, Trailer, Detalhes e, pelo Header: tipo do arquivo, banco, empresa e data de geração."""
        arquivo.header = next((r for r in arquivo.records if r.tipo == "header"), None)
        arquivo.trailer = next((r for r in arquivo.records if r.tipo == "trailer"), None)
        arquivo.detalhes = [r for r in arquivo.records if r.tipo == "detalhe"]
        if arquivo.header is None:
            arquivo.tipo_arquivo = "Desconhecido (sem header)"
            return
        linha = arquivo.header.raw
        arquivo.tipo_arquivo = self._tipo_do_arquivo(linha)
        arquivo.banco_codigo = safe_slice(linha, 77, 79)
        arquivo.banco_nome = NOMES_DOS_BANCOS.get(arquivo.banco_codigo, safe_slice(linha, 80, 94))
        arquivo.empresa_nome = safe_slice(linha, 47, 76)
        arquivo.data_geracao = self._data_de_geracao(linha)

    def aplicar_layout(self, arquivo, layout):
        """Nomes e posições de campo do layout em todos os registros; agrupa os lançamentos."""
        tipo = arquivo.tipo_arquivo
        campos_do_detalhe = layout.detail_fields(tipo)
        if arquivo.header is not None:
            arquivo.header.set_fields(layout.header_fields(tipo))
        if arquivo.trailer is not None:
            arquivo.trailer.set_fields(layout.trailer_fields(tipo))
        opcionais = layout.record_types or {}
        for registro in arquivo.records:
            registro.tipo_label = registro.rotulo_padrao  # desfaz o rótulo de um layout anterior
            if registro.tipo == "detalhe":
                registro.set_fields(campos_do_detalhe)
            elif registro.tipo == "desconhecido":
                self._aplicar_opcional(registro, opcionais, tipo, campos_do_detalhe)
        if opcionais:
            arquivo.detalhes = self._agrupar_lancamentos(arquivo.records, opcionais, tipo)
        else:
            arquivo.detalhes = [r for r in arquivo.records if r.tipo == "detalhe"]

    @staticmethod
    def _aplicar_opcional(registro, opcionais, tipo, campos_do_detalhe):
        """Registro além de 0/1/9: se o layout o descreve (ex.: dados de QR Code), usa os campos dele;
        senão, mostra com os campos do Detalhe, como antes."""
        descricao = opcionais[registro.tipo_char](tipo) if registro.tipo_char in opcionais else None
        if descricao:
            registro.tipo_label, campos = descricao
            registro.set_fields(campos)
        else:
            registro.set_fields(campos_do_detalhe)

    @staticmethod
    def _agrupar_lancamentos(registros, opcionais, tipo):
        """Cada Detalhe abre um lançamento; os registros opcionais seguintes que o layout descreve para este
        tipo de arquivo (QR Code, mensagens) entram nele, como os segmentos do CNAB 240."""
        grupos, atual = [], None
        for registro in registros:
            if registro.tipo == "detalhe":
                atual = [registro]
                grupos.append(atual)
            elif registro.tipo == "desconhecido" and atual is not None and registro.tipo_char in opcionais:
                if opcionais[registro.tipo_char](tipo):
                    atual.append(registro)
            else:
                atual = None
        return [CnabGroup(g) for g in grupos]

    @staticmethod
    def _tipo_do_arquivo(linha_do_header):
        """Posição 2 do Header: 1 = Remessa, 2 = Retorno; sem ela, procura as palavras na linha."""
        codigo = safe_slice(linha_do_header, 2, 2)
        if codigo == "1":
            return REMESSA
        if codigo == "2":
            return RETORNO
        texto = linha_do_header.upper()
        if "REMESSA" in texto:
            return REMESSA
        return RETORNO if "RETORNO" in texto else "Desconhecido"

    @staticmethod
    def _data_de_geracao(linha_do_header):
        """A data de geração fica a partir da posição 95, mas o tamanho varia: DDMMAA (6 posições) no
        FEBRABAN genérico, AAAAMMDD (8) no Sicredi e em outros bancos. Tenta as duas e só formata se a
        data for válida."""
        seis = format_data(safe_slice(linha_do_header, 95, 100))
        if "/" in seis:
            return seis
        oito = format_data(safe_slice(linha_do_header, 95, 102))
        if "/" in oito:
            return oito
        return seis or oito
