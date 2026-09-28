"""Registro dos layouts CNAB suportados (CNAB 400 e CNAB 240).

Cada layout (Layout400 ou Layout240, em base.py) só sabe escolher, pelo tipo do arquivo (Remessa ou
Retorno), a lista de campos de cada tipo de registro e as tabelas de códigos. Isso permite trocar a "visão"
de um arquivo já carregado (ex.: FEBRABAN <-> Sicredi) sem reler o disco.

Para acrescentar um banco:
  1. crie o módulo de dados (ex.: `layouts/itau400.py`) no estilo de `sicredi400.py`: listas de campos
     `(nome, início, fim, descrição)` que cobrem a linha inteira, e as tabelas de códigos;
  2. registre-o em LAYOUTS e LAYOUT_ORDER abaixo e, para a escolha automática pelo banco, em
     AUTO_LAYOUT_BY_BANK. A leitura e a tela não mudam.
"""

from cnablens.layouts import febraban400 as febraban
from cnablens.layouts import santander240, santander400, sicoob240, sicoob400
from cnablens.layouts import sicredi400 as sicredi
from cnablens.layouts.base import (
    Estrutura240,
    Layout240,
    Layout400,
    PorTipo,
    RegistroOpcional,
    Segmentos,
    campos_nao_mapeados,
)

# --- CNAB 400 -----------------------------------------------------------------

_MENSAGEM_NA_FICHA = "Mensagem na Ficha de Compensação"

_SANTANDER400_REGISTROS = {
    # o registro 2 é a mensagem do Recibo do Pagador na remessa e os dados de QR Code/PIX no retorno
    "2": RegistroOpcional(
        remessa=("Registro 2 - Mensagem no Recibo do Pagador", santander400.MENSAGEM_REMESSA_FIELDS),
        retorno=("Registro 2 - Dados de QR Code/PIX", santander400.QRCODE_RETORNO_FIELDS),
    ),
    **{
        tipo: RegistroOpcional(remessa=(f"Registro {tipo} - {_MENSAGEM_NA_FICHA}", santander400.MENSAGEM_REMESSA_FIELDS))
        for tipo in ("4", "5", "6", "7")
    },
    "8": RegistroOpcional(
        remessa=("Registro 8 - Tipo de pagamento e dados de QR Code/PIX", santander400.QRCODE_REMESSA_FIELDS),
    ),
}

# --- CNAB 240 -----------------------------------------------------------------


def _santander240_chave_segmento(tipo_arquivo, letra, linha):
    """Y e S se subdividem no Santander: o Y pelo sub-código das posições 18-19 (Y-03, Y-53, Y-04) e o S
    pelo formato da posição 18 (S-1, S-2). Os demais segmentos usam a própria letra."""
    if letra == "Y":
        return "Y-" + (linha + "  ")[17:19]
    if letra == "S":
        return "S-" + (linha + " ")[17:18]
    return letra


_SICOOB240_ESTRUTURA = Estrutura240(
    header_arquivo=PorTipo(sicoob240.HEADER_ARQUIVO_REMESSA_FIELDS, sicoob240.HEADER_ARQUIVO_RETORNO_FIELDS),
    header_lote=PorTipo(sicoob240.HEADER_LOTE_REMESSA_FIELDS, sicoob240.HEADER_LOTE_RETORNO_FIELDS),
    segmento=Segmentos(sicoob240.SEGMENTOS),
    trailer_lote=PorTipo(sicoob240.TRAILER_LOTE_REMESSA_FIELDS, sicoob240.TRAILER_LOTE_RETORNO_FIELDS),
    trailer_arquivo=PorTipo.igual(sicoob240.TRAILER_ARQUIVO_FIELDS),
)

_SANTANDER240_ESTRUTURA = Estrutura240(
    header_arquivo=PorTipo(santander240.HEADER_ARQUIVO_REMESSA_FIELDS, santander240.HEADER_ARQUIVO_RETORNO_FIELDS),
    header_lote=PorTipo(santander240.HEADER_LOTE_REMESSA_FIELDS, santander240.HEADER_LOTE_RETORNO_FIELDS),
    segmento=Segmentos(santander240.SEGMENTOS),
    trailer_lote=PorTipo(santander240.TRAILER_LOTE_REMESSA_FIELDS, santander240.TRAILER_LOTE_RETORNO_FIELDS),
    trailer_arquivo=PorTipo(santander240.TRAILER_ARQUIVO_REMESSA_FIELDS, santander240.TRAILER_ARQUIVO_RETORNO_FIELDS),
    chave_segmento=_santander240_chave_segmento,
)

# --- Registro -------------------------------------------------------------------

LAYOUTS = {layout.key: layout for layout in (
    Layout400(
        key="febraban",
        label="CNAB400 FEBRABAN (Padrão)",
        header_fields=PorTipo.igual(febraban.HEADER_FIELDS),
        detail_fields=PorTipo(febraban.DETAIL_REMESSA_FIELDS, febraban.DETAIL_RETORNO_FIELDS),
        trailer_fields=PorTipo.igual(febraban.TRAILER_FIELDS),
        ocorrencia_codes=febraban.OCORRENCIA_CODES,
    ),
    Layout400(
        key="sicredi",
        label="CNAB400 Sicredi",
        header_fields=PorTipo(sicredi.HEADER_REMESSA_FIELDS, sicredi.HEADER_RETORNO_FIELDS),
        detail_fields=PorTipo(sicredi.DETAIL_REMESSA_FIELDS, sicredi.DETAIL_RETORNO_FIELDS),
        trailer_fields=PorTipo.igual(sicredi.TRAILER_FIELDS),
        ocorrencia_codes=sicredi.OCORRENCIA_CODES,
    ),
    Layout400(
        key="sicoob400",
        label="CNAB400 Sicoob",
        header_fields=PorTipo(sicoob400.HEADER_REMESSA_FIELDS, sicoob400.HEADER_RETORNO_FIELDS),
        detail_fields=PorTipo(sicoob400.DETAIL_REMESSA_FIELDS, sicoob400.DETAIL_RETORNO_FIELDS),
        trailer_fields=PorTipo(sicoob400.TRAILER_REMESSA_FIELDS, sicoob400.TRAILER_RETORNO_FIELDS),
        ocorrencia_codes=sicoob400.OCORRENCIA_CODES,
        comando_codes=sicoob400.COMANDO_REMESSA_CODES,
    ),
    Layout400(
        key="santander400",
        label="CNAB400 Santander",
        header_fields=PorTipo(santander400.HEADER_REMESSA_FIELDS, santander400.HEADER_RETORNO_FIELDS),
        detail_fields=PorTipo(santander400.DETAIL_REMESSA_FIELDS, santander400.DETAIL_RETORNO_FIELDS),
        trailer_fields=PorTipo(santander400.TRAILER_REMESSA_FIELDS, santander400.TRAILER_RETORNO_FIELDS),
        ocorrencia_codes=santander400.OCORRENCIA_CODES,
        comando_codes=santander400.COMANDO_REMESSA_CODES,
        record_types=_SANTANDER400_REGISTROS,
    ),
    Layout240(
        key="santander240",
        label="CNAB240 Santander",
        structure=_SANTANDER240_ESTRUTURA,
        ocorrencia_codes=santander240.MOVIMENTO_RETORNO_CODES,
        comando_codes=santander240.MOVIMENTO_REMESSA_CODES,
    ),
    Layout240(
        key="sicoob240",
        label="CNAB240 Sicoob",
        structure=_SICOOB240_ESTRUTURA,
        ocorrencia_codes=sicoob240.OCORRENCIA_RETORNO_CODES,
        comando_codes=sicoob240.MOVIMENTO_REMESSA_CODES,
    ),
)}

# Ordem de exibição no seletor da interface.
LAYOUT_ORDER = ["febraban", "sicredi", "sicoob400", "santander400", "sicoob240", "santander240"]

DEFAULT_LAYOUT_KEY = "febraban"

# Layout usado quando o banco do arquivo não tem layout próprio, pelo tamanho da linha. Para um CNAB 240
# de outro banco vale o do Sicoob: a estrutura de lote e segmento é a padrão FEBRABAN, mas campos
# específicos do banco podem divergir.
DEFAULT_LAYOUT_BY_WIDTH = {400: "febraban", 240: "sicoob240"}

# Bancos que, detectados no Header, pré-selecionam um layout próprio (o usuário pode trocar a qualquer
# momento). Chave: (código do banco, largura da linha).
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
    """Rótulos para o seletor da tela, na ordem de LAYOUT_ORDER."""
    return [LAYOUTS[key].label for key in LAYOUT_ORDER]


def key_for_label(label):
    for key in LAYOUT_ORDER:
        if LAYOUTS[key].label == label:
            return key
    return DEFAULT_LAYOUT_KEY


__all__ = [
    "AUTO_LAYOUT_BY_BANK", "DEFAULT_LAYOUT_BY_WIDTH", "DEFAULT_LAYOUT_KEY", "LAYOUTS", "LAYOUT_ORDER",
    "auto_layout_key", "campos_nao_mapeados", "default_key_for_width", "key_for_label", "layout_labels",
]
