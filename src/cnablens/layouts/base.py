"""Blocos com que os layouts são descritos (CNAB 400 e 240).

Um campo é a tupla `(nome, início, fim, descrição)`, com posições 1-indexadas e inclusivas; uma lista de
campos descreve um tipo de registro e cobre todas as posições da linha, sem lacunas.

    PorTipo          escolhe a lista de campos pelo tipo do arquivo (Remessa ou Retorno)
    RegistroOpcional registro além de Header/Detalhe/Trailer que só alguns layouts CNAB 400 descrevem
    Segmentos        segmentos do CNAB 240 por (tipo do arquivo, chave do segmento)
    Estrutura240     como achar os campos de cada tipo de registro do CNAB 240
    Layout400        um layout CNAB 400
    Layout240        um layout CNAB 240

Os módulos de cada banco (febraban400.py, sicoob240.py...) só têm dados; o registro dos layouts fica em
layouts/__init__.py.
"""
from collections.abc import Callable
from dataclasses import dataclass, field

REMESSA = "Remessa"
RETORNO = "Retorno"


def validar_contiguidade(campos, largura, nome="campos"):
    """Confere que a lista cobre as posições 1..largura, sem lacuna nem sobreposição, e que todo campo tem
    nome e descrição. Levanta ValueError dizendo onde está o problema."""
    esperado = 1
    for campo in campos:
        if len(campo) != 4:
            raise ValueError(f"{nome}: campo deve ser (nome, início, fim, descrição): {campo!r}")
        titulo, inicio, fim, descricao = campo
        if not (titulo and descricao):
            raise ValueError(f"{nome}: campo sem nome ou descrição na posição {inicio}")
        if inicio != esperado:
            raise ValueError(f"{nome}: '{titulo}' começa em {inicio}, esperado {esperado}")
        if fim < inicio:
            raise ValueError(f"{nome}: '{titulo}' termina antes de começar ({inicio}-{fim})")
        esperado = fim + 1
    if esperado != largura + 1:
        raise ValueError(f"{nome}: termina em {esperado - 1}, esperado {largura}")


def campos_nao_mapeados(largura):
    """Campos de um registro que o layout escolhido não descreve (ex.: um segmento CNAB 240 desconhecido):
    a linha inteira como um campo só."""
    return [(
        "Conteúdo do Registro (não mapeado neste layout)", 1, largura,
        "Registro que este layout não descreve (tipo ou segmento não previsto); "
        "o conteúdo bruto é exibido inteiro.",
    )]


@dataclass(frozen=True)
class PorTipo:
    """Lista de campos que depende do tipo do arquivo: `PorTipo(remessa, retorno)(tipo_arquivo)`.
    Quando os dois tipos usam a mesma lista, use `PorTipo.igual(campos)`."""
    remessa: list
    retorno: list

    @classmethod
    def igual(cls, campos):
        return cls(campos, campos)

    def __call__(self, tipo_arquivo):
        return self.retorno if tipo_arquivo == RETORNO else self.remessa


@dataclass(frozen=True)
class RegistroOpcional:
    """Registro CNAB 400 além de Header (0), Detalhe (1) e Trailer (9), como os de QR Code/PIX e de mensagens
    do Santander. Para cada tipo de arquivo: (rótulo, campos), ou None se o registro não existe nele.
    Esses registros ficam agrupados sob o Detalhe que os precede."""
    remessa: tuple | None = None
    retorno: tuple | None = None

    def __call__(self, tipo_arquivo):
        return self.retorno if tipo_arquivo == RETORNO else self.remessa


@dataclass(frozen=True)
class Segmentos:
    """Campos dos segmentos do CNAB 240: `Segmentos(tabela)(tipo_arquivo, chave)`, com a tabela
    {(tipo_arquivo, chave do segmento): campos}. Segmento que o layout não descreve: None."""
    tabela: dict

    def __call__(self, tipo_arquivo, chave):
        return self.tabela.get((tipo_arquivo, chave))


@dataclass(frozen=True)
class Estrutura240:
    """Como achar os campos de cada tipo de registro do CNAB 240. Cada item é chamado com o tipo do
    arquivo (o `segmento`, também com a chave do segmento).

    `chave_segmento` (opcional): (tipo_arquivo, letra do segmento, linha) -> chave usada em `segmento`.
    Sem ele, a chave é a própria letra. O Santander usa para os segmentos que se subdividem (Y-03, S-1...)."""
    header_arquivo: Callable
    header_lote: Callable
    segmento: Callable
    trailer_lote: Callable
    trailer_arquivo: Callable
    chave_segmento: Callable | None = None


@dataclass(frozen=True)
class Layout400:
    """Um layout CNAB 400: campos de Header, Detalhe e Trailer (cada um um PorTipo), tabelas de códigos e,
    se houver, os registros opcionais ({caractere da posição 1: RegistroOpcional})."""
    key: str
    label: str
    header_fields: PorTipo
    detail_fields: PorTipo
    trailer_fields: PorTipo
    ocorrencia_codes: dict
    comando_codes: dict | None = None
    record_types: dict | None = None
    width: int = field(default=400, init=False)
    structure: None = field(default=None, init=False)


@dataclass(frozen=True)
class Layout240:
    """Um layout CNAB 240: a estrutura (Estrutura240) e as tabelas de códigos."""
    key: str
    label: str
    structure: Estrutura240
    ocorrencia_codes: dict
    comando_codes: dict | None = None
    width: int = field(default=240, init=False)
    record_types: None = field(default=None, init=False)
