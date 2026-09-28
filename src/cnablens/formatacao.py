# -*- coding: utf-8 -*-
"""Formatação de valores lidos dos arquivos CNAB: moeda (centavos implícitos), datas (DDMMAA, AAAAMMDD
ou DDMMAAAA) e o valor como aparece na coluna "Valor" do painel de campos. Não depende da interface."""


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
