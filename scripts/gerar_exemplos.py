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
import cnab400_layout_santander as santander400  # noqa: E402
import cnab240_layout_santander as santander240  # noqa: E402
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


# ---------------------------------------------------------------- CNAB400 Santander
TXID = "SANTANDERTXID000000000000000042"  # 30 caracteres, fictício
CHAVE_PIX = "chave-pix-ficticia@exemplo.com.br"
URL_QR = "https://pix.exemplo.com.br/qr/v2/00000000-0000-0000-0000-000000000042"


def santander400_arquivo(tipo):
    ret = tipo == "Retorno"
    if ret:
        h = montar(santander400.HEADER_RETORNO_FIELDS, 400, {
            "Código do registro": "0", "Código da remessa": "2", "Literal de transmissão": "RETORNO",
            "Código de serviço": "01", "Literal do serviço": "COBRANCA", "Código da agência do beneficiário": "1234",
            "Conta Movimento do beneficiário": "56789", "Conta Cobrança do beneficiário": "56789",
            "Nome do beneficiário": EMPRESA, "Código do banco": "033", "Nome do banco": "SANTANDER",
            "Data da geração do arquivo": "210926", "Código do beneficiário": "12345", "Sigla da empresa no sistema": "EXEM",
            "Número Sequência do arquivo": "1", "Número Sequencial do registro no arquivo": "1"})
    else:
        h = montar(santander400.HEADER_REMESSA_FIELDS, 400, {
            "Código do Registro": "0", "Código da Remessa": "1", "Literal de Transmissão": "REMESSA",
            "Código do Tipo Serviço": "01", "Literal de Serviço": "COBRANCA", "Código de Transmissão": "12340056789000000001",
            "Nome do Beneficiário": EMPRESA, "Código do Banco": "033", "Nome do Banco": "SANTANDER",
            "Data da Geração do Arquivo": "210926", "Mensagem 1": "MENSAGEM FICTICIA DO ARQUIVO",
            "Nº sequencial do arquivo": "1", "Nº sequencial do registro no arquivo": "1"})
    linhas, n, total = [h], 1, 0
    for i, (nome, doc) in enumerate(PAGADORES[:2], 1):
        n += 1
        valor = 15990 * i
        total += valor
        if ret:
            linhas.append(montar(santander400.DETAIL_RETORNO_FIELDS, 400, {
                "Código do Registro": "1", "Tipo de inscrição do beneficiário": "02", "Inscrição do beneficiário": CNPJ,
                "Código de agência do beneficiário": "1234", "Conta movimento do beneficiário": "56789",
                "Conta cobrança do beneficiário": "56789", "Identificação do boleto na empresa cliente": f"CTRL-{i}",
                "Nosso Número": f"0000123{i}", "Tipo de Cobrança": "5",
                "Código de Movimento de Retorno": "06" if i == 1 else "02", "Data da ocorrência": "210926",
                "Número do Documento": f"NF-{1000 + i}", "Código Original da remessa": "01",
                "Data de vencimento do boleto": "251026", "Valor nominal do boleto": valor, "Número do banco cobrador": "033",
                "Espécie do boleto": "01", "Valor Pago": valor if i == 1 else 0, "Data da efetivação crédito": "220926",
                "Nome do Pagador": nome, "Sigla da empresa no sistema": "EXEM", "Número Sequência do arquivo": "1",
                "Número Sequencial do registro": seq(n)}))
        else:
            linhas.append(montar(santander400.DETAIL_REMESSA_FIELDS, 400, {
                "Código do Registro": "1", "Tipo de inscrição do beneficiário": "02", "Inscrição do beneficiário": CNPJ,
                "Código da agência beneficiário": "1234", "Conta movimento beneficiário": "56789",
                "Conta cobrança beneficiário": "56789", "Identificação do boleto na empresa": f"CTRL-{i}",
                "Nosso Número": f"0000123{i}", "Código de Multa": "2", "Percentual de Multa": "200", "Código da Moeda": "00",
                "Tipo de Cobrança": "5", "Código de Movimento Remessa": "01", "Número do Documento": f"NF-{1000 + i}",
                "Data de vencimento do boleto": "251026", "Valor nominal do boleto": valor, "Número do banco cobrador": "033",
                "Espécie do boleto": "01", "Identificação boleto aceite": "N", "Data de emissão do boleto": "210926",
                "Tipo de inscrição do Pagador": "01", "Inscrição do Pagador": doc, "Nome do Pagador": nome,
                "Endereço do Pagador": "RUA EXEMPLO 100", "Bairro do Pagador": "CENTRO", "Cep do Pagador": "86000",
                "Sufixo do Cep do Pagador": "000", "Cidade do Pagador": "LONDRINA", "Unidade de Federação do Pagador": "PR",
                "Número de dias corridos para Protesto": "00", "Número sequencial do registro": seq(n)}))
        if i == 1:  # o primeiro boleto leva QR Code/PIX (Boleto SX) e uma mensagem no recibo
            n += 1
            if ret:
                linhas.append(montar(santander400.QRCODE_RETORNO_FIELDS, 400, {
                    "Código do Registro": "2", "Tipo de Chave DICT": "1", "Código Chave DICT": URL_QR,
                    "Código de identificação do Qr Code": TXID, "Número Sequência do arquivo": "1",
                    "Número Sequencial do Registro": seq(n)}))
            else:
                linhas.append(montar(santander400.QRCODE_REMESSA_FIELDS, 400, {
                    "Código do Registro": "8", "Identificação do tipo de pagamento": "01", "Quantidade de pagamento": "01",
                    "Tipo de valor informado": "1", "Tipo de Chave DICT": "1", "Código Chave DICT": CHAVE_PIX,
                    "Código de identificação do Qr Code": TXID, "Número sequencial do registro": seq(n)}))
                n += 1
                linhas.append(montar(santander400.MENSAGEM_REMESSA_FIELDS, 400, {
                    "Código do registro": "2", "Código da Agência do Beneficiário": "1234", "Conta Movimento Beneficiário": "56789",
                    "Conta Cobrança Beneficiário": "56789", "Sub-sequência do registro (1ª": "01",
                    "Mensagem variável por boleto (1ª": "PAGUE ATE O VENCIMENTO. MENSAGEM FICTICIA.",
                    "Número sequencial do registro": seq(n)}))
    n += 1
    if ret:
        t = montar(santander400.TRAILER_RETORNO_FIELDS, 400, {
            "Código de registro": "9", "Código da remessa": "2", "Código do Serviço": "01", "Código do banco": "033",
            "Quantidade de registros na cobrança Simples": "2", "Valor total dos boletos na cobrança Simples": total,
            "Número do aviso de cobrança Simples": "1", "Número Sequência do arquivo": "1",
            "Número Sequencial do registro": seq(n)})
    else:
        t = montar(santander400.TRAILER_REMESSA_FIELDS, 400, {
            "Código do Registro": "9", "Quantidade de registro no arquivo": str(n), "Valor Total dos boletos": total,
            "Número sequencial de registro no arquivo": seq(n)})
    linhas.append(t)
    return linhas


# ---------------------------------------------------------------- CNAB240 Santander
def santander240_arquivo(tipo):
    ret = tipo == "Retorno"

    def fixa(linha, lote, registro):
        linha = pos(linha, 1, "033" + lote)
        return pos(linha, 8, registro)

    ha = fixa(montar(santander240.HEADER_ARQUIVO_RETORNO_FIELDS if ret else santander240.HEADER_ARQUIVO_REMESSA_FIELDS, 240, {
        "Tipo de inscrição da empresa": "2", "Inscrição da empresa": CNPJ, "Código de Transmissão": "123400567890001",
        "Agência do Beneficiário": "1234", "Número da conta corrente": "56789", "Código do Beneficiário": "12345",
        "Nome da empresa": EMPRESA, "Nome do Banco": "BANCO SANTANDER", "Código remessa": "2" if ret else "1",
        "Data de geração": "21092026", "Nº seqüencial do arquivo": "1", "Nº da versão do layout do arquivo": "040"}), "0000", "0")
    hl = fixa(montar(santander240.HEADER_LOTE_RETORNO_FIELDS if ret else santander240.HEADER_LOTE_REMESSA_FIELDS, 240, {
        "Tipo de operação": "T" if ret else "R", "Tipo de serviço": "01", "Nº da versão do layout do lote": "040",
        "Tipo de inscrição da empresa": "2", "Inscrição da empresa": CNPJ, "Código de Transmissão": "123400567890001",
        "Código do Beneficiário": "12345", "Nome do Beneficiário": EMPRESA, "Nome da empresa": EMPRESA,
        "Mensagem 1": "MENSAGEM FICTICIA DO LOTE", "Número remessa/retorno": "1", "Número do Retorno": "1",
        "Data da gravação remessa/retorno": "21092026"}), "0001", "1")
    contador = [0]

    def segmento(campos, letra, valores):
        contador[0] += 1
        ln = montar(campos, 240, valores)
        ln = pos(ln, 1, "0330001"); ln = pos(ln, 8, "3"); ln = pos(ln, 9, str(contador[0]).rjust(5, "0"))
        return pos(ln, 14, letra)

    linhas = [ha, hl]
    for i, (nome, doc) in enumerate(PAGADORES[:2], 1):
        nosso = f"000000012340{i}"[-13:]
        valor = 15990 * i
        if ret:
            mov = "06" if i == 1 else "02"
            linhas.append(segmento(santander240.SEGMENTO_T_RETORNO_FIELDS, "T", {
                "Código de Movimento (Ocorrência)": mov, "Agência do Beneficiário": "1234", "Número da conta corrente": "56789",
                "Nosso Número": nosso, "Código da carteira": "5", "Número do Documento": f"NF-{1000 + i}",
                "Data de Vencimento do boleto": "25102026", "Valor nominal do boleto": valor, "Código da moeda": "09",
                "Tipo de inscrição Pagador": "1", "Inscrição Pagador": doc, "Nome do Pagador": nome,
                "Valor da Tarifa/Custas": 0}))
            linhas.append(segmento(santander240.SEGMENTO_U_RETORNO_FIELDS, "U", {
                "Código de Movimento (Ocorrência)": mov, "Valor Pago pelo Pagador": valor if i == 1 else 0,
                "Valor liquido a ser creditado": valor if i == 1 else 0, "Data da ocorrência do Pagador": "",
                "Data da ocorrência": "21092026", "Data da efetivação do crédito": "22092026"}))
            if i == 1:
                linhas.append(segmento(santander240.SEGMENTO_Y03_RETORNO_FIELDS, "Y", {
                    "Código de Movimento (Ocorrência)": mov, "Identificação Registro": "03", "Tipo de Chave Pix": "1",
                    "Chave Pix / URL do QR Code": URL_QR, "Código identificação do QR Code": TXID}))
        else:
            linhas.append(segmento(santander240.SEGMENTO_P_REMESSA_FIELDS, "P", {
                "Código de movimento remessa": "01", "Agência do Destinatário": "1234", "Número da conta corrente": "56789",
                "Nosso Número": nosso, "Tipo de cobrança": "5", "Forma de Cadastramento": "1", "Tipo de documento": "1",
                "Número do Documento": f"NF-{1000 + i}", "Data de vencimento do boleto": "25102026",
                "Valor nominal do boleto": valor, "Espécie do boleto": "02", "Identif. de boleto Aceito": "N",
                "Data da emissão do boleto": "21092026", "Código de juros de mora": "0", "Código do desconto 1": "0",
                "Identificação do boleto na empresa": f"CTRL-{i}", "Código para protesto": "3",
                "Código para Baixa/Devolução": "0", "Código da moeda": "09"}))
            linhas.append(segmento(santander240.SEGMENTO_Q_REMESSA_FIELDS, "Q", {
                "Código de movimento remessa": "01", "Tipo de inscrição do Pagador": "1", "Inscrição do Pagador": doc,
                "Nome do Pagador": nome, "Endereço do Pagador": "RUA EXEMPLO 100", "Bairro do Pagador": "CENTRO",
                "Cep do Pagador": "86000", "Sufixo do Cep do Pagador": "000", "Cidade do Pagador": "LONDRINA",
                "Unidade da Federação do Pagador": "PR"}))
            if i == 1:  # o primeiro título leva QR Code/PIX (Boleto SX)
                linhas.append(segmento(santander240.SEGMENTO_Y03_REMESSA_FIELDS, "Y", {
                    "Código de movimento Remessa": "01", "Identificação Registro": "03", "Tipo de Chave Pix": "1",
                    "Chave Pix": CHAVE_PIX, "Código identificação do QR Code": TXID}))
    if ret:
        tl = fixa(montar(santander240.TRAILER_LOTE_RETORNO_FIELDS, 240, {
            "Quantidade de registros do lote": str(len(linhas)), "Quantidade de Boletos cobrança simples": "2",
            "Valor total dos Boletos cobrança simples": 15990 + 31980}), "0001", "5")
    else:
        tl = fixa(montar(santander240.TRAILER_LOTE_REMESSA_FIELDS, 240, {
            "Quantidade de registros do lote": str(len(linhas))}), "0001", "5")
    ta = fixa(montar(santander240.TRAILER_ARQUIVO_RETORNO_FIELDS if ret else santander240.TRAILER_ARQUIVO_REMESSA_FIELDS, 240, {
        "Quantidade de lotes": "1", "Quantidade de registros do arquivo": str(len(linhas) + 2)}), "9999", "9")
    return linhas + [tl, ta]


def main():
    os.makedirs(SAIDA, exist_ok=True)
    print("Gerando exemplos em", SAIDA)
    for nome, fabrica, largura in (("febraban", febraban_arquivo, 400), ("sicredi", sicredi_arquivo, 400),
                                   ("sicoob400", sicoob400_arquivo, 400), ("sicoob240", sicoob240_arquivo, 240),
                                   ("santander400", santander400_arquivo, 400), ("santander240", santander240_arquivo, 240)):
        gravar(f"{nome}_remessa.rem", fabrica("Remessa"), largura)
        gravar(f"{nome}_retorno.ret", fabrica("Retorno"), largura)


if __name__ == "__main__":
    main()
