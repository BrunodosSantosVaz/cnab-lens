# -*- coding: utf-8 -*-
"""
Registro central dos layouts CNAB suportados pelo app (CNAB400 e CNAB240).

Cada layout sabe apenas escolher, a partir do tipo de arquivo (Remessa ou
Retorno), qual tabela de campos usar para cada tipo de registro e qual
tabela de códigos de ocorrência aplicar. Isso permite ao usuário trocar a
"visão" de um arquivo já carregado (ex.: FEBRABAN puro <-> Sicredi) sem reler
o arquivo do disco - só reaplica os nomes/posições de campo.

Dois formatos convivem aqui, distinguidos por `CnabLayout.width`:
  - 400 posições: `header_fields`/`detail_fields`/`trailer_fields` devolvem a
    lista de campos do Header, do Detalhe e do Trailer.
  - 240 posições: o arquivo tem vários tipos de registro (header de arquivo,
    header de lote, detalhe dividido em segmentos, trailer de lote, trailer de
    arquivo), então o layout traz em `structure` (um `Cnab240Structure`) uma
    função para cada um deles.

Para adicionar um novo layout no futuro (outro banco/cooperativa com campos
próprios): criar um módulo `cnab400_layout_<nome>.py` (ou `cnab240_layout_<nome>.py`)
no mesmo estilo de `cnab400_layout_sicredi.py` e registrar uma nova entrada em
LAYOUTS abaixo.
"""

from collections import namedtuple

import cnab400_layout as febraban
import cnab400_layout_santander as santander400
import cnab400_layout_sicredi as sicredi
import cnab400_layout_sicoob as sicoob400
import cnab240_layout_santander as santander240
import cnab240_layout_sicoob as sicoob240

CnabLayout = namedtuple(
    "CnabLayout",
    ["key", "label", "header_fields", "detail_fields", "trailer_fields", "ocorrencia_codes",
     "width", "comando_codes", "structure", "record_types"],
    defaults=(400, None, None, None),
)
# `record_types` (só CNAB400, opcional): registros além de Header (0), Detalhe (1) e Trailer (9) que o
# layout descreve, como {caractere da posição 1: função(tipo_arquivo) -> (rótulo, lista de campos) ou None}.
# Esses registros (ex.: dados de QR Code, mensagens) ficam agrupados sob o Detalhe (tipo 1) que os precede.

# Só CNAB240: como achar a lista de campos de cada tipo de registro.
Cnab240Structure = namedtuple(
    "Cnab240Structure",
    ["header_arquivo", "header_lote", "segmento", "trailer_lote", "trailer_arquivo", "chave_segmento"],
    defaults=(None,),
)
# `chave_segmento` (opcional): (tipo_arquivo, letra do segmento, linha) -> chave usada em `segmento`.
# Sem ele a chave é a própria letra. O Santander usa para os segmentos que se subdividem: o Y pelo
# sub-código das posições 18-19 (Y-03, Y-53, Y-04) e o S pelo formato da posição 18 (S-1, S-2).


def unmapped_fields(width):
    """Campos de um registro que o layout escolhido não mapeia (ex.: um
    segmento CNAB240 desconhecido): mostra a linha inteira como um campo só."""
    return [(
        "Conteúdo do Registro (não mapeado neste layout)", 1, width,
        "Registro que este layout não descreve (tipo ou segmento não previsto); "
        "o conteúdo bruto é exibido inteiro.",
    )]


# --- CNAB400 -----------------------------------------------------------------

def _febraban_header(tipo_arquivo):
    return febraban.HEADER_FIELDS


def _febraban_detail(tipo_arquivo):
    return febraban.DETAIL_RETORNO_FIELDS if tipo_arquivo == "Retorno" else febraban.DETAIL_REMESSA_FIELDS


def _febraban_trailer(tipo_arquivo):
    return febraban.TRAILER_FIELDS


def _sicredi_header(tipo_arquivo):
    return sicredi.HEADER_RETORNO_FIELDS if tipo_arquivo == "Retorno" else sicredi.HEADER_REMESSA_FIELDS


def _sicredi_detail(tipo_arquivo):
    return sicredi.DETAIL_RETORNO_FIELDS if tipo_arquivo == "Retorno" else sicredi.DETAIL_REMESSA_FIELDS


def _sicredi_trailer(tipo_arquivo):
    return sicredi.TRAILER_FIELDS


def _sicoob400_header(tipo_arquivo):
    return sicoob400.HEADER_RETORNO_FIELDS if tipo_arquivo == "Retorno" else sicoob400.HEADER_REMESSA_FIELDS


def _sicoob400_detail(tipo_arquivo):
    return sicoob400.DETAIL_RETORNO_FIELDS if tipo_arquivo == "Retorno" else sicoob400.DETAIL_REMESSA_FIELDS


def _sicoob400_trailer(tipo_arquivo):
    # No Sicoob o Trailer é diferente na Remessa e no Retorno.
    return sicoob400.TRAILER_RETORNO_FIELDS if tipo_arquivo == "Retorno" else sicoob400.TRAILER_REMESSA_FIELDS


def _santander400_header(tipo_arquivo):
    return santander400.HEADER_RETORNO_FIELDS if tipo_arquivo == "Retorno" else santander400.HEADER_REMESSA_FIELDS


def _santander400_detail(tipo_arquivo):
    return santander400.DETAIL_RETORNO_FIELDS if tipo_arquivo == "Retorno" else santander400.DETAIL_REMESSA_FIELDS


def _santander400_trailer(tipo_arquivo):
    return santander400.TRAILER_RETORNO_FIELDS if tipo_arquivo == "Retorno" else santander400.TRAILER_REMESSA_FIELDS


def _santander400_registro_2(tipo_arquivo):
    # O registro 2 é a mensagem do Recibo do Pagador na remessa e os dados de QR Code/PIX no retorno.
    if tipo_arquivo == "Retorno":
        return "Registro 2 - Dados de QR Code/PIX", santander400.QRCODE_RETORNO_FIELDS
    return "Registro 2 - Mensagem no Recibo do Pagador", santander400.MENSAGEM_REMESSA_FIELDS


def _santander400_registro_8(tipo_arquivo):
    if tipo_arquivo == "Retorno":
        return None
    return "Registro 8 - Tipo de pagamento e dados de QR Code/PIX", santander400.QRCODE_REMESSA_FIELDS


def _santander400_mensagem_ficha(tipo_arquivo):
    if tipo_arquivo == "Retorno":
        return None
    return "Mensagem na Ficha de Compensação", santander400.MENSAGEM_REMESSA_FIELDS


_SANTANDER400_REGISTROS = {
    "2": _santander400_registro_2,
    "4": lambda tipo: _rotulado(_santander400_mensagem_ficha(tipo), "Registro 4"),
    "5": lambda tipo: _rotulado(_santander400_mensagem_ficha(tipo), "Registro 5"),
    "6": lambda tipo: _rotulado(_santander400_mensagem_ficha(tipo), "Registro 6"),
    "7": lambda tipo: _rotulado(_santander400_mensagem_ficha(tipo), "Registro 7"),
    "8": _santander400_registro_8,
}


def _rotulado(registro, prefixo):
    """Acrescenta o número do registro ao rótulo (ou devolve None se o registro não existe nesse tipo)."""
    return None if registro is None else (f"{prefixo} - {registro[0]}", registro[1])


# --- CNAB240 -----------------------------------------------------------------

def _por_tipo(remessa, retorno):
    """Escolhe a lista de campos pelo tipo do arquivo (Remessa/Retorno)."""
    return lambda tipo_arquivo: retorno if tipo_arquivo == "Retorno" else remessa


_SICOOB240_STRUCTURE = Cnab240Structure(
    header_arquivo=_por_tipo(sicoob240.HEADER_ARQUIVO_REMESSA_FIELDS, sicoob240.HEADER_ARQUIVO_RETORNO_FIELDS),
    header_lote=_por_tipo(sicoob240.HEADER_LOTE_REMESSA_FIELDS, sicoob240.HEADER_LOTE_RETORNO_FIELDS),
    segmento=lambda tipo_arquivo, letra: sicoob240.SEGMENTOS.get((tipo_arquivo, letra)),
    trailer_lote=_por_tipo(sicoob240.TRAILER_LOTE_REMESSA_FIELDS, sicoob240.TRAILER_LOTE_RETORNO_FIELDS),
    trailer_arquivo=_por_tipo(sicoob240.TRAILER_ARQUIVO_FIELDS, sicoob240.TRAILER_ARQUIVO_FIELDS),
)


def _santander240_chave_segmento(tipo_arquivo, letra, linha):
    if letra == "Y":
        return "Y-" + (linha + "  ")[17:19]
    if letra == "S":
        return "S-" + (linha + " ")[17:18]
    return letra


_SANTANDER240_STRUCTURE = Cnab240Structure(
    header_arquivo=_por_tipo(santander240.HEADER_ARQUIVO_REMESSA_FIELDS, santander240.HEADER_ARQUIVO_RETORNO_FIELDS),
    header_lote=_por_tipo(santander240.HEADER_LOTE_REMESSA_FIELDS, santander240.HEADER_LOTE_RETORNO_FIELDS),
    segmento=lambda tipo_arquivo, chave: santander240.SEGMENTOS.get((tipo_arquivo, chave)),
    trailer_lote=_por_tipo(santander240.TRAILER_LOTE_REMESSA_FIELDS, santander240.TRAILER_LOTE_RETORNO_FIELDS),
    trailer_arquivo=_por_tipo(santander240.TRAILER_ARQUIVO_REMESSA_FIELDS, santander240.TRAILER_ARQUIVO_RETORNO_FIELDS),
    chave_segmento=_santander240_chave_segmento,
)


LAYOUTS = {
    "febraban": CnabLayout(
        key="febraban",
        label="CNAB400 FEBRABAN (Padrão)",
        header_fields=_febraban_header,
        detail_fields=_febraban_detail,
        trailer_fields=_febraban_trailer,
        ocorrencia_codes=febraban.OCORRENCIA_CODES,
    ),
    "sicredi": CnabLayout(
        key="sicredi",
        label="CNAB400 Sicredi",
        header_fields=_sicredi_header,
        detail_fields=_sicredi_detail,
        trailer_fields=_sicredi_trailer,
        ocorrencia_codes=sicredi.OCORRENCIA_CODES,
    ),
    "sicoob400": CnabLayout(
        key="sicoob400",
        label="CNAB400 Sicoob",
        header_fields=_sicoob400_header,
        detail_fields=_sicoob400_detail,
        trailer_fields=_sicoob400_trailer,
        ocorrencia_codes=sicoob400.OCORRENCIA_CODES,
        comando_codes=sicoob400.COMANDO_REMESSA_CODES,
    ),
    "santander400": CnabLayout(
        key="santander400",
        label="CNAB400 Santander",
        header_fields=_santander400_header,
        detail_fields=_santander400_detail,
        trailer_fields=_santander400_trailer,
        ocorrencia_codes=santander400.OCORRENCIA_CODES,
        comando_codes=santander400.COMANDO_REMESSA_CODES,
        record_types=_SANTANDER400_REGISTROS,
    ),
    "santander240": CnabLayout(
        key="santander240",
        label="CNAB240 Santander",
        header_fields=None,
        detail_fields=None,
        trailer_fields=None,
        ocorrencia_codes=santander240.MOVIMENTO_RETORNO_CODES,
        width=240,
        comando_codes=santander240.MOVIMENTO_REMESSA_CODES,
        structure=_SANTANDER240_STRUCTURE,
    ),
    "sicoob240": CnabLayout(
        key="sicoob240",
        label="CNAB240 Sicoob",
        header_fields=None,
        detail_fields=None,
        trailer_fields=None,
        ocorrencia_codes=sicoob240.OCORRENCIA_RETORNO_CODES,
        width=240,
        comando_codes=sicoob240.MOVIMENTO_REMESSA_CODES,
        structure=_SICOOB240_STRUCTURE,
    ),
}

# Ordem de exibição no seletor da interface.
LAYOUT_ORDER = ["febraban", "sicredi", "sicoob400", "santander400", "sicoob240", "santander240"]

DEFAULT_LAYOUT_KEY = "febraban"

# Layout usado quando o banco do arquivo não tem um layout próprio, por
# tamanho de linha. (Só há um layout CNAB240; para um arquivo CNAB240 de
# outro banco ele é aplicado mesmo assim, já que a estrutura de lote/segmento
# é a padrão FEBRABAN - mas campos específicos do banco podem divergir.)
DEFAULT_LAYOUT_BY_WIDTH = {400: "febraban", 240: "sicoob240"}

# Bancos que, ao serem detectados no Header, fazem o app pré-selecionar
# automaticamente um layout diferente do padrão (o usuário pode trocar
# manualmente a qualquer momento). Chave: (código do banco, largura da linha).
AUTO_LAYOUT_BY_BANK = {
    ("033", 400): "santander400",
    ("353", 400): "santander400",  # código legado do Santander, aceito no Header do CNAB 400
    ("748", 400): "sicredi",
    ("756", 400): "sicoob400",
    ("756", 240): "sicoob240",
    ("033", 240): "santander240",
}


def default_key_for_width(width):
    return DEFAULT_LAYOUT_BY_WIDTH.get(width, DEFAULT_LAYOUT_KEY)


def auto_layout_key(bank_code, width):
    return AUTO_LAYOUT_BY_BANK.get((bank_code, width)) or default_key_for_width(width)


def layout_labels():
    """Lista de rótulos (para o Combobox), na ordem definida em LAYOUT_ORDER."""
    return [LAYOUTS[key].label for key in LAYOUT_ORDER]


def key_for_label(label):
    for key in LAYOUT_ORDER:
        if LAYOUTS[key].label == label:
            return key
    return DEFAULT_LAYOUT_KEY
