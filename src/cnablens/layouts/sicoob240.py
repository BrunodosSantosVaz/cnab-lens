# -*- coding: utf-8 -*-
"""
CNAB 240 Sicoob (Bancoob, banco 756) - Cobrança Bancária - field layout reference data.

O Sicoob usa o padrão FEBRABAN CNAB 240 para cobrança (o suporte a CNAB 400 foi
descontinuado), com particularidades próprias descritas abaixo. Cada linha do
arquivo tem 240 posições; o tipo de registro fica na posição 8 (0 = Header de
Arquivo, 1 = Header de Lote, 3 = Detalhe, 5 = Trailer de Lote, 9 = Trailer de
Arquivo) e a letra do segmento na posição 14 (registros tipo 3). Todas as
posições abaixo são 1-indexadas e inclusivas (inicio, fim).

Fonte usada (acessada 2026-09-21):
  Sicoob - planilha oficial "Layouts para troca de informações" / "Instruções
  para montagem e validação de boletos de cobrança" (Implantação de Sistema
  Próprio), aba "03.Remessa - Opção CNAB240" e aba "04.Retorno - Opção CNAB240"
  (aba Introdução: "Atualização: 26/06/2019"; arquivo publicado em 23/02/2021 e
  ainda vigente no site do Sicoob, já contemplando a alteração de 18/03/2020 do
  Nosso Número para 20 posições, 38-57). Versão de layout declarada no próprio
  layout: arquivo "081"; lote "040" (Remessa) / "044" (Retorno).
  https://www.sicoob.com.br/documents/3068856/0/layout-cnab-240.xls/5bfadf52-4278-3d28-0b69-b09b467aad45
  O arquivo .xls é protegido com a senha padrão de "somente leitura" do Excel
  (VelvetSweatshop), aberto sem problemas; o manual em PDF de "Transferência de
  Arquivos de Cobrança" do Sicoobnet é apenas operacional e não contém layout.
  -> Fonte primária para TODAS as listas de campos (Header/Trailer de Arquivo,
     Header/Trailer de Lote, Segmentos P, Q, R, S, T, U) e para
     MOVIMENTO_REMESSA_CODES, OCORRENCIA_RETORNO_CODES e ESPECIE_TITULO_CODES.

Conferência cruzada (fonte secundária):
  - ACBr (frones/ACBr, ACBrBancoSicoob.pas): posições de leitura do Retorno
    (Segmentos T e U) e tabelas de motivos conferem com a planilha oficial.
  - brcobranca (kivanio/brcobranca, remessa/cnab240/sicoob.rb): versões de layout
    081/040, Trailer de Lote, Segmento R e formato do Nosso Número conferem.
  - MOTIVOS_CODES: a planilha oficial só cita alguns códigos como exemplo
    (03, 04, 08, 11, 21 em tarifas; 58 e 79 em rejeições) e remete à tabela
    FEBRABAN (rejeições 01-95 / tarifas 01-20). As tabelas completas aqui vêm
    do ACBr (transcrição da tabela FEBRABAN usada pelo Sicoob) - FONTE
    SECUNDÁRIA, confiança menor que as demais listas.

Notas sobre o layout do Sicoob:
  - Sequência de segmentos por título na Remessa: P, Q, R e (opcional) S. No
    Retorno, T e U (o manual do Sicoob não define Q/R/S no Retorno, nem
    Segmentos Y/Y-xx/W; por isso não estão modelados).
  - Header de Lote: Remessa (Tipo de Operação "R", layout "040") e Retorno
    ("T", layout "044") têm as MESMAS posições, mas conteúdos diferentes;
    por isso há duas listas (HEADER_LOTE_REMESSA_FIELDS / _RETORNO_FIELDS). O
    mesmo vale para o Trailer de Lote. O Trailer de Arquivo é único
    (TRAILER_ARQUIVO_FIELDS) para os dois sentidos.
  - Segmento S: o manual define duas variantes conforme o Tipo de Impressão
    (posição 18). Somente o tipo 3 (Corpo de Instruções, mensagens 5 a 9) é
    utilizado; a variante 1/2 (frente/verso) fica em lista separada
    (SEGMENTO_S_REMESSA_TIPO_IMPRESSAO_1_2_FIELDS) e não entra em SEGMENTOS.
  - "Nosso Número" (posições 38-57 nos Segmentos P e T) tem 20 posições,
    compostas por: NumTítulo (10) + Parcela (2) + Modalidade (2) + Tipo
    Formulário (1) + 5 brancos. Aqui é um único campo; a composição está na
    descrição.
  - Campos de data usam DDMMAAAA (8 posições); hora usa HHMMSS. Campos
    monetários têm 2 decimais implícitos (ex.: 13 inteiros + 2 decimais em 15
    posições).
  - Convenção de nomes (o app localiza colunas por substring): campos
    não monetários evitam de propósito as palavras "Desconto", "Juros", "Mora",
    "Abatimento", "Tarifa" etc. (ex.: "Código Desc. 1", "Código do Encargo por
    Atraso"), e campos de data evitam essas palavras, para não serem formatados
    como valor em R$.
  - "Valor/Percentual Desc. 1/2/3", "Valor/Taxa de Juros de Mora" e
    "Valor/Percentual da Multa" podem conter percentual (2 decimais) em vez de
    valor em R$, conforme o código do campo anterior.
  - Erros de digitação do manual corrigidos/anotados: Trailer de Lote posições
    76-92 (rotulado "Quantidade de Títulos em Carteiras", é valor); texto da
    ocorrência 38 do Retorno vem truncado no manual; ocorrência 43 tem "Pagadorr/
    Avalista" no Segmento T (é Sacador/Avalista, como no Segmento U); a
    descrição da "Data Juros Mora"/"Data da Multa" do manual escreve "DD = Ano"
    (é dia); formato correto DDMMAAAA.
  - Segmento U: o manual repete para "Data do Crédito" (146-153) a mesma
    descrição de "Data da Ocorrência"; é a data de efetivação do crédito.
  - Motivo da Ocorrência (Segmento T, posições 214-223): 5 códigos de 2
    posições, cada um interpretado conforme o Código de Movimento (ver
    MOTIVOS_CODES e descricao_motivo()).
"""


# ---------------------------------------------------------------------------
# Validação de layout
# ---------------------------------------------------------------------------


def _validate_contiguous(fields, name, width=240):
    """Confere que os campos cobrem 1..width sem lacunas nem sobreposição e que
    cada tupla tem (nome, inicio, fim, descricao) válidos."""
    expected = 1
    for i, f in enumerate(fields):
        if len(f) != 4:
            raise ValueError(f"{name}[{i}]: tupla deve ter 4 elementos: {f!r}")
        nome, ini, fim, desc = f
        if not (isinstance(nome, str) and nome and isinstance(desc, str) and desc):
            raise ValueError(f"{name}[{i}]: nome/descrição inválidos: {f!r}")
        if ini != expected:
            raise ValueError(f"{name}[{i}] {nome!r}: início {ini} != esperado {expected}")
        if fim < ini:
            raise ValueError(f"{name}[{i}] {nome!r}: fim {fim} < início {ini}")
        expected = fim + 1
    if expected != width + 1:
        raise ValueError(f"{name}: termina em {expected - 1}, esperado {width}")


# ---------------------------------------------------------------------------
# 1. Header de Arquivo (Registro tipo 0) - REMESSA (Beneficiário -> Sicoob)
# ---------------------------------------------------------------------------

HEADER_ARQUIVO_REMESSA_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Lote de Serviço do Header de Arquivo: sempre \"0000\"."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"0\" (Header de Arquivo)."),
    ("Uso Reservado (Filler)", 9, 17,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Tipo de Inscrição da Empresa", 18, 18,
     "Tipo de inscrição do Beneficiário (Empresa): '1' = CPF; '2' = CNPJ."),
    ("Número de Inscrição da Empresa", 19, 32,
     "CPF/CNPJ do Beneficiário, alinhado à direita com zeros à esquerda, sem pontuação."),
    ("Código do Convênio no Sicoob", 33, 52,
     "Código do Convênio no Sicoob - preencher com espaços em branco."),
    ("Prefixo da Cooperativa (Agência)", 53, 57,
     "Prefixo da Cooperativa (agência mantenedora da conta); vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador do Prefixo", 58, 58,
     "Dígito verificador do Prefixo da Cooperativa; vide planilha \"Contracapa\" do manual."),
    ("Número da Conta Corrente", 59, 70,
     "Número da conta corrente do convênio de cobrança; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Conta", 71, 71,
     "Dígito verificador da conta corrente; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Agência/Conta", 72, 72,
     "Dígito verificador da Agência/Conta - preencher com zeros."),
    ("Nome da Empresa", 73, 102,
     "Nome (razão social) do Beneficiário/Empresa."),
    ("Nome do Banco", 103, 132,
     "Nome do Banco: \"SICOOB\"."),
    ("Uso Reservado (Filler)", 133, 142,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Código Remessa/Retorno", 143, 143,
     "Código do arquivo: \"1\" = Remessa."),
    ("Data de Geração do Arquivo", 144, 151,
     "Data de geração do arquivo no formato DDMMAAAA."),
    ("Hora de Geração do Arquivo", 152, 157,
     "Hora de geração do arquivo no formato HHMMSS."),
    ("Número Sequencial do Arquivo (NSA)", 158, 163,
     "Número sequencial adotado e controlado por quem gera o arquivo, para ordenar os arquivos enviados; evoluir 1 a cada Header de Arquivo."),
    ("Versão do Layout do Arquivo", 164, 166,
     "Nº da versão do layout do arquivo: \"081\"."),
    ("Densidade de Gravação do Arquivo", 167, 171,
     "Densidade de gravação do arquivo: \"00000\"."),
    ("Uso Reservado (Filler) - Banco", 172, 191,
     "Para uso reservado do Banco - preencher com espaços em branco."),
    ("Uso Reservado (Filler) - Empresa", 192, 211,
     "Para uso reservado da Empresa - preencher com espaços em branco."),
    ("Uso Reservado (Filler)", 212, 240,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
]


# ---------------------------------------------------------------------------
# 2. Header de Arquivo (Registro tipo 0) - RETORNO (Sicoob -> Beneficiário)
# ---------------------------------------------------------------------------

HEADER_ARQUIVO_RETORNO_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Lote de Serviço do Header de Arquivo: sempre \"0000\"."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"0\" (Header de Arquivo)."),
    ("Uso Reservado (Filler)", 9, 17,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
    ("Tipo de Inscrição da Empresa", 18, 18,
     "Tipo de inscrição do Beneficiário (Empresa): '1' = CPF; '2' = CNPJ."),
    ("Número de Inscrição da Empresa", 19, 32,
     "CPF/CNPJ do Beneficiário, alinhado à direita com zeros à esquerda, sem pontuação."),
    ("Código do Convênio no Sicoob", 33, 52,
     "Código do Convênio no Sicoob - o sistema retorna as posições em branco."),
    ("Prefixo da Cooperativa (Agência)", 53, 57,
     "Prefixo da Cooperativa (agência mantenedora da conta); vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador do Prefixo", 58, 58,
     "Dígito verificador do Prefixo da Cooperativa - o sistema retorna preenchido com zero \"0\"."),
    ("Número da Conta Corrente", 59, 70,
     "Número da conta corrente do convênio de cobrança; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Conta", 71, 71,
     "Dígito verificador da conta corrente; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Agência/Conta", 72, 72,
     "Dígito verificador da Agência/Conta - o sistema retorna as posições com zeros."),
    ("Nome da Empresa", 73, 102,
     "Nome (razão social) do Beneficiário/Empresa."),
    ("Nome do Banco", 103, 132,
     "Nome do Banco: \"SICOOB\"."),
    ("Uso Reservado (Filler)", 133, 142,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
    ("Código Remessa/Retorno", 143, 143,
     "Código do arquivo: \"2\" = Retorno."),
    ("Data de Geração do Arquivo", 144, 151,
     "Data de geração do arquivo no formato DDMMAAAA."),
    ("Hora de Geração do Arquivo", 152, 157,
     "Hora de geração do arquivo no formato HHMMSS."),
    ("Número Sequencial do Arquivo (NSA)", 158, 163,
     "Número sequencial do arquivo, para ordenar a disposição dos arquivos encaminhados; evolui 1 a cada Header de Arquivo."),
    ("Versão do Layout do Arquivo", 164, 166,
     "Nº da versão do layout do arquivo: \"081\"."),
    ("Densidade de Gravação do Arquivo", 167, 171,
     "Densidade de gravação do arquivo: \"00000\"."),
    ("Uso Reservado (Filler) - Banco", 172, 191,
     "Para uso reservado do Banco - o sistema retorna as posições em branco."),
    ("Uso Reservado (Filler) - Empresa", 192, 211,
     "Para uso reservado da Empresa - o sistema retorna as posições em branco."),
    ("Uso Reservado (Filler)", 212, 240,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
]


# ---------------------------------------------------------------------------
# 3. Header de Lote (Registro tipo 1) - REMESSA
# ---------------------------------------------------------------------------

HEADER_LOTE_REMESSA_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"1\" (Header de Lote)."),
    ("Tipo de Operação", 9, 9,
     "Tipo de Operação: \"R\" = Remessa."),
    ("Tipo de Serviço", 10, 11,
     "Tipo de Serviço: \"01\" = Cobrança."),
    ("Uso Reservado (Filler)", 12, 13,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Versão do Layout do Lote", 14, 16,
     "Nº da versão do layout do lote: \"040\"."),
    ("Uso Reservado (Filler)", 17, 17,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Tipo de Inscrição da Empresa", 18, 18,
     "Tipo de inscrição do Beneficiário (Empresa): '1' = CPF; '2' = CNPJ."),
    ("Número de Inscrição da Empresa", 19, 33,
     "CPF/CNPJ do Beneficiário (15 posições), alinhado à direita com zeros à esquerda, sem pontuação."),
    ("Código do Convênio no Banco", 34, 53,
     "Código do Convênio no Banco - preencher com espaços em branco."),
    ("Prefixo da Cooperativa (Agência)", 54, 58,
     "Prefixo da Cooperativa; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador do Prefixo", 59, 59,
     "Dígito verificador do Prefixo; vide planilha \"Contracapa\" do manual."),
    ("Número da Conta Corrente", 60, 71,
     "Número da conta corrente; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Conta", 72, 72,
     "Dígito verificador da conta; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Agência/Conta", 73, 73,
     "Dígito verificador da Agência/Conta - preencher com espaços em branco."),
    ("Nome da Empresa", 74, 103,
     "Nome (razão social) do Beneficiário/Empresa."),
    ("Mensagem 1", 104, 143,
     "Mensagem 1 - preencher com espaços em branco."),
    ("Mensagem 2", 144, 183,
     "Mensagem 2 - preencher com espaços em branco."),
    ("Número Remessa/Retorno", 184, 191,
     "Número adotado e controlado por quem gera o arquivo para identificar a sequência de envio/devolução entre o Beneficiário e o Sicoob. Se não informado, retornará zeros."),
    ("Data de Gravação Remessa/Retorno", 192, 199,
     "Data de gravação da remessa/retorno, formato DDMMAAAA."),
    ("Data do Crédito", 200, 207,
     "Data do Crédito: \"00000000\" na Remessa (formato DDMMAAAA)."),
    ("Uso Reservado (Filler)", 208, 240,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
]


# ---------------------------------------------------------------------------
# 4. Header de Lote (Registro tipo 1) - RETORNO
# ---------------------------------------------------------------------------

HEADER_LOTE_RETORNO_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"1\" (Header de Lote)."),
    ("Tipo de Operação", 9, 9,
     "Tipo de Operação: \"T\" = Retorno."),
    ("Tipo de Serviço", 10, 11,
     "Tipo de Serviço: \"01\" = Cobrança."),
    ("Uso Reservado (Filler)", 12, 13,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
    ("Versão do Layout do Lote", 14, 16,
     "Nº da versão do layout do lote: \"044\"."),
    ("Uso Reservado (Filler)", 17, 17,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
    ("Tipo de Inscrição da Empresa", 18, 18,
     "Tipo de inscrição do Beneficiário (Empresa): '1' = CPF; '2' = CNPJ."),
    ("Número de Inscrição da Empresa", 19, 33,
     "CPF/CNPJ do Beneficiário (15 posições), alinhado à direita com zeros à esquerda, sem pontuação."),
    ("Código do Convênio no Banco", 34, 53,
     "Código do Convênio no Banco - o sistema retorna o código do convênio da cooperativa; se não existir, retorna em branco."),
    ("Prefixo da Cooperativa (Agência)", 54, 58,
     "Prefixo da Cooperativa; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador do Prefixo", 59, 59,
     "Dígito verificador do Prefixo - o sistema retorna preenchido com zero \"0\"."),
    ("Número da Conta Corrente", 60, 71,
     "Número da conta corrente; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Conta", 72, 72,
     "Dígito verificador da conta; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Agência/Conta", 73, 73,
     "Dígito verificador da Agência/Conta - o sistema retorna as posições em branco."),
    ("Nome da Empresa", 74, 103,
     "Nome (razão social) do Beneficiário/Empresa."),
    ("Mensagem 1", 104, 143,
     "Mensagem 1 - estes campos não são utilizados no arquivo de retorno."),
    ("Mensagem 2", 144, 183,
     "Mensagem 2 - estes campos não são utilizados no arquivo de retorno."),
    ("Número Remessa/Retorno", 184, 191,
     "Número adotado e controlado por quem gera o arquivo para identificar a sequência de envio/devolução entre o Beneficiário e o Sicoob."),
    ("Data de Gravação Remessa/Retorno", 192, 199,
     "Data de gravação da remessa/retorno, formato DDMMAAAA."),
    ("Data do Crédito", 200, 207,
     "Data de efetivação do crédito referente ao pagamento do título de cobrança; informada somente no arquivo de retorno, formato DDMMAAAA."),
    ("Uso Reservado (Filler)", 208, 240,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
]


# ---------------------------------------------------------------------------
# 5. Detalhe (Registro tipo 3) - Segmento P - REMESSA (dados do título)
# ---------------------------------------------------------------------------

SEGMENTO_P_REMESSA_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"3\" (Registro Detalhe)."),
    ("Número Sequencial do Registro no Lote", 9, 13,
     "Número adotado para identificar a sequência de registros enviados no lote. '00001' para o primeiro segmento P do lote; nos demais, o número do registro anterior + 1 (ex.: P = 00001, Q = 00002, R = 00003, S = 00004 e assim por diante)."),
    ("Código do Segmento do Registro Detalhe", 14, 14,
     "Código do Segmento: \"P\"."),
    ("Uso Reservado (Filler)", 15, 15,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Código de Movimento Remessa", 16, 17,
     "Instrução enviada pelo Beneficiário: 01 Entrada de Títulos; 02 Solicitação de Baixa; 04 Concessão de Abatimento; 05 Cancelamento de Abatimento; 06 Prorrogação de Vencimento; 09 Protestar; 10 Desistência do Protesto e Baixar Título; 11 Desistência do Protesto e manter em carteira; 12 Alteração de Juros de Mora; 13 Dispensar Cobrança de Juros de Mora; 14 Alteração de Valor/Percentual de Multa; 15 Dispensar Cobrança de Multa; 19 Prazo limite de recebimento - alterar; 20 Prazo limite de recebimento - dispensar; 23 Alterar dados do pagador; 31 Alterações de outros dados. (Tabela completa em MOVIMENTO_REMESSA_CODES.)"),
    ("Prefixo da Cooperativa (Agência)", 18, 22,
     "Prefixo da Cooperativa; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador do Prefixo", 23, 23,
     "Dígito verificador do Prefixo; vide planilha \"Contracapa\" do manual."),
    ("Número da Conta Corrente", 24, 35,
     "Número da conta corrente; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Conta", 36, 36,
     "Dígito verificador da conta; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Agência/Conta", 37, 37,
     "Dígito verificador da Agência/Conta - preencher com espaços em branco."),
    ("Nosso Número", 38, 57,
     "Identificação do título no Sicoob (20 posições). Se a emissão do boleto é a cargo do Sicoob: NumTítulo (1-10) zeros; Parcela (11-12) '01' se parcela única; Modalidade (13-14) conforme planilha \"Contracapa\"; Tipo Formulário (15) '1' auto-copiativo, '3' auto-envelopável, '4' A4 sem envelopamento, '6' A4 sem envelopamento 3 vias; posições 16-20 em branco. Se a emissão é a cargo do Beneficiário: NumTítulo (1-10) conforme item 3.13 da planilha \"02.Especificações do Boleto\"; Parcela, Modalidade e Tipo Formulário idem; posições 16-20 em branco."),
    ("Código da Carteira", 58, 58,
     "Código da Carteira; vide planilha \"Contracapa\" do manual."),
    ("Forma de Cadastramento do Título no Banco", 59, 59,
     "Forma de cadastramento do título no banco: \"0\"."),
    ("Tipo de Documento", 60, 60,
     "Tipo de Documento - preencher com espaços em branco."),
    ("Identificação da Emissão do Boleto", 61, 61,
     "Emissão do boleto: '1' = Sicoob emite; '2' = Beneficiário emite (vide planilha \"Contracapa\")."),
    ("Identificação da Distribuição do Boleto", 62, 62,
     "Distribuição do boleto: '1' = Sicoob distribui; '2' = Beneficiário distribui (vide planilha \"Contracapa\")."),
    ("Número do Documento", 63, 77,
     "Número do Documento de Cobrança (Seu Número): adotado e controlado pelo cliente para identificar o título; referenciado pelo Sicoob para identificar o documento cobrado (nº da duplicata, apólice etc.)."),
    ("Data de Vencimento", 78, 85,
     "Data de vencimento do título, formato DDMMAAAA."),
    ("Valor Nominal do Título", 86, 100,
     "Valor nominal do título, 13 inteiros + 2 decimais, sem separador."),
    ("Agência Encarregada da Cobrança", 101, 105,
     "Agência encarregada da cobrança: \"00000\"."),
    ("Dígito Verificador da Agência Cobradora", 106, 106,
     "Dígito verificador da agência - preencher com espaços em branco."),
    ("Espécie do Título", 107, 108,
     "Espécie do título: 01 CH Cheque; 02 DM Duplicata Mercantil; 03 DMI; 04 DS Duplicata de Serviço; 05 DSI; 06 DR Duplicata Rural; 07 LC; 08 NCC; 09 NCE; 10 NCI; 11 NCR; 12 NP Nota Promissória; 13 NPR; 14 TM; 15 TS; 16 NS; 17 RC Recibo; 18 FAT Fatura; 19 ND Nota de Débito; 20 AP; 21 ME; 22 PC; 23 NF Nota Fiscal; 24 DD; 25 Cédula de Produto Rural; 31 Cartão de Crédito; 32 BDP Boleto de Proposta; 99 Outros. Tabela completa em ESPECIE_TITULO_CODES."),
    ("Identificação de Título Aceito/Não Aceito", 109, 109,
     "Aceite: 'A' = Aceite; 'N' = Não Aceite."),
    ("Data de Emissão do Título", 110, 117,
     "Data de emissão do título, formato DDMMAAAA."),
    ("Código do Encargo por Atraso", 118, 118,
     "Código do Juros de Mora: '0' = Isento; '1' = Valor por Dia; '2' = Taxa Mensal."),
    ("Data Início do Encargo por Atraso", 119, 126,
     "Data indicativa do início da cobrança dos juros de mora, formato DDMMAAAA; deve ser maior que a data de vencimento. Se inválida, igual ao vencimento ou não informada, será considerado o vencimento + 1 dia."),
    ("Valor/Taxa de Juros de Mora", 127, 141,
     "Juros de mora por dia (valor em R$ ao dia) ou taxa ao mês (%), 13 inteiros + 2 decimais. Ex.: 0000000000220 = 2,20%; 0000000001040 = 10,40%."),
    ("Código Desc. 1", 142, 142,
     "Código do Desconto 1: '0' = Não conceder desconto; '1' = Valor fixo até a data informada; '2' = Percentual até a data informada."),
    ("Data Desc. 1", 143, 150,
     "Data do Desconto 1, formato DDMMAAAA."),
    ("Valor/Percentual Desc. 1", 151, 165,
     "Valor ou percentual a ser concedido no Desconto 1, 13 inteiros + 2 decimais."),
    ("Valor do IOF a Ser Recolhido", 166, 180,
     "Valor do IOF a ser recolhido, 13 inteiros + 2 decimais."),
    ("Valor do Abatimento", 181, 195,
     "Valor do abatimento, 13 inteiros + 2 decimais."),
    ("Identificação do Título na Empresa", 196, 220,
     "Uso Empresa Beneficiário: campo livre do Beneficiário para identificação do título."),
    ("Código para Protesto", 221, 221,
     "Código para protesto: '1' = Protestar dias corridos; '3' = Não protestar; '9' = Cancelar instrução de protesto (deve estar atrelado ao código de movimento '31')."),
    ("Prazo para Protesto", 222, 223,
     "Prazo, em dias, de início do protesto a partir do vencimento; '00' = não protestar."),
    ("Código para Baixa/Devolução", 224, 224,
     "Código para baixa/devolução: \"0\"."),
    ("Prazo para Baixa/Devolução", 225, 227,
     "Número de dias para baixa/devolução - preencher com espaços em branco."),
    ("Código da Moeda", 228, 229,
     "Código da moeda: '09' = Real."),
    ("Número do Contrato da Operação de Crédito", 230, 239,
     "Nº do contrato da operação de crédito. Para a modalidade Simples com Registro, preencher \"0000000000\"."),
    ("Uso Reservado (Filler)", 240, 240,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
]


# ---------------------------------------------------------------------------
# 6. Detalhe (Registro tipo 3) - Segmento Q - REMESSA (dados do Pagador/Sacado e Sacador/Avalista)
# ---------------------------------------------------------------------------

SEGMENTO_Q_REMESSA_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"3\" (Registro Detalhe)."),
    ("Número Sequencial do Registro no Lote", 9, 13,
     "Número adotado para identificar a sequência de registros enviados no lote. '00001' para o primeiro segmento P do lote; nos demais, o número do registro anterior + 1 (ex.: P = 00001, Q = 00002, R = 00003, S = 00004 e assim por diante). Ex.: se o segmento P anterior é 00001, o segmento Q é 00002."),
    ("Código do Segmento do Registro Detalhe", 14, 14,
     "Código do Segmento: \"Q\"."),
    ("Uso Reservado (Filler)", 15, 15,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Código de Movimento Remessa", 16, 17,
     "Instrução enviada pelo Beneficiário: 01 Entrada de Títulos; 02 Solicitação de Baixa; 04 Concessão de Abatimento; 05 Cancelamento de Abatimento; 06 Prorrogação de Vencimento; 09 Protestar; 10 Desistência do Protesto e Baixar Título; 11 Desistência do Protesto e manter em carteira; 12 Alteração de Juros de Mora; 13 Dispensar Cobrança de Juros de Mora; 14 Alteração de Valor/Percentual de Multa; 15 Dispensar Cobrança de Multa; 19 Prazo limite de recebimento - alterar; 20 Prazo limite de recebimento - dispensar; 23 Alterar dados do pagador; 31 Alterações de outros dados. (Tabela completa em MOVIMENTO_REMESSA_CODES.)"),
    ("Tipo de Inscrição do Pagador", 18, 18,
     "Tipo de inscrição do Pagador: '1' = CPF; '2' = CNPJ."),
    ("Número de Inscrição do Pagador", 19, 33,
     "CPF/CNPJ do Pagador (15 posições), alinhado à direita com zeros à esquerda."),
    ("Nome do Pagador", 34, 73,
     "Nome do Pagador (Sacado)."),
    ("Endereço do Pagador", 74, 113,
     "Endereço do Pagador."),
    ("Bairro do Pagador", 114, 128,
     "Bairro do Pagador."),
    ("CEP do Pagador", 129, 133,
     "CEP do Pagador (5 primeiros dígitos)."),
    ("Sufixo do CEP do Pagador", 134, 136,
     "Sufixo do CEP (3 últimos dígitos)."),
    ("Cidade do Pagador", 137, 151,
     "Cidade do Pagador."),
    ("UF do Pagador", 152, 153,
     "Unidade da Federação do Pagador."),
    ("Tipo de Inscrição do Sacador/Avalista", 154, 154,
     "Tipo de inscrição do Sacador/Avalista: '0' = Isento/Não informado; '1' = CPF; '2' = CNPJ."),
    ("Número de Inscrição do Sacador/Avalista", 155, 169,
     "CPF/CNPJ do Sacador/Avalista (15 posições)."),
    ("Nome do Sacador/Avalista", 170, 209,
     "Nome do Sacador/Avalista."),
    ("Código do Banco Correspondente na Compensação", 210, 212,
     "Se o Beneficiário não contratou Banco Correspondente com o Sicoob, preencher \"000\"; se contratou e a emissão é a cargo do Sicoob (posição 61 do Segmento P), preencher \"001\" (Banco do Brasil) ou \"237\" (Bradesco)."),
    ("Nosso Nº no Banco Correspondente", 213, 232,
     "Preencher com \"000\" somente quando o campo anterior indicar uso de Banco Correspondente; o preenchimento é alinhado à esquerda a partir da posição 213 até a 219."),
    ("Uso Reservado (Filler)", 233, 240,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
]


# ---------------------------------------------------------------------------
# 7. Detalhe (Registro tipo 3) - Segmento R - REMESSA (descontos 2/3, multa, mensagens 3/4, débito automático)
# ---------------------------------------------------------------------------

SEGMENTO_R_REMESSA_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"3\" (Registro Detalhe)."),
    ("Número Sequencial do Registro no Lote", 9, 13,
     "Número adotado para identificar a sequência de registros enviados no lote. '00001' para o primeiro segmento P do lote; nos demais, o número do registro anterior + 1 (ex.: P = 00001, Q = 00002, R = 00003, S = 00004 e assim por diante). Ex.: se P = 00001 e Q = 00002, o segmento R é 00003."),
    ("Código do Segmento do Registro Detalhe", 14, 14,
     "Código do Segmento: \"R\"."),
    ("Uso Reservado (Filler)", 15, 15,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Código de Movimento Remessa", 16, 17,
     "Instrução enviada pelo Beneficiário: 01 Entrada de Títulos; 02 Solicitação de Baixa; 04 Concessão de Abatimento; 05 Cancelamento de Abatimento; 06 Prorrogação de Vencimento; 09 Protestar; 10 Desistência do Protesto e Baixar Título; 11 Desistência do Protesto e manter em carteira; 12 Alteração de Juros de Mora; 13 Dispensar Cobrança de Juros de Mora; 14 Alteração de Valor/Percentual de Multa; 15 Dispensar Cobrança de Multa; 19 Prazo limite de recebimento - alterar; 20 Prazo limite de recebimento - dispensar; 23 Alterar dados do pagador; 31 Alterações de outros dados. (Tabela completa em MOVIMENTO_REMESSA_CODES.)"),
    ("Código Desc. 2", 18, 18,
     "Código do Desconto 2: '0' = Não conceder desconto; '1' = Valor fixo até a data informada; '2' = Percentual até a data informada."),
    ("Data Desc. 2", 19, 26,
     "Data do Desconto 2, formato DDMMAAAA."),
    ("Valor/Percentual Desc. 2", 27, 41,
     "Valor ou percentual a ser concedido no Desconto 2, 13 inteiros + 2 decimais."),
    ("Código Desc. 3", 42, 42,
     "Código do Desconto 3: '0' = Não conceder desconto; '1' = Valor fixo até a data informada; '2' = Percentual até a data informada."),
    ("Data Desc. 3", 43, 50,
     "Data do Desconto 3, formato DDMMAAAA."),
    ("Valor/Percentual Desc. 3", 51, 65,
     "Valor ou percentual a ser concedido no Desconto 3, 13 inteiros + 2 decimais."),
    ("Código da Multa", 66, 66,
     "Código da Multa: '0' = Isento; '1' = Valor fixo; '2' = Percentual."),
    ("Data da Multa", 67, 74,
     "Data indicativa do início da cobrança da multa, formato DDMMAAAA; deve ser maior que a data de vencimento. Se inválida, igual ao vencimento ou não informada, será considerado o vencimento + 1 dia."),
    ("Valor/Percentual da Multa", 75, 89,
     "Valor ou percentual a ser aplicado, 13 inteiros + 2 decimais. Ex.: 0000000000220 = 2,20%; 0000000001040 = 10,40%."),
    ("Informação ao Pagador", 90, 99,
     "Informação ao Pagador - preencher com espaços em branco."),
    ("Mensagem 3", 100, 139,
     "Mensagem 3 - preencher com espaços em branco."),
    ("Mensagem 4", 140, 179,
     "Mensagem 4 - preencher com espaços em branco."),
    ("Uso Reservado (Filler)", 180, 199,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Data Limite de Pagamento", 200, 207,
     "Data limite de pagamento, formato \"DDMMAAAA\" (usada com os códigos de movimento 19/20 de Prazo limite de recebimento)."),
    ("Código do Banco na Conta do Débito", 208, 210,
     "Código do banco da conta de débito: \"000\"."),
    ("Código da Agência do Débito", 211, 215,
     "Código da agência do débito: \"00000\"."),
    ("Dígito Verificador da Agência do Débito", 216, 216,
     "Dígito verificador da agência - preencher com espaços em branco."),
    ("Conta Corrente para Débito", 217, 228,
     "Conta corrente para débito: \"000000000000\"."),
    ("Dígito Verificador da Conta do Débito", 229, 229,
     "Dígito verificador da conta - preencher com espaços em branco."),
    ("Dígito Verificador da Agência/Conta do Débito", 230, 230,
     "Dígito verificador da Agência/Conta - preencher com espaços em branco."),
    ("Aviso para Débito Automático", 231, 231,
     "Identificação da emissão do aviso de débito automático: \"0\"."),
    ("Uso Reservado (Filler)", 232, 240,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
]


# ---------------------------------------------------------------------------
# 8. Detalhe (Registro tipo 3) - Segmento S - REMESSA (Tipo de Impressão 3: mensagens 5 a 9 do boleto)
# ---------------------------------------------------------------------------

SEGMENTO_S_REMESSA_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"3\" (Registro Detalhe)."),
    ("Número Sequencial do Registro no Lote", 9, 13,
     "Número adotado para identificar a sequência de registros enviados no lote. '00001' para o primeiro segmento P do lote; nos demais, o número do registro anterior + 1 (ex.: P = 00001, Q = 00002, R = 00003, S = 00004 e assim por diante). Ex.: se P = 00001, Q = 00002 e R = 00003, o segmento S é 00004."),
    ("Código do Segmento do Registro Detalhe", 14, 14,
     "Código do Segmento: \"S\"."),
    ("Uso Reservado (Filler)", 15, 15,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Código de Movimento Remessa", 16, 17,
     "Instrução enviada pelo Beneficiário: 01 Entrada de Títulos; 02 Solicitação de Baixa; 04 Concessão de Abatimento; 05 Cancelamento de Abatimento; 06 Prorrogação de Vencimento; 09 Protestar; 10 Desistência do Protesto e Baixar Título; 11 Desistência do Protesto e manter em carteira; 12 Alteração de Juros de Mora; 13 Dispensar Cobrança de Juros de Mora; 14 Alteração de Valor/Percentual de Multa; 15 Dispensar Cobrança de Multa; 19 Prazo limite de recebimento - alterar; 20 Prazo limite de recebimento - dispensar; 23 Alterar dados do pagador; 31 Alterações de outros dados. (Tabela completa em MOVIMENTO_REMESSA_CODES.)"),
    ("Tipo de Impressão", 18, 18,
     "Identificação da impressão: '3' = Corpo de Instruções da Ficha de Compensação do Boleto."),
    ("Mensagem 5", 19, 58,
     "Mensagem 5: texto livre impresso no campo de instruções da ficha de compensação. As mensagens 5 a 9 prevalecem sobre as anteriores."),
    ("Mensagem 6", 59, 98,
     "Mensagem 6: texto livre impresso no campo de instruções da ficha de compensação."),
    ("Mensagem 7", 99, 138,
     "Mensagem 7: texto livre impresso no campo de instruções da ficha de compensação."),
    ("Mensagem 8", 139, 178,
     "Mensagem 8: texto livre impresso no campo de instruções da ficha de compensação."),
    ("Mensagem 9", 179, 218,
     "Mensagem 9: texto livre impresso no campo de instruções da ficha de compensação."),
    ("Uso Reservado (Filler)", 219, 240,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
]


# ---------------------------------------------------------------------------
# 8b. Segmento S - REMESSA - variante Tipo de Impressão 1/2 (frente/verso; NÃO utilizada segundo o manual)
# ---------------------------------------------------------------------------

SEGMENTO_S_REMESSA_TIPO_IMPRESSAO_1_2_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"3\" (Registro Detalhe)."),
    ("Número Sequencial do Registro no Lote", 9, 13,
     "Número adotado para identificar a sequência de registros enviados no lote. '00001' para o primeiro segmento P do lote; nos demais, o número do registro anterior + 1 (ex.: P = 00001, Q = 00002, R = 00003, S = 00004 e assim por diante)."),
    ("Código do Segmento do Registro Detalhe", 14, 14,
     "Código do Segmento: \"S\"."),
    ("Uso Reservado (Filler)", 15, 15,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Código de Movimento Remessa", 16, 17,
     "Instrução enviada pelo Beneficiário: 01 Entrada de Títulos; 02 Solicitação de Baixa; 04 Concessão de Abatimento; 05 Cancelamento de Abatimento; 06 Prorrogação de Vencimento; 09 Protestar; 10 Desistência do Protesto e Baixar Título; 11 Desistência do Protesto e manter em carteira; 12 Alteração de Juros de Mora; 13 Dispensar Cobrança de Juros de Mora; 14 Alteração de Valor/Percentual de Multa; 15 Dispensar Cobrança de Multa; 19 Prazo limite de recebimento - alterar; 20 Prazo limite de recebimento - dispensar; 23 Alterar dados do pagador; 31 Alterações de outros dados. (Tabela completa em MOVIMENTO_REMESSA_CODES.)"),
    ("Tipo de Impressão", 18, 18,
     "Identificação da impressão: '1' = Frente do Boleto; '2' = Verso do Boleto. Segundo o manual, os tipos 1 e 2 não são utilizados."),
    ("Número da Linha a Ser Impressa", 19, 20,
     "Número da linha a ser impressa."),
    ("Mensagem a Ser Impressa", 21, 160,
     "Mensagem a ser impressa - tipos 1 e 2 não são utilizados; preencher com espaços em branco."),
    ("Tipo de Caractere (Fonte) a Ser Impresso", 161, 162,
     "Tipo de caractere a ser impresso."),
    ("Uso Reservado (Filler)", 163, 240,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
]


# ---------------------------------------------------------------------------
# 9. Detalhe (Registro tipo 3) - Segmento T - RETORNO (dados do título e do Pagador)
# ---------------------------------------------------------------------------

SEGMENTO_T_RETORNO_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"3\" (Registro Detalhe)."),
    ("Número Sequencial do Registro no Lote", 9, 13,
     "Número sequencial do registro dentro do lote, iniciado sempre em 1 a cada novo lote."),
    ("Código do Segmento do Registro Detalhe", 14, 14,
     "Código do Segmento: \"T\"."),
    ("Uso Reservado (Filler)", 15, 15,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
    ("Código de Movimento Retorno", 16, 17,
     "Código de Movimento/Ocorrência do Retorno (ex.: 02 Entrada Confirmada; 03 Entrada Rejeitada; 06 Liquidação; 09 Baixa; 17 Liquidação Após Baixa ou Liquidação Título Não Registrado; 26 Instrução Rejeitada; 28 Débito de Tarifas/Custas). Tabela completa em OCORRENCIA_RETORNO_CODES."),
    ("Prefixo da Cooperativa (Agência)", 18, 22,
     "Prefixo da Cooperativa; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador do Prefixo", 23, 23,
     "Dígito verificador do Prefixo; vide planilha \"Contracapa\" do manual."),
    ("Número da Conta Corrente", 24, 35,
     "Número da conta corrente; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Conta", 36, 36,
     "Dígito verificador da conta; vide planilha \"Contracapa\" do manual."),
    ("Dígito Verificador da Agência/Conta", 37, 37,
     "Dígito verificador da Agência/Conta - o sistema retorna as posições em branco."),
    ("Nosso Número", 38, 57,
     "Identificação do título no Sicoob (20 posições). Se a emissão do boleto é a cargo do Sicoob: brancos. Se a cargo do Beneficiário: NumTítulo (1-10); Parcela (11-12) '01' se parcela única; Modalidade (13-14) conforme planilha \"Contracapa\"; Tipo Formulário (15) '1' auto-copiativo, '3' auto-envelopável, '4' A4 sem envelopamento, '6' A4 sem envelopamento 3 vias; posições 16-20 em branco."),
    ("Código da Carteira", 58, 58,
     "Código da Carteira; vide planilha \"Contracapa\" do manual."),
    ("Número do Documento", 59, 73,
     "Número do Documento de Cobrança (Seu Número): adotado e controlado pelo cliente para identificar o título (nº da duplicata, apólice etc.)."),
    ("Data de Vencimento", 74, 81,
     "Data de vencimento do título, formato DDMMAAAA."),
    ("Valor Nominal do Título", 82, 96,
     "Valor nominal do título, 13 inteiros + 2 decimais, sem separador."),
    ("Número do Banco Cobrador/Recebedor", 97, 99,
     "Número do banco cobrador/recebedor - só é informado nos casos de cobrança/liquidação em outros bancos."),
    ("Agência Cobradora/Recebedora", 100, 104,
     "Código adotado pelo banco responsável pela conta para identificar a unidade à qual a conta corrente está vinculada."),
    ("Dígito Verificador da Agência Recebedora", 105, 105,
     "Dígito verificador da agência recebedora."),
    ("Identificação do Título na Empresa", 106, 130,
     "Uso Empresa Beneficiário: campo livre do Beneficiário para identificação do título."),
    ("Código da Moeda", 131, 132,
     "Código da moeda: '02' = Dólar Americano Comercial (Venda); '09' = Real."),
    ("Tipo de Inscrição do Pagador", 133, 133,
     "Tipo de inscrição do Pagador: '1' = CPF; '2' = CNPJ."),
    ("Número de Inscrição do Pagador", 134, 148,
     "CPF/CNPJ do Pagador (15 posições), alinhado à direita com zeros à esquerda."),
    ("Nome do Pagador", 149, 188,
     "Nome do Pagador (Sacado)."),
    ("Número do Contrato da Operação de Crédito", 189, 198,
     "Nº do contrato da operação de crédito, adotado pela empresa beneficiária."),
    ("Valor da Tarifa/Custas", 199, 213,
     "Valor da tarifa/custas cobrada, 13 inteiros + 2 decimais."),
    ("Motivo da Ocorrência", 214, 223,
     "Até cinco códigos de 2 posições (5 x 2) FEBRABAN que identificam as ocorrências (rejeições, tarifas, custas, liquidação e baixas) do título. Tarifas/custas (01 a 20) associadas ao movimento '28'; rejeições (01 a 95) associadas aos movimentos '02', '03', '26' e '30'. Ver MOTIVOS_CODES."),
    ("Uso Reservado (Filler)", 224, 240,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
]


# ---------------------------------------------------------------------------
# 10. Detalhe (Registro tipo 3) - Segmento U - RETORNO (valores pagos/creditados e datas)
# ---------------------------------------------------------------------------

SEGMENTO_U_RETORNO_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"3\" (Registro Detalhe)."),
    ("Número Sequencial do Registro no Lote", 9, 13,
     "Número sequencial do registro dentro do lote, iniciado sempre em 1 a cada novo lote."),
    ("Código do Segmento do Registro Detalhe", 14, 14,
     "Código do Segmento: \"U\"."),
    ("Uso Reservado (Filler)", 15, 15,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
    ("Código de Movimento Retorno", 16, 17,
     "Código de Movimento/Ocorrência do Retorno (ex.: 02 Entrada Confirmada; 03 Entrada Rejeitada; 06 Liquidação; 09 Baixa; 17 Liquidação Após Baixa ou Liquidação Título Não Registrado; 26 Instrução Rejeitada; 28 Débito de Tarifas/Custas). Tabela completa em OCORRENCIA_RETORNO_CODES."),
    ("Valor dos Juros/Multa/Encargos (Acréscimos)", 18, 32,
     "Valor dos acréscimos (juros, multa, encargos) efetuados no título, em moeda corrente, 13 inteiros + 2 decimais."),
    ("Valor do Desconto Concedido", 33, 47,
     "Valor dos descontos efetuados no título, em moeda corrente, 13 inteiros + 2 decimais."),
    ("Valor do Abatimento", 48, 62,
     "Valor dos abatimentos efetuados ou cancelados no título, em moeda corrente, 13 inteiros + 2 decimais."),
    ("Valor do IOF Recolhido", 63, 77,
     "Valor do IOF recolhido sobre o título, em moeda corrente, 13 inteiros + 2 decimais."),
    ("Valor Pago pelo Pagador", 78, 92,
     "Valor do pagamento efetuado pelo Pagador referente ao título, em moeda corrente, 13 inteiros + 2 decimais."),
    ("Valor Líquido a Ser Creditado", 93, 107,
     "Valor efetivo a ser creditado referente ao título, em moeda corrente, 13 inteiros + 2 decimais."),
    ("Valor de Outras Despesas", 108, 122,
     "Valor efetivo de despesas referente ao título de cobrança, em moeda corrente, 13 inteiros + 2 decimais."),
    ("Valor de Outros Créditos", 123, 137,
     "Valor efetivo de créditos referente ao título de cobrança, em moeda corrente, 13 inteiros + 2 decimais."),
    ("Data da Ocorrência", 138, 145,
     "Data do evento que afeta o estado do título de cobrança, formato DDMMAAAA."),
    ("Data do Crédito", 146, 153,
     "Data de efetivação do crédito, formato DDMMAAAA (o manual repete aqui a descrição de 'data do evento que afeta o estado do título')."),
    ("Código da Ocorrência do Pagador", 154, 157,
     "Ocorrência do Pagador: o sistema retorna as posições em branco."),
    ("Data da Ocorrência do Pagador", 158, 165,
     "Data da ocorrência do Pagador: \"00000000\"."),
    ("Valor da Ocorrência do Pagador", 166, 180,
     "Valor da ocorrência do Pagador: \"000000000000000\"."),
    ("Complemento da Ocorrência do Pagador", 181, 210,
     "Complemento da ocorrência do Pagador: o sistema retorna as posições em branco."),
    ("Código do Banco Correspondente", 211, 213,
     "Código do banco correspondente na compensação: '756' se o Beneficiário não contratou Banco Correspondente com o Sicoob; '001' (Banco do Brasil) se contratou."),
    ("Nº do Título no Banco Correspondente", 214, 233,
     "Código fornecido pelo Banco Correspondente para identificação do título de cobrança."),
    ("Uso Reservado (Filler)", 234, 240,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
]


# ---------------------------------------------------------------------------
# 11. Trailer de Lote (Registro tipo 5) - REMESSA
# ---------------------------------------------------------------------------

TRAILER_LOTE_REMESSA_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"5\" (Trailer de Lote)."),
    ("Uso Reservado (Filler)", 9, 17,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
    ("Quantidade de Registros no Lote", 18, 23,
     "Quantidade de registros do lote (inclui Header e Trailer do lote), 6 dígitos."),
    ("Quantidade de Títulos em Cobrança Simples", 24, 29,
     "Cobrança Simples - quantidade de títulos em cobrança."),
    ("Valor Total dos Títulos em Carteira Simples", 30, 46,
     "Cobrança Simples - valor total dos títulos em carteira, 15 inteiros + 2 decimais."),
    ("Quantidade de Títulos em Cobrança Vinculada", 47, 52,
     "Cobrança Vinculada - quantidade de títulos em cobrança."),
    ("Valor Total dos Títulos em Carteira Vinculada", 53, 69,
     "Cobrança Vinculada - valor total dos títulos em carteira, 15 inteiros + 2 decimais."),
    ("Quantidade de Títulos em Cobrança Caucionada", 70, 75,
     "Cobrança Caucionada - quantidade de títulos em cobrança."),
    ("Valor Total dos Títulos em Carteira Caucionada", 76, 92,
     "Cobrança Caucionada - valor total dos títulos em carteira, 15 inteiros + 2 decimais (o manual rotula este campo como 'Quantidade de Títulos em Carteiras', provável erro de digitação; 15 posições com 2 decimais indicam valor)."),
    ("Quantidade de Títulos em Cobrança Descontada", 93, 98,
     "Cobrança Descontada - quantidade de títulos em cobrança."),
    ("Valor Total dos Títulos em Carteira Descontada", 99, 115,
     "Cobrança Descontada - valor total dos títulos em carteira, 15 inteiros + 2 decimais."),
    ("Número do Aviso de Lançamento", 116, 123,
     "Número do aviso de lançamento - preencher com espaços em branco."),
    ("Uso Reservado (Filler)", 124, 240,
     "Uso exclusivo FEBRABAN/CNAB - preencher com espaços em branco."),
]


# ---------------------------------------------------------------------------
# 12. Trailer de Lote (Registro tipo 5) - RETORNO
# ---------------------------------------------------------------------------

TRAILER_LOTE_RETORNO_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Número sequencial que identifica unicamente o lote de serviço, criado e controlado por quem gera o arquivo. '0001' para o primeiro lote do arquivo; nos demais, o número do lote anterior + 1 (não pode repetir dentro do arquivo)."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"5\" (Trailer de Lote)."),
    ("Uso Reservado (Filler)", 9, 17,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
    ("Quantidade de Registros no Lote", 18, 23,
     "Quantidade de registros do lote (inclui Header e Trailer do lote), 6 dígitos."),
    ("Quantidade de Títulos em Cobrança Simples", 24, 29,
     "Cobrança Simples - quantidade de títulos em cobrança."),
    ("Valor Total dos Títulos em Carteira Simples", 30, 46,
     "Cobrança Simples - valor total dos títulos em carteira, 15 inteiros + 2 decimais."),
    ("Quantidade de Títulos em Cobrança Vinculada", 47, 52,
     "Cobrança Vinculada - quantidade de títulos em cobrança."),
    ("Valor Total dos Títulos em Carteira Vinculada", 53, 69,
     "Cobrança Vinculada - valor total dos títulos em carteira, 15 inteiros + 2 decimais."),
    ("Quantidade de Títulos em Cobrança Caucionada", 70, 75,
     "Cobrança Caucionada - quantidade de títulos em cobrança."),
    ("Valor Total dos Títulos em Carteira Caucionada", 76, 92,
     "Cobrança Caucionada - valor total dos títulos em carteira, 15 inteiros + 2 decimais (o manual rotula este campo como 'Quantidade de Títulos em Carteiras', provável erro de digitação; 15 posições com 2 decimais indicam valor)."),
    ("Quantidade de Títulos em Cobrança Descontada", 93, 98,
     "Cobrança Descontada - quantidade de títulos em cobrança."),
    ("Valor Total dos Títulos em Carteira Descontada", 99, 115,
     "Cobrança Descontada - valor total dos títulos em carteira, 15 inteiros + 2 decimais."),
    ("Número do Aviso de Lançamento", 116, 123,
     "Número do aviso de lançamento - o sistema retorna as posições em branco."),
    ("Uso Reservado (Filler)", 124, 240,
     "Uso exclusivo FEBRABAN/CNAB - o Sicoob retorna estas posições em branco."),
]


# ---------------------------------------------------------------------------
# 13. Trailer de Arquivo (Registro tipo 9) - REMESSA e RETORNO (mesmo layout)
# ---------------------------------------------------------------------------

TRAILER_ARQUIVO_FIELDS = [
    ("Código do Banco na Compensação", 1, 3,
     "Código do Sicoob (Bancoob) na Câmara de Compensação. Sempre \"756\"."),
    ("Lote de Serviço", 4, 7,
     "Lote de Serviço do Trailer de Arquivo: sempre \"9999\"."),
    ("Tipo de Registro", 8, 8,
     "Tipo de Registro: \"9\" (Trailer de Arquivo)."),
    ("Uso Reservado (Filler)", 9, 17,
     "Uso exclusivo FEBRABAN/CNAB - em branco (na Remessa preencher com espaços; no Retorno o sistema retorna em branco)."),
    ("Quantidade de Lotes do Arquivo", 18, 23,
     "Quantidade de lotes do arquivo."),
    ("Quantidade de Registros do Arquivo", 24, 29,
     "Quantidade total de registros (linhas) do arquivo, incluindo Header e Trailer de Arquivo."),
    ("Quantidade de Contas para Conciliação (Lotes)", 30, 35,
     "Qtde de contas para conciliação (lotes): \"000000\"."),
    ("Uso Reservado (Filler)", 36, 240,
     "Uso exclusivo FEBRABAN/CNAB - em branco (na Remessa preencher com espaços; no Retorno o sistema retorna em branco)."),
]


# ---------------------------------------------------------------------------
# Mapeamento (tipo de arquivo, letra do segmento) -> lista de campos
# ---------------------------------------------------------------------------

SEGMENTOS = {
    ("Remessa", "P"): SEGMENTO_P_REMESSA_FIELDS,
    ("Remessa", "Q"): SEGMENTO_Q_REMESSA_FIELDS,
    ("Remessa", "R"): SEGMENTO_R_REMESSA_FIELDS,
    ("Remessa", "S"): SEGMENTO_S_REMESSA_FIELDS,
    ("Retorno", "T"): SEGMENTO_T_RETORNO_FIELDS,
    ("Retorno", "U"): SEGMENTO_U_RETORNO_FIELDS,
}

# Registros que não são Detalhe, indexados por (tipo de arquivo, tipo de registro
# da posição 8).
REGISTROS = {
    ("Remessa", "0"): HEADER_ARQUIVO_REMESSA_FIELDS,
    ("Retorno", "0"): HEADER_ARQUIVO_RETORNO_FIELDS,
    ("Remessa", "1"): HEADER_LOTE_REMESSA_FIELDS,
    ("Retorno", "1"): HEADER_LOTE_RETORNO_FIELDS,
    ("Remessa", "5"): TRAILER_LOTE_REMESSA_FIELDS,
    ("Retorno", "5"): TRAILER_LOTE_RETORNO_FIELDS,
    ("Remessa", "9"): TRAILER_ARQUIVO_FIELDS,
    ("Retorno", "9"): TRAILER_ARQUIVO_FIELDS,
}


# ---------------------------------------------------------------------------
# Tabelas de códigos
# ---------------------------------------------------------------------------

# Código de Movimento Remessa (posições 16-17 dos Segmentos P/Q/R/S).
MOVIMENTO_REMESSA_CODES = {
    "01": "Entrada de Títulos",
    "02": "Solicitação de Baixa",
    "04": "Concessão de Abatimento",
    "05": "Cancelamento de Abatimento",
    "06": "Prorrogação de Vencimento",
    "09": "Protestar",
    "10": "Desistência do Protesto e Baixar Título",
    "11": "Desistência do Protesto e manter em carteira",
    "12": "Alteração de Juros de Mora",
    "13": "Dispensar Cobrança de Juros de Mora",
    "14": "Alteração de Valor/Percentual de Multa",
    "15": "Dispensar Cobrança de Multa",
    "19": "Prazo limite de recebimento - alterar",
    "20": "Prazo limite de recebimento - dispensar",
    "23": "Alterar dados do pagador",
    "31": "Alterações de outros dados",
}

# Código de Movimento/Ocorrência Retorno (posições 16-17 dos Segmentos T/U).
OCORRENCIA_RETORNO_CODES = {
    "02": "Entrada Confirmada",
    "03": "Entrada Rejeitada",
    "04": "Transferência de Carteira/Entrada",
    "05": "Transferência de Carteira/Baixa",
    "06": "Liquidação",
    "07": "Confirmação do Recebimento da Instrução de Desconto",
    "08": "Confirmação do Recebimento do Cancelamento do Desconto",
    "09": "Baixa",
    "11": "Títulos em Carteira (Em Ser)",
    "12": "Confirmação Recebimento Instrução de Abatimento",
    "13": "Confirmação Recebimento Instrução de Cancelamento Abatimento",
    "14": "Confirmação Recebimento Instrução Alteração de Vencimento",
    "15": "Franco de Pagamento",
    "17": "Liquidação Após Baixa ou Liquidação Título Não Registrado",
    "19": "Confirmação Recebimento Instrução de Protesto",
    "20": "Confirmação Recebimento Instrução de Sustação/Cancelamento de Protesto",
    "23": "Remessa a Cartório (Aponte em Cartório)",
    "24": "Retirada de Cartório e Manutenção em Carteira",
    "25": "Protestado e Baixado (Baixa por Ter Sido Protestado)",
    "26": "Instrução Rejeitada",
    "27": "Confirmação do Pedido de Alteração de Outros Dados",
    "28": "Débito de Tarifas/Custas",
    "29": "Ocorrências do Pagador",
    "30": "Alteração de Dados Rejeitada",
    "33": "Confirmação da Alteração dos Dados do Rateio de Crédito",
    "34": "Confirmação do Cancelamento dos Dados do Rateio de Crédito",
    "35": "Confirmação do Desagendamento do Débito Automático",
    "36": "Confirmação de envio de e-mail/SMS",
    "37": "Envio de e-mail/SMS rejeitado",
    "38": "Confirmação de alteração do Prazo Limite de Recebimento",
    "39": "Confirmação de Dispensa de Prazo Limite de Recebimento",
    "40": "Confirmação da alteração do número do título dado pelo Beneficiário",
    "41": "Confirmação da alteração do número controle do Participante",
    "42": "Confirmação da alteração dos dados do Pagador",
    "43": "Confirmação da alteração dos dados do Sacador/Avalista",
    "44": "Título pago com cheque devolvido",
    "45": "Título pago com cheque compensado",
    "46": "Instrução para cancelar protesto confirmada",
    "47": "Instrução para protesto para fins falimentares confirmada",
    "48": "Confirmação de instrução de transferência de carteira/modalidade de cobrança",
    "49": "Alteração de contrato de cobrança",
    "50": "Título pago com cheque pendente de liquidação",
    "51": "Título DDA reconhecido pelo Pagador",
    "52": "Título DDA não reconhecido pelo Pagador",
    "53": "Título DDA recusado pela CIP",
    "54": "Confirmação da Instrução de Baixa de Título Negativado sem Protesto",
    "55": "Confirmação de Pedido de Dispensa de Multa",
    "56": "Confirmação do Pedido de Cobrança de Multa",
    "57": "Confirmação do Pedido de Alteração de Cobrança de Juros",
    "58": "Confirmação do Pedido de Alteração do Valor/Data de Desconto",
    "59": "Confirmação do Pedido de Alteração do Beneficiário do Título",
    "60": "Confirmação do Pedido de Dispensa de Juros de Mora",
    "85": "Confirmação de Desistência de Protesto",
    "86": "Confirmação de cancelamento do Protesto",
}

# Espécie do Título (Segmento P, posições 107-108).
ESPECIE_TITULO_CODES = {
    "01": "CH - Cheque",
    "02": "DM - Duplicata Mercantil",
    "03": "DMI - Duplicata Mercantil p/ Indicação",
    "04": "DS - Duplicata de Serviço",
    "05": "DSI - Duplicata de Serviço p/ Indicação",
    "06": "DR - Duplicata Rural",
    "07": "LC - Letra de Câmbio",
    "08": "NCC - Nota de Crédito Comercial",
    "09": "NCE - Nota de Crédito a Exportação",
    "10": "NCI - Nota de Crédito Industrial",
    "11": "NCR - Nota de Crédito Rural",
    "12": "NP - Nota Promissória",
    "13": "NPR - Nota Promissória Rural",
    "14": "TM - Triplicata Mercantil",
    "15": "TS - Triplicata de Serviço",
    "16": "NS - Nota de Seguro",
    "17": "RC - Recibo",
    "18": "FAT - Fatura",
    "19": "ND - Nota de Débito",
    "20": "AP - Apólice de Seguro",
    "21": "ME - Mensalidade Escolar",
    "22": "PC - Parcela de Consórcio",
    "23": "NF - Nota Fiscal",
    "24": "DD - Documento de Dívida",
    "25": "Cédula de Produto Rural",
    "31": "Cartão de Crédito",
    "32": "BDP - Boleto de Proposta",
    "99": "Outros",
}

# Motivos da Ocorrência (Segmento T, posições 214-223; até 5 códigos de 2 posições).
# ATENÇÃO: a planilha oficial do Sicoob só cita alguns códigos como exemplo; estas
# tabelas completas (padrão FEBRABAN, códigos alfanuméricos A1-A9/B1-B5 incluídos)
# vêm do ACBr - fonte secundária. O mesmo código de 2 posições tem significado
# diferente conforme o grupo (ver MOTIVOS_POR_MOVIMENTO / descricao_motivo()).
# Nota: na planilha oficial o código '11' aparece citado como 'Forma de Cadastramento
# do Título Inválido' entre os de tarifas, mas essa descrição pertence à tabela de
# rejeições; para tarifas usa-se '11' = Custas de Edital (FEBRABAN).
MOTIVOS_CODES = {
    # Rejeições - movimentos 02, 03, 26 e 30
    "rejeicao": {
        "00": "Outros Motivos",
        "01": "Código do Banco Inválido",
        "02": "Código do Registro Detalhe Inválido",
        "03": "Código do Segmento Inválido",
        "04": "Código de Movimento Não Permitido para Carteira",
        "05": "Código de Movimento Inválido",
        "06": "Tipo/Número de Inscrição do Beneficiário Inválidos",
        "07": "Agência/Conta/DV Inválido",
        "08": "Nosso Número Inválido",
        "09": "Nosso Número Duplicado",
        "10": "Carteira Inválida",
        "11": "Forma de Cadastramento do Título Inválido",
        "12": "Tipo de Documento Inválido",
        "13": "Identificação da Emissão do Boleto de Pagamento Inválida",
        "14": "Identificação da Distribuição do Boleto de Pagamento Inválida",
        "15": "Características da Cobrança Incompatíveis",
        "16": "Data de Vencimento Inválida",
        "17": "Data de Vencimento Anterior a Data de Emissão",
        "18": "Vencimento Fora do Prazo de Operação",
        "19": "Título a Cargo de Bancos Correspondentes com Vencimento Inferior a XX Dias",
        "20": "Valor do Título Inválido",
        "21": "Espécie do Título Inválida",
        "22": "Espécie do Título Não Permitida para a Carteira",
        "23": "Aceite Inválido",
        "24": "Data da Emissão Inválida",
        "25": "Data da Emissão Posterior a Data de Entrada",
        "26": "Código de Juros de Mora Inválido",
        "27": "Valor/Taxa de Juros de Mora Inválido",
        "28": "Código do Desconto Inválido",
        "29": "Valor do Desconto Maior ou Igual ao Valor do Título",
        "30": "Desconto a Conceder Não Confere",
        "31": "Concessão de Desconto - Já Existe Desconto Anterior",
        "32": "Valor do IOF Inválido",
        "33": "Valor do Abatimento Inválido",
        "34": "Valor do Abatimento Maior ou Igual ao Valor do Título",
        "35": "Valor a Conceder Não Confere",
        "36": "Concessão de Abatimento - Já Existe Abatimento Anterior",
        "37": "Código para Protesto Inválido",
        "38": "Prazo para Protesto Inválido",
        "39": "Pedido de Protesto Não Permitido para o Título",
        "40": "Título com Ordem de Protesto Emitida",
        "41": "Pedido de Cancelamento/Sustação para Títulos sem Instrução de Protesto",
        "42": "Código para Baixa/Devolução Inválido",
        "43": "Prazo para Baixa/Devolução Inválido",
        "44": "Código da Moeda Inválido",
        "45": "Nome do Pagador Não Informado",
        "46": "Tipo/Número de Inscrição do Pagador Inválidos",
        "47": "Endereço do Pagador Não Informado",
        "48": "CEP Inválido",
        "49": "CEP Sem Praça de Cobrança (Não Localizado)",
        "50": "CEP Referente a um Banco Correspondente",
        "51": "CEP incompatível com a Unidade da Federação",
        "52": "Unidade da Federação Inválida",
        "53": "Tipo/Número de Inscrição do Sacador/Avalista Inválidos",
        "54": "Sacador/Avalista Não Informado",
        "55": "Nosso número no Banco Correspondente Não Informado",
        "56": "Código do Banco Correspondente Não Informado",
        "57": "Código da Multa Inválido",
        "58": "Data da Multa Inválida",
        "59": "Valor/Percentual da Multa Inválido",
        "60": "Movimento para Título Não Cadastrado",
        "61": "Alteração da Agência Cobradora/DV Inválida",
        "62": "Tipo de Impressão Inválido",
        "63": "Entrada para Título já Cadastrado",
        "64": "Número da Linha Inválido",
        "65": "Código do Banco para Débito Inválido",
        "66": "Agência/Conta/DV para Débito Inválido",
        "67": "Dados para Débito incompatível com a Identificação da Emissão do Boleto de Pagamento",
        "68": "Débito Automático Agendado",
        "69": "Débito Não Agendado - Erro nos Dados da Remessa",
        "70": "Débito Não Agendado - Pagador Não Consta do Cadastro de Autorizante",
        "71": "Débito Não Agendado - Beneficiário Não Autorizado pelo Pagador",
        "72": "Débito Não Agendado - Beneficiário Não Participa da Modalidade Débito Automático",
        "73": "Débito Não Agendado - Código de Moeda Diferente de Real (R$)",
        "74": "Débito Não Agendado - Data Vencimento Inválida",
        "75": "Débito Não Agendado, Conforme seu Pedido, Título Não Registrado",
        "76": "Débito Não Agendado, Tipo/Num. Inscrição do Debitado, Inválido",
        "77": "Transferência para Desconto Não Permitida para a Carteira do Título",
        "78": "Data Inferior ou Igual ao Vencimento para Débito Automático",
        "79": "Data Juros de Mora Inválido",
        "80": "Data do Desconto Inválida",
        "81": "Tentativas de Débito Esgotadas - Baixado",
        "82": "Tentativas de Débito Esgotadas - Pendente",
        "83": "Limite Excedido",
        "84": "Número Autorização Inexistente",
        "85": "Título com Pagamento Vinculado",
        "86": "Seu Número Inválido",
        "87": "e-mail/SMS enviado",
        "88": "e-mail Lido",
        "89": "e-mail/SMS devolvido - endereço de e-mail ou número do celular incorreto",
        "90": "e-mail devolvido - caixa postal cheia",
        "91": "e-mail/número do celular do Pagador não informado",
        "92": "Pagador optante por Boleto de Pagamento Eletrônico - e-mail não enviado",
        "93": "Código para emissão de Boleto de Pagamento não permite envio de e-mail",
        "94": "Código da Carteira inválido para envio e-mail.",
        "95": "Contrato não permite o envio de e-mail",
        "96": "Número de contrato inválido",
        "97": "Rejeição da alteração do prazo limite de recebimento (a data deve ser informada no campo 28.3.p)",
        "98": "Rejeição de dispensa de prazo limite de recebimento",
        "99": "Rejeição da alteração do número do título dado pelo Beneficiário",
        "A1": "Rejeição da alteração do número controle do participante",
        "A2": "Rejeição da alteração dos dados do Pagador",
        "A3": "Rejeição da alteração dos dados do Sacador/avalista",
        "A4": "Pagador DDA",
        "A5": "Registro Rejeitado - Título já Liquidado",
        "A6": "Código do Convenente Inválido ou Encerrado",
        "A7": "Título já se encontra na situação Pretendida",
        "A8": "Valor do Abatimento inválido para cancelamento",
        "A9": "Não autoriza pagamento parcial",
        "B1": "Autoriza recebimento parcial",
        "B2": "Valor Nominal do Título Conflitante",
        "B3": "Tipo de Pagamento Inválido",
        "B4": "Valor Máximo/Percentual Inválido",
        "B5": "Valor Mínimo/Percentual Inválido",
    },
    # Tarifas/Custas - movimento 28
    "tarifas": {
        "01": "Tarifa de Extrato de Posição",
        "02": "Tarifa de Manutenção de Título Vencido",
        "03": "Tarifa de Sustação",
        "04": "Tarifa de Protesto",
        "05": "Tarifa de Outras Instruções",
        "06": "Tarifa de Outras Ocorrências",
        "07": "Tarifa de Envio de Duplicata ao Pagador",
        "08": "Custas de Protesto",
        "09": "Custas de Sustação de Protesto",
        "10": "Custas de Cartório Distribuidor",
        "11": "Custas de Edital",
        "12": "Tarifa Sobre Devolução de Título Vencido",
        "13": "Tarifa Sobre Registro Cobrada na Baixa/Liquidação",
        "14": "Tarifa Sobre Reapresentação Automática",
        "15": "Tarifa Sobre Rateio de Crédito",
        "16": "Tarifa Sobre Informações Via Fax",
        "17": "Tarifa Sobre Prorrogação de Vencimento",
        "18": "Tarifa Sobre Alteração de Abatimento/Desconto",
        "19": "Tarifa Sobre Arquivo mensal (Em Ser)",
        "20": "Tarifa Sobre Emissão de Boleto de Pagamento Pré-Emitido pelo Banco",
        "21": "Tarifa de Gravação Eletrônica (CRA)",
    },
    # Liquidação/Baixa - movimentos 04, 06, 09 e 17
    "liquidacao_baixa": {
        "01": "Por Saldo",
        "02": "Por Conta",
        "03": "Liquidação no Guichê de Caixa em Dinheiro",
        "04": "Compensação Eletrônica",
        "05": "Compensação Convencional",
        "06": "Por Meio Eletrônico",
        "07": "Após Feriado Local",
        "08": "Em Cartório",
        "09": "Comandada Banco",
        "10": "Comandada Cliente Arquivo",
        "11": "Comandada Cliente On-line",
        "12": "Decurso Prazo - Cliente",
        "13": "Decurso Prazo - Banco",
        "14": "Protestado",
        "15": "Título Excluído",
        "30": "Liquidação no Guichê de Caixa em Cheque",
        "31": "Liquidação em banco correspondente",
        "32": "Liquidação Terminal de Auto-Atendimento",
        "33": "Liquidação na Internet (Home banking)",
        "34": "Liquidado Office Banking",
        "35": "Liquidado Correspondente em Dinheiro",
        "36": "Liquidado Correspondente em Cheque",
        "37": "Liquidado por meio de Central de Atendimento (Telefone)",
    },
}


# Agrupamento dos Motivos da Ocorrência (Segmento T, posições 214-223) conforme o
# Código de Movimento Retorno (posições 16-17). Os movimentos 02 (Entrada Confirmada),
# 03, 26 e 30 usam a tabela de rejeições; 28 usa a de tarifas/custas; 06, 09, 17 e
# demais baixas/liquidações usam a de liquidação/baixa.
MOTIVOS_POR_MOVIMENTO = {
    "02": "rejeicao", "03": "rejeicao", "26": "rejeicao", "30": "rejeicao",
    "28": "tarifas",
    "04": "liquidacao_baixa", "06": "liquidacao_baixa", "09": "liquidacao_baixa",
    "17": "liquidacao_baixa",
}


def split_motivos(valor):
    """Divide o campo Motivo da Ocorrência (10 posições) em até 5 códigos de 2
    posições, descartando os '00'/brancos."""
    valor = (valor or "").ljust(10)[:10]
    codigos = [valor[i:i + 2].strip() for i in range(0, 10, 2)]
    return [c for c in codigos if c and c != "00"]


def descricao_motivo(codigo_movimento, motivo):
    """Descrição de um código de 2 posições do Motivo da Ocorrência, conforme o
    Código de Movimento Retorno. Retorna '' se o grupo ou código for desconhecido."""
    grupo = MOTIVOS_POR_MOVIMENTO.get((codigo_movimento or "").strip())
    if grupo is None:
        return ""
    return MOTIVOS_CODES[grupo].get((motivo or "").strip().upper(), "")



if __name__ == "__main__":
    _ALL = [
        ("HEADER_ARQUIVO_REMESSA_FIELDS", HEADER_ARQUIVO_REMESSA_FIELDS),
        ("HEADER_ARQUIVO_RETORNO_FIELDS", HEADER_ARQUIVO_RETORNO_FIELDS),
        ("HEADER_LOTE_REMESSA_FIELDS", HEADER_LOTE_REMESSA_FIELDS),
        ("HEADER_LOTE_RETORNO_FIELDS", HEADER_LOTE_RETORNO_FIELDS),
        ("SEGMENTO_P_REMESSA_FIELDS", SEGMENTO_P_REMESSA_FIELDS),
        ("SEGMENTO_Q_REMESSA_FIELDS", SEGMENTO_Q_REMESSA_FIELDS),
        ("SEGMENTO_R_REMESSA_FIELDS", SEGMENTO_R_REMESSA_FIELDS),
        ("SEGMENTO_S_REMESSA_FIELDS", SEGMENTO_S_REMESSA_FIELDS),
        ("SEGMENTO_S_REMESSA_TIPO_IMPRESSAO_1_2_FIELDS", SEGMENTO_S_REMESSA_TIPO_IMPRESSAO_1_2_FIELDS),
        ("SEGMENTO_T_RETORNO_FIELDS", SEGMENTO_T_RETORNO_FIELDS),
        ("SEGMENTO_U_RETORNO_FIELDS", SEGMENTO_U_RETORNO_FIELDS),
        ("TRAILER_LOTE_REMESSA_FIELDS", TRAILER_LOTE_REMESSA_FIELDS),
        ("TRAILER_LOTE_RETORNO_FIELDS", TRAILER_LOTE_RETORNO_FIELDS),
        ("TRAILER_ARQUIVO_FIELDS", TRAILER_ARQUIVO_FIELDS),
    ]
    for _name, _fields in _ALL:
        _validate_contiguous(_fields, _name)
        print(f"OK  {_name:<48} {len(_fields):>3} campos, posições 1-{_fields[-1][2]}")
    for _key, _fields in SEGMENTOS.items():
        assert any(f[0] == "Código de Movimento Remessa" or f[0] == "Código de Movimento Retorno"
                   for f in _fields), _key
    for _name, _d in (("MOVIMENTO_REMESSA_CODES", MOVIMENTO_REMESSA_CODES),
                      ("OCORRENCIA_RETORNO_CODES", OCORRENCIA_RETORNO_CODES),
                      ("ESPECIE_TITULO_CODES", ESPECIE_TITULO_CODES)):
        print(f"OK  {_name:<48} {len(_d):>3} códigos")
    for _g, _d in MOTIVOS_CODES.items():
        print(f"OK  MOTIVOS_CODES[{_g!r}]".ljust(52) + f" {len(_d):>3} códigos")
    print("Todas as validações passaram.")
