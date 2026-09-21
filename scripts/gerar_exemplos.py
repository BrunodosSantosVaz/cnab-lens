# -*- coding: utf-8 -*-
"""Gera os arquivos de exemplo em exemplos/ (100% fictícios) para todos os layouts.

    python scripts/gerar_exemplos.py

Os dados (empresa, CNPJ, pagadores, valores) são inventados: servem para experimentar o
app e para os testes, sem expor nenhum dado de cliente real. Cada arquivo é montado a
partir das tabelas de campos em src/, então se um layout mudar, rode o script de novo.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

import cnab400_layout as febraban          # noqa: E402
import cnab400_layout_sicredi as sicredi   # noqa: E402
import cnab400_layout_sicoob as sicoob400  # noqa: E402
import cnab240_layout_sicoob as sicoob240  # noqa: E402

SAIDA = os.path.join(RAIZ, "exemplos")
EMPRESA = "EMPRESA EXEMPLO LTDA"
CNPJ = "11222333000181"
PAGADORES = [("MARIA EXEMPLO DA SILVA", "11144477735"), ("JOAO FICTICIO DE OLIVEIRA", "52998224725"),
             ("COMERCIO MODELO ME", "45997418000153")]


def montar(campos, largura, valores):
    """Monta uma linha: cada campo recebe o valor da 1ª chave de `valores` que for prefixo do
    nome do campo (numérico -> zeros à esquerda; texto -> espaços à direita); sem chave, branco."""
    linha = [" "] * largura
    for nome, ini, fim, _desc in campos:
        tam = fim - ini + 1
        for chave, valor in valores.items():
            if nome.startswith(chave):
                valor = str(valor)
                valor = valor.rjust(tam, "0") if valor.isdigit() else valor.ljust(tam)
                linha[ini - 1:fim] = list(valor[:tam])
                break
    return "".join(linha)


def pos(linha, ini, texto):
    return linha[:ini - 1] + texto + linha[ini - 1 + len(texto):]


def gravar(nome, linhas, largura):
    for i, ln in enumerate(linhas, 1):
        assert len(ln) == largura, (nome, i, len(ln))
    with open(os.path.join(SAIDA, nome), "w", encoding="latin-1", newline="") as f:
        f.write("\r\n".join(linhas) + "\r\n")
    print("  ", nome, f"({len(linhas)} linhas de {largura})")


def seq(n):
    return str(n).rjust(6, "0")


# ---------------------------------------------------------------- CNAB400 FEBRABAN
def febraban_arquivo(tipo):
    ret = tipo == "Retorno"
    h = montar(febraban.HEADER_FIELDS, 400, {
        "Identificação do Registro": "0", "Identificação do Arquivo": "2" if ret else "1",
        "Literal de Remessa/Retorno": "RETORNO" if ret else "REMESSA", "Código do Serviço": "01",
        "Literal de Serviço": "COBRANCA", "Agência do Cedente": "1234", "Conta Corrente do Cedente": "56789",
        "Nome da Empresa": EMPRESA, "Código do Banco": "341", "Nome do Banco": "BANCO EXEMPLO",
        "Data de Gravação": "210926", "Número Sequencial do Registro": seq(1)})
    detalhes = []
    for i, (nome, _doc) in enumerate(PAGADORES[:2], 1):
        if ret:
            campos = febraban.DETAIL_RETORNO_FIELDS
            v = {"Identificação do Registro": "1", "Código de Inscrição da Empresa": "02", "Número de Inscrição da Empresa": CNPJ,
                 "Nosso Número (Identificação do Título no Banco)": f"1000000{i}", "Código da Ocorrência": "06" if i == 1 else "02",
                 "Data da Ocorrência": "210926", "Número do Documento": f"NF-{1000 + i}", "Data de Vencimento": "251026",
                 "Valor Nominal": 15990 * i, "Valor Principal": 15990 * i if i == 1 else 0, "Nome do Pagador": nome,
                 "Número Sequencial do Registro": seq(i + 1)}
        else:
            campos = febraban.DETAIL_REMESSA_FIELDS
            v = {"Identificação do Registro": "1", "Código de Inscrição da Empresa": "02", "Número de Inscrição da Empresa": CNPJ,
                 "Nosso Número (Identificação do Título no Banco)": f"1000000{i}", "Identificação da Ocorrência": "01",
                 "Número do Documento": f"NF-{1000 + i}", "Data de Vencimento": "251026", "Valor Nominal": 15990 * i,
                 "Nome do Sacado": nome, "Número Sequencial do Registro": seq(i + 1)}
        detalhes.append(montar(campos, 400, v))
    t = montar(febraban.TRAILER_FIELDS, 400, {"Identificação do Registro": "9", "Número Sequencial do Registro": seq(4)})
    return [h] + detalhes + [t]


# ---------------------------------------------------------------- CNAB400 Sicredi
def sicredi_arquivo(tipo):
    ret = tipo == "Retorno"
    h = montar(sicredi.HEADER_RETORNO_FIELDS if ret else sicredi.HEADER_REMESSA_FIELDS, 400, {
        "Identificação do Registro": "0", "Identificação do Arquivo": "2" if ret else "1",
        "Literal Remessa": "REMESSA", "Literal Retorno": "RETORNO", "Código do Serviço": "01",
        "Literal Cobrança": "COBRANCA", "Código do Beneficiário": "12345", "CPF/CNPJ do Beneficiário": CNPJ,
        "Número do Sicredi": "748", "Literal Sicredi": "SICREDI", "Literal (": "BANSICREDI", "Data de Geração": "20260921",
        "Número Sequencial": "1", "Versão do Sistema": "2.00", "Número Sequencial do Registro": seq(1)})
    detalhes = []
    for i, (nome, doc) in enumerate(PAGADORES[:2], 1):
        if ret:
            campos = sicredi.DETAIL_RETORNO_FIELDS
            v = {"Identificação do Registro": "1", "Tipo de Cobrança": "A", "Nosso Número": f"26100{i}0000000{i}",
                 "Código da Ocorrência": "06" if i == 1 else "02", "Data da Ocorrência": "210926",
                 "Seu Número": f"NF-{1000 + i}", "Data de Vencimento": "251026", "Valor do Título": 15990 * i,
                 "Valor Efetivamente Pago": 15990 if i == 1 else 0, "Número Sequencial do Registro": seq(i + 1)}
        else:
            campos = sicredi.DETAIL_REMESSA_FIELDS
            v = {"Identificação do Registro": "1", "Tipo de Cobrança": "A", "Tipo de Carteira": "A", "Tipo de Impressão": "A",
                 "Tipo de Moeda": "A", "Nosso Número [Ano": "26", "Nosso Número [Byte": "2", "Nosso Número [Número": f"0000{i}",
                 "Nosso Número [Dígito": "7", "Instrução (": "01", "Seu Número": f"NF-{1000 + i}", "Data de Vencimento": "251026",
                 "Valor do Título": 15990 * i, "Data de Emissão": "210926", "Tipo de Inscrição do Pagador": "1",
                 "CPF/CNPJ do Pagador": doc, "Nome do Pagador": nome, "Endereço do Pagador": "RUA EXEMPLO 100",
                 "CEP do Pagador": "86000000", "Número Sequencial do Registro": seq(i + 1)}
        detalhes.append(montar(campos, 400, v))
    t = montar(sicredi.TRAILER_FIELDS, 400, {"Identificação do Registro": "9", "Identificação do Arquivo": "2" if ret else "1",
                                              "Número do Sicredi": "748", "Código do Beneficiário": "12345",
                                              "Número Sequencial do Registro": seq(4)})
    return [h] + detalhes + [t]


# ---------------------------------------------------------------- CNAB400 Sicoob
def sicoob400_arquivo(tipo):
    ret = tipo == "Retorno"
    h = montar(sicoob400.HEADER_RETORNO_FIELDS if ret else sicoob400.HEADER_REMESSA_FIELDS, 400, {
        "Identificação do Registro": "0", "Tipo de Operação": "2" if ret else "1",
        "Identificação por Extenso do Tipo de Operação": "RETORNO" if ret else "REMESSA",
        "Identificação do Tipo de Serviço": "01", "Identificação por Extenso do Tipo de Serviço": "COBRANÇA",
        "Prefixo da Cooperativa": "4321", "Código do Cliente": "00012345", "Nome do Beneficiário": EMPRESA,
        "Identificação do Banco": "756BANCOOBCED", "Data da Gravação": "210926", "Sequencial da Remessa": "1",
        "Número Sequencial": "1"})
    if ret:
        h = pos(h, 77, "756BANCOOBCED"); h = pos(h, 95, "210926")
    detalhes = []
    for i, (nome, doc) in enumerate(PAGADORES[:2], 1):
        if ret:
            campos = sicoob400.DETAIL_RETORNO_FIELDS
            v = {"Identificação do Registro": "1", "CPF/CNPJ do Beneficiário": CNPJ, "Nosso Número [Sequencial]": f"1000000000{i}",
                 "Nosso Número [DV]": "4", "Código da Ocorrência": "06" if i == 1 else "02", "Data da Ocorrência": "210926",
                 "Número do Documento": f"NF-{1000 + i}", "Data de Vencimento": "251026", "Valor Nominal": 15990 * i,
                 "Valor Pago": 15990 if i == 1 else 0, "CPF/CNPJ do Pagador": doc, "Número Sequencial": seq(i + 1)}
        else:
            campos = sicoob400.DETAIL_REMESSA_FIELDS
            v = {"Identificação do Registro": "1", "Tipo de Inscrição do Beneficiário": "02", "CPF/CNPJ do Beneficiário": CNPJ,
                 "Nosso Número [Sequencial]": f"1000000000{i}", "Nosso Número [DV]": "4", "Identificação da Ocorrência": "01",
                 "Número do Documento": f"NF-{1000 + i}", "Data de Vencimento": "251026", "Valor Nominal": 15990 * i,
                 "Data de Emissão": "210926", "Tipo de Inscrição do Sacado": "01", "CPF/CNPJ do Sacado": doc,
                 "Nome do Sacado": nome, "Endereço do Sacado": "RUA EXEMPLO 100", "Número Sequencial": seq(i + 1)}
        detalhes.append(montar(campos, 400, v))
    t = montar(sicoob400.TRAILER_RETORNO_FIELDS if ret else sicoob400.TRAILER_REMESSA_FIELDS, 400,
               {"Identificação do Registro": "9", "Número Sequencial": seq(4)})
    return [h] + detalhes + [t]


# ---------------------------------------------------------------- CNAB240 Sicoob
def sicoob240_arquivo(tipo):
    ret = tipo == "Retorno"
    ha = pos(montar(sicoob240.HEADER_ARQUIVO_RETORNO_FIELDS if ret else sicoob240.HEADER_ARQUIVO_REMESSA_FIELDS, 240, {}), 1, "7560000")
    ha = pos(ha, 8, "0"); ha = pos(ha, 73, EMPRESA.ljust(30)); ha = pos(ha, 103, "SICOOB".ljust(30))
    ha = pos(ha, 143, "2" if ret else "1"); ha = pos(ha, 144, "21092026")
    hl = pos(montar(sicoob240.HEADER_LOTE_RETORNO_FIELDS if ret else sicoob240.HEADER_LOTE_REMESSA_FIELDS, 240, {}), 1, "7560001")
    hl = pos(hl, 8, "1")
    contador = [0]

    def segmento(campos, letra, valores):
        contador[0] += 1
        ln = montar(campos, 240, valores)
        ln = pos(ln, 1, "7560001"); ln = pos(ln, 8, "3"); ln = pos(ln, 9, str(contador[0]).rjust(5, "0"))
        return pos(ln, 14, letra)

    linhas = [ha, hl]
    for i, (nome, doc) in enumerate(PAGADORES[:2], 1):
        nosso = f"10000000{i}0101"
        if ret:
            linhas.append(segmento(sicoob240.SEGMENTO_T_RETORNO_FIELDS, "T", {
                "Código de Movimento": "06" if i == 1 else "02", "Nosso Número": nosso, "Número do Documento": f"NF-{1000 + i}",
                "Data de Vencimento": "25102026", "Valor Nominal": 15990 * i, "Nome do Pagador": nome}))
            linhas.append(segmento(sicoob240.SEGMENTO_U_RETORNO_FIELDS, "U", {
                "Código de Movimento": "06" if i == 1 else "02", "Valor Pago": 15990 if i == 1 else 0,
                "Data da Ocorrência": "21092026", "Data do Crédito": "22092026"}))
        else:
            linhas.append(segmento(sicoob240.SEGMENTO_P_REMESSA_FIELDS, "P", {
                "Código de Movimento": "01", "Nosso Número": nosso, "Número do Documento": f"NF-{1000 + i}",
                "Data de Vencimento": "25102026", "Valor Nominal": 15990 * i, "Data de Emissão": "21092026"}))
            linhas.append(segmento(sicoob240.SEGMENTO_Q_REMESSA_FIELDS, "Q", {
                "Código de Movimento": "01", "Tipo de Inscrição do Pagador": "1", "Número de Inscrição do Pagador": doc,
                "Nome do Pagador": nome, "Cidade do Pagador": "LONDRINA", "UF do Pagador": "PR"}))
    tl = pos(montar(sicoob240.TRAILER_LOTE_RETORNO_FIELDS if ret else sicoob240.TRAILER_LOTE_REMESSA_FIELDS, 240, {}), 1, "7560001")
    tl = pos(tl, 8, "5")
    ta = pos(pos(montar(sicoob240.TRAILER_ARQUIVO_FIELDS, 240, {}), 1, "7569999"), 8, "9")
    return linhas + [tl, ta]


def main():
    os.makedirs(SAIDA, exist_ok=True)
    print("Gerando exemplos em", SAIDA)
    for nome, fabrica, largura in (("febraban", febraban_arquivo, 400), ("sicredi", sicredi_arquivo, 400),
                                   ("sicoob400", sicoob400_arquivo, 400), ("sicoob240", sicoob240_arquivo, 240)):
        gravar(f"{nome}_remessa.rem", fabrica("Remessa"), largura)
        gravar(f"{nome}_retorno.ret", fabrica("Retorno"), largura)


if __name__ == "__main__":
    main()
