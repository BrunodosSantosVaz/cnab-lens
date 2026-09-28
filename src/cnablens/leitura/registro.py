# -*- coding: utf-8 -*-
"""Um registro (linha) do arquivo CNAB e um lançamento formado por vários registros.

    CnabRecord  uma linha: tipo de registro (Header, Detalhe, Trailer, segmento...) e os campos, depois que
                um layout é aplicado
    CnabGroup   vários registros tratados como um só na tela (os segmentos de um título CNAB 240, ou um
                Detalhe CNAB 400 com os registros opcionais que vêm depois dele)
"""


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
