# -*- coding: utf-8 -*-
"""
CNAB400 Sicoob (Bancoob, banco 756) - field layout reference data.

O Sicoob NÃO usa o layout "genérico" de cobrança CNAB400 (o mesmo que
Itaú/BB/Bradesco/Caixa etc. compartilham, representado em `cnab400_layout.py`).
Ele define seu próprio conjunto de campos/posições para Header, Detalhe e
Trailer, tanto na Remessa quanto no Retorno - por isso este módulo existe
separadamente (mesmo caso do Sicredi).

Fonte usada (acessada 2026-09-21):
  Sicoob - "Layout_Cobranca_CNAB400.xls" (planilhas "03.Remessa - CNAB400" e
  "04.Retorno - CNAB400"), arquivo oficial publicado pelo Sicoob em
  https://www.sicoob.com.br/documents/20128/263767178/Layout_Cobranca_CNAB400.xls/675009c2-3ed6-3156-ea46-54cf78088652?version=1.0&t=1747656841831&download=true
  (versão 1.0 do documento no portal; publicado em 19/05/2025; metadado do
  arquivo: última gravação 05/05/2025). A planilha oficial NÃO traz número de
  versão/revisão próprio - a "versão" aqui é a publicada no portal em
  2025-05. O arquivo foi baixado e lido integralmente (todas as posições
  abaixo vêm da coluna INICIO/FINAL/TAM da planilha).
  -> Fonte primária para HEADER_REMESSA_FIELDS, DETAIL_REMESSA_FIELDS,
     TRAILER_REMESSA_FIELDS, HEADER_RETORNO_FIELDS, DETAIL_RETORNO_FIELDS,
     TRAILER_RETORNO_FIELDS, OCORRENCIA_CODES, COMANDO_REMESSA_CODES,
     ESPECIE_TITULO_CODES, INSTRUCAO_CODES e CARTEIRA_MODALIDADE_CODES.

Conferência cruzada (fontes secundárias):
  - kivanio/brcobranca (Ruby): `lib/brcobranca/remessa/cnab400/sicoob.rb` e a
    planilha oficial `docs/Sicoob/LEIAUTE COBRANCA SICOOB SISTEMAS DE TERCEIRO.XLSX`
    (cópia da mesma planilha; as abas 03/04 são idênticas às oficiais atuais,
    exceto por redação das instruções "PROTESTAR N DIAS [UTEIS] APOS VENCIMENTO").
  - eduardokum/laravel-boleto (PHP): `src/Cnab/Remessa/Cnab400/Banco/Bancoob.php`
    e `src/Cnab/Retorno/Cnab400/Banco/Bancoob.php`.
  Header/Detalhe/Trailer de Remessa e as posições do Retorno usadas por
  eduardokum (nosso número 63-73, seu número 117-126, vencimento 147-152, valor
  153-165, crédito 176-181, tarifa 182-188, abatimento 228-240, desconto
  241-253, pago 254-266, mora 267-279, multa/outros 280-292) conferem com a
  planilha oficial.

Notas sobre o layout do Sicoob:
  - Todas as datas do Header/Detalhe são DDMMAA (6 dígitos). A única exceção
    é a "Data do Movimento" do Trailer de Retorno (posições 156-163), que é
    DDMMAAAA (8 dígitos).
  - O arquivo de Remessa deve ser gerado no padrão Windows (CR+LF) e
    codificação ANSI (nota da planilha oficial).
  - O Sicoob NÃO tem, no CNAB400, registros adicionais (tipo 2 mensagem, 3
    rateio, 5 etc.): o Detalhe tipo 1 é o único registro de título. Mensagens
    de boleto vão em campos do próprio Detalhe (posições 352-391) ou nas
    linhas do Trailer de Remessa (195-394, ver INSTRUCAO_CODES). Extensão NÃO
    oficial: eduardokum acrescenta a chave da NF-e nas posições 401-444 do
    Detalhe (fora das 400 posições e fora do manual); ignorada aqui.
  - O Trailer é DIFERENTE entre Remessa e Retorno (na Remessa é quase todo
    branco + até 5 linhas de mensagem; no Retorno traz dados da cooperativa,
    data do movimento, quantidade de registros e último nosso número). Por
    isso existem TRAILER_REMESSA_FIELDS e TRAILER_RETORNO_FIELDS.
    `TRAILER_FIELDS` é um alias de TRAILER_RETORNO_FIELDS (compatibilidade com
    o módulo Sicredi, que tem um único trailer).
  - Convenção de nomes: campos percentuais têm nomes SEM as palavras
    "Valor/Juros/Mora/Desconto/IOF" ("Taxa Mensal por Atraso", "Taxa de Desc.
    (%)", "Taxa de I.O.F. (%)") para que o app não os formate como moeda; por
    o mesmo motivo o campo "Grupo de Valor" do manual aparece como "Grupo do
    Título" e o "Indicativo valor" como "Indicativo do Ajuste".
  - "Nosso Número": no Detalhe de Remessa (12 posições, 63-74) e de Retorno
    (63-74) o campo é sequencial de 11 dígitos + 1 dígito verificador (módulo
    11 - a planilha oficial descreve 063-073 sequencial e 074 DV na Remessa e
    lista o DV como campo separado no Retorno). Aqui ele aparece quebrado em
    "Nosso Número [Sequencial]" (63-73) e "Nosso Número [DV]" (74) nas duas
    listas. Para comando 01 com emissão a cargo do Sicoob (Tipo de Emissão =
    1) o campo vai todo zerado na Remessa e o banco devolve o número gerado.
  - O Retorno NÃO traz o nome do pagador; traz apenas o CPF/CNPJ do Pagador
    (343-356). Por isso não há campo "Nome do Pagador" em DETAIL_RETORNO_FIELDS.
  - O manual oficial CNAB400 do Sicoob NÃO traz tabela de motivos de
    rejeição: o único campo relacionado é "Código de Baixa/Recusa" (81-82 do
    Retorno), sem tabela no documento. Tabelas de "motivos" encontradas em
    outras fontes (eduardokum, posições 319-328) são do layout ANTIGO
    (Correspondente Bradesco) e conflitam com o layout atual (319-332 hoje é
    Indicativo Débito/Crédito, Indicativo do Ajuste e Valor do Ajuste); por
    isso MOTIVOS_CODES fica vazio.

Anomalias/decisões de transcrição em relação à planilha oficial:
  - Detalhe de Remessa, SEQ 53: a planilha diz INICIO=394, FINAL=395, TAM=1,
    o que se sobrepõe ao Sequencial (395-400). Tratado como 394-394 (TAM 1;
    confirmado por brcobranca e eduardokum).
  - Detalhe de Remessa, SEQ 41 (193-205): a planilha descreve um único campo
    "9(13)" com dois subcampos (193 = código da moeda; 194-205 = IOF/quantidade
    monetária); aqui aparece dividido nesses dois subcampos.
  - Detalhe de Remessa, SEQ 43 (219-220): máscara diz 9(01) mas TAM é 2 e
    valores são "01"/"02"; usado 2 posições.
  - Detalhe de Retorno, SEQ 50/51: a planilha grafa CPF/CNPJ do Pagador em
    343-357 (TAM 14, máscara 9(14)) e o Filler seguinte em 358-394 (TAM 38,
    máscara X(38)). As posições são inconsistentes com TAM/máscara (343-357 =
    15; 358-394 = 37), e 333-394 tem 62 posições = 10 + 14 + 38. Adotado
    343-356 (14) e 357-394 (38), seguindo TAM/máscara. BAIXA CONFIANÇA quanto
    ao deslocamento de 1 posição; confirmar com um arquivo de retorno real.
  - Detalhe de Retorno, SEQ 30 (166-168): o texto da planilha ("Informado o
    prefixo de agência do banco recebedor") repete o do SEQ 31; o campo é o
    código do banco recebedor (3 dígitos).
"""

# ---------------------------------------------------------------------------
# 1. Header (Registro tipo 0) - Arquivo de REMESSA (empresa -> Sicoob)
# ---------------------------------------------------------------------------

HEADER_REMESSA_FIELDS = [
    ("Identificação do Registro (0 = Header)", 1, 1,
     "Marca o início do arquivo. Deve ser sempre o caractere '0'."),
    ("Tipo de Operação (1 = Remessa)", 2, 2,
     "Indica que este é um arquivo de Remessa (a empresa envia títulos ao Sicoob). Deve ser sempre '1'."),
    ("Identificação por Extenso do Tipo de Operação (\"REMESSA\")", 3, 9,
     "Texto fixo 'REMESSA'."),
    ("Identificação do Tipo de Serviço (01)", 10, 11,
     "Código do serviço do arquivo; para cobrança é sempre '01'."),
    ("Identificação por Extenso do Tipo de Serviço (\"COBRANÇA\")", 12, 19,
     "Texto fixo 'COBRANÇA' (8 posições)."),
    ("Uso Reservado (Filler)", 20, 26,
     "Complemento do registro - preencher com espaços em branco."),
    ("Prefixo da Cooperativa", 27, 30,
     "Prefixo (código) da cooperativa Sicoob onde o beneficiário tem o convênio de cobrança, 4 dígitos (planilha 'Contracapa' do manual)."),
    ("Dígito Verificador do Prefixo", 31, 31,
     "Dígito verificador do prefixo da cooperativa. Na Remessa a planilha oficial manda preencher em branco (em implementações de mercado costuma ir o DV calculado)."),
    ("Código do Cliente/Beneficiário", 32, 39,
     "Código do cliente/beneficiário na cooperativa, 8 dígitos, informado pela cooperativa (planilha 'Contracapa')."),
    ("Dígito Verificador do Código do Cliente", 40, 40,
     "Dígito verificador do código do cliente/beneficiário (planilha 'Contracapa')."),
    ("Número do Convênio Líder", 41, 46,
     "Preencher com espaços em branco."),
    ("Nome do Beneficiário", 47, 76,
     "Nome/razão social do beneficiário (cedente), 30 posições."),
    ("Identificação do Banco (\"756BANCOOBCED\")", 77, 94,
     "Texto fixo '756BANCOOBCED' (código do banco + literal), alinhado à esquerda em 18 posições."),
    ("Data da Gravação da Remessa (DDMMAA)", 95, 100,
     "Data em que o arquivo de remessa foi gerado, no formato DDMMAA (6 dígitos)."),
    ("Sequencial da Remessa", 101, 107,
     "Número sequencial da remessa, acrescido de 1 a cada arquivo enviado; o primeiro é '0000001'."),
    ("Uso Reservado (Filler)", 108, 394,
     "Complemento do registro - preencher com espaços em branco."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial da linha dentro do arquivo; o Header é sempre '000001'."),
]

# ---------------------------------------------------------------------------
# 2. Detalhe (Registro tipo 1) - Arquivo de REMESSA (empresa -> Sicoob)
# ---------------------------------------------------------------------------

DETAIL_REMESSA_FIELDS = [
    ("Identificação do Registro (1 = Detalhe)", 1, 1,
     "Identifica esta linha como um registro de Detalhe (um título). Deve ser sempre '1'."),
    ("Tipo de Inscrição do Beneficiário (01 = CPF, 02 = CNPJ)", 2, 3,
     "Tipo de documento do beneficiário informado a seguir: '01' CPF, '02' CNPJ."),
    ("CPF/CNPJ do Beneficiário", 4, 17,
     "CPF ou CNPJ do beneficiário, 14 dígitos, alinhado à direita com zeros à esquerda, sem pontuação."),
    ("Prefixo da Cooperativa", 18, 21,
     "Prefixo da cooperativa Sicoob (planilha 'Contracapa')."),
    ("Dígito Verificador do Prefixo", 22, 22,
     "Dígito verificador do prefixo da cooperativa (planilha 'Contracapa')."),
    ("Conta Corrente", 23, 30,
     "Conta corrente do beneficiário na cooperativa, 8 dígitos (planilha 'Contracapa')."),
    ("Dígito Verificador da Conta", 31, 31,
     "Dígito verificador da conta corrente (planilha 'Contracapa')."),
    ("Número do Convênio de Cobrança do Beneficiário", 32, 37,
     "Fixo '000000' segundo a planilha."),
    ("Número de Controle do Participante", 38, 62,
     "Campo livre (25 posições) para controle da empresa; o Sicoob devolve o mesmo conteúdo no Retorno."),
    ("Nosso Número [Sequencial]", 63, 73,
     "Número sequencial do título (11 dígitos, a partir de '00000000001'), sem reutilização nem duplicidade. Para comando 01 com emissão a cargo do Sicoob (Tipo de Emissão = 1) todo o campo Nosso Número (63-74) deve ir zerado; para emissão a cargo do beneficiário (Tipo de Emissão = 2) e demais comandos, deve ser preenchido."),
    ("Nosso Número [DV]", 74, 74,
     "Dígito verificador do Nosso Número, calculado por módulo 11 (só preenchido quando o beneficiário informa o Nosso Número; com emissão pelo Sicoob, vai '0' junto com o restante do campo)."),
    ("Número da Parcela", 75, 76,
     "Número da parcela; '01' quando for parcela única."),
    ("Grupo do Título (\"Grupo de Valor\" = 00)", 77, 78,
     "Fixo '00' (no manual, campo 'Grupo de Valor')."),
    ("Uso Reservado (Filler)", 79, 81,
     "Complemento do registro - preencher com espaços em branco."),
    ("Indicativo de Mensagem ou Sacador/Avalista", 82, 82,
     "Em branco: as posições 352-391 podem conter uma mensagem qualquer a ser impressa no boleto. 'A': as posições 352-391 devem conter o nome (e CPF/CNPJ) do sacador/avalista."),
    ("Prefixo do Título", 83, 85,
     "Preencher com espaços em branco (no Retorno o Sicoob devolve a sigla da espécie)."),
    ("Variação da Carteira", 86, 88,
     "Fixo '000'."),
    ("Conta Caução", 89, 89,
     "Fixo '0'."),
    ("Número do Contrato Garantia", 90, 94,
     "Carteira 1 (Simples com Registro): '00000'. Carteira 3 (Garantida Caucionada): número do contrato sem DV."),
    ("Dígito Verificador do Contrato", 95, 95,
     "Carteira 1: '0'. Carteira 3: dígito verificador do contrato."),
    ("Número do Borderô", 96, 101,
     "Preencher apenas em caso de carteira 3 (Garantida Caucionada); nos demais casos, zeros."),
    ("Uso Reservado (Filler)", 102, 105,
     "Complemento do registro - preencher com espaços em branco."),
    ("Tipo de Emissão (1 = Cooperativa, 2 = Cliente)", 106, 106,
     "Quem emite o boleto: '1' Cooperativa (Sicoob gera o Nosso Número), '2' Cliente (o beneficiário emite e informa o Nosso Número)."),
    ("Carteira/Modalidade (01 = Simples c/ Registro, 03 = Garantida Caucionada)", 107, 108,
     "Modalidade de cobrança do título: '01' Simples com Registro, '03' Garantida Caucionada (ver CARTEIRA_MODALIDADE_CODES)."),
    ("Identificação da Ocorrência (Comando/Movimento)", 109, 110,
     "Comando enviado ao Sicoob para este título: '01' Entrada de Títulos, '02' Solicitação de Baixa, '04' Concessão de Abatimento, '05' Cancelamento de Abatimento, '06' Prorrogação de Vencimento, '08' Alteração de Seu Número, '09' Instrução para Protestar, '10' Desistência do Protesto e Baixar Título, '11' Instrução para Dispensar Juros, '12' Alteração de Pagador, '31' Alteração de Outros Dados, '34' Baixa - Pagamento Direto ao Beneficiário (ver COMANDO_REMESSA_CODES)."),
    ("Número do Documento (Seu Número)", 111, 120,
     "Seu Número: número do título/documento atribuído pela empresa, 10 posições."),
    ("Data de Vencimento (DDMMAA)", 121, 126,
     "Data de vencimento no formato DDMMAA. Valores especiais: '888888' = à vista; '999999' = contra apresentação."),
    ("Valor Nominal do Título", 127, 139,
     "Valor de face do título, 13 dígitos (11 inteiros + 2 decimais), alinhado à direita com zeros à esquerda."),
    ("Número do Banco (756)", 140, 142,
     "Código do Sicoob/Bancoob na câmara de compensação. Fixo '756'."),
    ("Prefixo da Cooperativa (Cobradora)", 143, 146,
     "Prefixo da cooperativa responsável pela cobrança (planilha 'Contracapa')."),
    ("Dígito Verificador do Prefixo (Cobradora)", 147, 147,
     "Dígito verificador do prefixo da cooperativa (planilha 'Contracapa')."),
    ("Espécie do Título", 148, 149,
     "Espécie do documento: '01' Duplicata Mercantil, '02' Nota Promissória, '03' Nota de Seguro, '05' Recibo, '06' Duplicata Rural, '08' Letra de Câmbio, '09' Warrant, '10' Cheque, '12' Duplicata de Serviço, '13' Nota de Débito, '14' Triplicata Mercantil, '15' Triplicata de Serviço, '18' Fatura, '20' Apólice de Seguro, '21' Mensalidade Escolar, '22' Parcela de Consórcio, '99' Outros (ver ESPECIE_TITULO_CODES)."),
    ("Aceite do Título (0 = Sem aceite, 1 = Com aceite)", 150, 150,
     "Indica se o título tem aceite: '0' sem aceite, '1' com aceite."),
    ("Data de Emissão do Título (DDMMAA)", 151, 156,
     "Data de emissão do título no formato DDMMAA."),
    ("Primeira Instrução Codificada", 157, 158,
     "Primeira instrução de cobrança/impressão (ver INSTRUCAO_CODES). '00'+'00' não imprime nada; '01'+'01' ignora instruções CNAB e imprime as mensagens do Trailer do arquivo; '99'+'99' (com posição 82 em branco) ignora instruções CNAB e imprime a mensagem das posições 352-391 do Detalhe; demais combinações imprimem o texto padrão da instrução."),
    ("Segunda Instrução Codificada", 159, 160,
     "Segunda instrução (mesmos códigos e regras da Primeira Instrução, posições 157-158)."),
    ("Taxa Mensal por Atraso (taxa de mora mês, 99V9999)", 161, 166,
     "Taxa de mora ao mês, 6 dígitos com 4 decimais implícitos (ex.: '022000' = 2,20%). Percentual, não valor monetário."),
    ("Taxa de Multa (%, 99V9999)", 167, 172,
     "Taxa de multa, 6 dígitos com 4 decimais implícitos (ex.: '022000' = 2,20%)."),
    ("Tipo de Distribuição (1 = Cooperativa, 2 = Cliente)", 173, 173,
     "Quem distribui/entrega o boleto ao pagador: '1' Cooperativa, '2' Cliente."),
    ("Data do Primeiro Desconto (DDMMAA)", 174, 179,
     "Data limite para o pagador pagar com desconto, DDMMAA (não pode ser posterior ao vencimento). Zeros quando não há desconto."),
    ("Valor do Primeiro Desconto", 180, 192,
     "Valor do desconto (13 dígitos, 2 decimais). Zeros quando não há desconto."),
    ("Código da Moeda", 193, 193,
     "Código da moeda do título. Se for Real, o campo seguinte (194-205) é o IOF; se diferente de Real, é a quantidade monetária. O manual não lista a tabela de códigos ('9' = Real na prática de eduardokum/brcobranca)."),
    ("Valor do IOF / Quantidade Monetária", 194, 205,
     "12 dígitos: valor do IOF quando a moeda é Real, ou a quantidade monetária nos demais casos. Normalmente zeros."),
    ("Valor do Abatimento", 206, 218,
     "Valor de abatimento a conceder (13 dígitos, 2 decimais). Zeros quando não há."),
    ("Tipo de Inscrição do Sacado (01 = CPF, 02 = CNPJ)", 219, 220,
     "Tipo de documento do pagador informado a seguir: '01' CPF, '02' CNPJ."),
    ("CPF/CNPJ do Sacado", 221, 234,
     "CPF ou CNPJ do pagador, 14 dígitos, alinhado à direita com zeros à esquerda, sem pontuação."),
    ("Nome do Sacado (Pagador)", 235, 274,
     "Nome (razão social) do pagador, 40 posições."),
    ("Endereço do Sacado (Pagador)", 275, 311,
     "Endereço do pagador, 37 posições. (Atenção: implementações de mercado às vezes usam 40 posições e bairro de 12; o manual oficial define 37 + 15.)"),
    ("Bairro do Sacado (Pagador)", 312, 326,
     "Bairro do pagador, 15 posições."),
    ("CEP do Sacado (Pagador)", 327, 334,
     "CEP do pagador, 8 dígitos sem hífen."),
    ("Cidade do Sacado (Pagador)", 335, 349,
     "Cidade do pagador, 15 posições."),
    ("UF do Sacado (Pagador)", 350, 351,
     "Sigla da UF do pagador."),
    ("Observações/Mensagem ou Sacador/Avalista", 352, 391,
     "Com a posição 82 em branco e Primeira/Segunda Instrução = '99'/'99': texto impresso em 'texto de responsabilidade da Empresa' no Recibo do Sacado e na Ficha de Compensação. Com a posição 82 = 'A': nome/razão social do Sacador/Avalista."),
    ("Número de Dias para Protesto", 392, 393,
     "Quantidade de dias para envio a protesto; '0' usa o prazo padrão cadastrado na cooperativa para o cliente."),
    ("Uso Reservado (Filler)", 394, 394,
     "Complemento do registro - preencher com espaço em branco. (A planilha oficial grafa 394-395, mas 395 pertence ao Sequencial; tratado como 394-394.)"),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial da linha no arquivo, incrementado em 1 a cada registro (Header = 000001, primeiro Detalhe = 000002 ...)."),
]

# ---------------------------------------------------------------------------
# 3. Trailer (Registro tipo 9) - Arquivo de REMESSA (empresa -> Sicoob)
# ---------------------------------------------------------------------------

TRAILER_REMESSA_FIELDS = [
    ("Identificação do Registro (9 = Trailer)", 1, 1,
     "Marca o fim do arquivo. Deve ser sempre o caractere '9'."),
    ("Uso Reservado (Filler)", 2, 194,
     "Complemento do registro - preencher com espaços em branco."),
    ("Mensagem de Responsabilidade do Beneficiário [Linha 1]", 195, 234,
     "Só usada quando Primeira e Segunda Instrução do Detalhe = '01'/'01': mensagem/instrução (40 posições) impressa no boleto. Nos demais casos, espaços em branco."),
    ("Mensagem de Responsabilidade do Beneficiário [Linha 2]", 235, 274,
     "Idem Linha 1 (40 posições)."),
    ("Mensagem de Responsabilidade do Beneficiário [Linha 3]", 275, 314,
     "Idem Linha 1 (40 posições)."),
    ("Mensagem de Responsabilidade do Beneficiário [Linha 4]", 315, 354,
     "Idem Linha 1 (40 posições)."),
    ("Mensagem de Responsabilidade do Beneficiário [Linha 5]", 355, 394,
     "Idem Linha 1 (40 posições)."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial dessa linha (a última do arquivo), incrementado em 1 a cada registro."),
]

# ---------------------------------------------------------------------------
# 4. Header (Registro tipo 0) - Arquivo de RETORNO (Sicoob -> empresa)
# ---------------------------------------------------------------------------

HEADER_RETORNO_FIELDS = [
    ("Identificação do Registro (0 = Header)", 1, 1,
     "Marca o início do arquivo. Deve ser sempre o caractere '0'."),
    ("Tipo de Operação (2 = Retorno)", 2, 2,
     "Indica que este é um arquivo de Retorno. Deve ser sempre '2'."),
    ("Identificação por Extenso do Tipo de Operação (\"RETORNO\")", 3, 9,
     "Texto fixo 'RETORNO'."),
    ("Identificação do Tipo de Serviço (01)", 10, 11,
     "Código do serviço do arquivo; para cobrança é sempre '01'."),
    ("Identificação por Extenso do Tipo de Serviço (\"COBRANÇA\")", 12, 19,
     "Texto fixo 'COBRANÇA' (8 posições)."),
    ("Uso Reservado (Filler)", 20, 26,
     "Complemento do registro - o sistema retorna com as posições em branco."),
    ("Prefixo da Cooperativa", 27, 30,
     "Prefixo (código) da cooperativa Sicoob, 4 dígitos."),
    ("Dígito Verificador do Prefixo", 31, 31,
     "No Retorno, este campo sempre volta com o valor '0' (zero)."),
    ("Código do Cliente/Beneficiário", 32, 39,
     "Código do cliente/beneficiário na cooperativa, 8 dígitos."),
    ("Dígito Verificador do Código do Cliente", 40, 40,
     "Dígito verificador do código do cliente/beneficiário."),
    ("Número do Convênio Líder", 41, 46,
     "O sistema retorna o número da conta corrente do cliente/beneficiário."),
    ("Nome do Beneficiário", 47, 76,
     "Nome/razão social do beneficiário, 30 posições."),
    ("Identificação do Banco (\"756 - BANCOOB S/A\")", 77, 94,
     "Texto de identificação do banco, 18 posições, ex.: '756 - BANCOOB S/A'."),
    ("Data da Gravação do Retorno (DDMMAA)", 95, 100,
     "Data em que o Sicoob gerou o arquivo de retorno, DDMMAA (6 dígitos)."),
    ("Sequencial do Retorno", 101, 107,
     "Número sequencial atribuído pelo Sicoob, acrescido de 1 a cada retorno; começa em '0000001'."),
    ("Uso Reservado (Filler)", 108, 394,
     "Complemento do registro - o sistema retorna com as posições em branco."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial da linha no arquivo; o Header é sempre '000001'."),
]

# ---------------------------------------------------------------------------
# 5. Detalhe (Registro tipo 1) - Arquivo de RETORNO (Sicoob -> empresa)
# ---------------------------------------------------------------------------

DETAIL_RETORNO_FIELDS = [
    ("Identificação do Registro (1 = Detalhe)", 1, 1,
     "Identifica esta linha como um registro de Detalhe (um título). Deve ser sempre '1'."),
    ("Tipo de Inscrição do Beneficiário (01 = CPF, 02 = CNPJ)", 2, 3,
     "Tipo de documento do beneficiário: '01' CPF, '02' CNPJ."),
    ("CPF/CNPJ do Beneficiário", 4, 17,
     "CPF ou CNPJ do beneficiário, 14 dígitos."),
    ("Prefixo da Cooperativa", 18, 21,
     "Prefixo da cooperativa Sicoob."),
    ("Dígito Verificador do Prefixo", 22, 22,
     "Dígito verificador do prefixo da cooperativa."),
    ("Conta Corrente", 23, 30,
     "Conta corrente do beneficiário, 8 dígitos."),
    ("Dígito Verificador da Conta", 31, 31,
     "Dígito verificador da conta corrente."),
    ("Número do Convênio de Cobrança do Beneficiário", 32, 37,
     "Fixo '000000'."),
    ("Número de Controle do Participante", 38, 62,
     "O sistema devolve as informações enviadas na Remessa (25 posições)."),
    ("Nosso Número [Sequencial]", 63, 73,
     "Número sequencial do título no Sicoob (11 dígitos)."),
    ("Nosso Número [DV]", 74, 74,
     "Dígito verificador do Nosso Número (módulo 11)."),
    ("Número da Parcela", 75, 76,
     "Número da parcela do título."),
    ("Grupo do Título (\"Grupo de Valor\" = 00)", 77, 80,
     "Fixo '00' (4 posições no Retorno; no manual, campo 'Grupo de Valor')."),
    ("Código de Baixa/Recusa", 81, 82,
     "Código de baixa/recusa do título. O manual oficial CNAB400 não traz a tabela de códigos deste campo."),
    ("Prefixo do Título (espécie)", 83, 85,
     "Sigla da espécie do título: 'DM' Duplicata Mercantil, 'CH' Cheque, 'DS' Duplicata de Serviço, 'PC' Parcela de Consórcio, 'OU' Outros."),
    ("Variação da Carteira", 86, 88,
     "Fixo '000'."),
    ("Conta Caução", 89, 89,
     "Fixo '0'."),
    ("Código de Responsabilidade", 90, 94,
     "Fixo '00000'."),
    ("Dígito Verificador do Código de Responsabilidade", 95, 95,
     "Fixo '0'."),
    ("Taxa de Desc. (%, 999V99)", 96, 100,
     "Taxa de desconto, 5 dígitos com 2 decimais implícitos. Percentual, não valor monetário."),
    ("Taxa de I.O.F. (%, 9V9999)", 101, 105,
     "Taxa de IOF, 5 dígitos com 4 decimais implícitos. Percentual, não valor monetário."),
    ("Uso Reservado (Filler)", 106, 106,
     "Complemento do registro - o sistema retorna com a posição em branco."),
    ("Carteira/Modalidade (01 = Simples c/ Registro, 03 = Garantida Caucionada)", 107, 108,
     "Modalidade de cobrança do título: '01' Simples com Registro, '03' Garantida Caucionada."),
    ("Código da Ocorrência (Comando/Movimento - ver OCORRENCIA_CODES)", 109, 110,
     "Código de 2 dígitos do que aconteceu com o título neste retorno: '02' Confirmação de Entrada, '04' Transferência de Carteira/Entrada, '05' Liquidação Sem Registro, '06' Liquidação Normal, '09' Baixa de Título, '10' Baixa Solicitada (pedido do beneficiário), '11' Títulos em Ser, '14' Alteração de Vencimento, '15' Liquidação em Cartório, '23' Encaminhado a Protesto, '27' Confirmação de Alteração de Dados, '48' Confirmação de Instrução de Transferência de Carteira/Modalidade."),
    ("Data da Ocorrência (Entrada/Liquidação, DDMMAA)", 111, 116,
     "Data da entrada/liquidação (data do movimento informado na ocorrência), DDMMAA."),
    ("Número do Documento (Seu Número)", 117, 126,
     "Devolve o Seu Número (número atribuído pela empresa) enviado na Remessa, 10 posições."),
    ("Uso Reservado (Filler)", 127, 146,
     "Complemento do registro - o sistema retorna com as posições em branco."),
    ("Data de Vencimento (DDMMAA)", 147, 152,
     "Data de vencimento do título, DDMMAA."),
    ("Valor Nominal do Título", 153, 165,
     "Valor de face do título, 13 dígitos (11 inteiros + 2 decimais)."),
    ("Código do Banco Recebedor", 166, 168,
     "Código do banco recebedor do pagamento; zeros quando não informado."),
    ("Prefixo da Agência Recebedora", 169, 172,
     "Prefixo da agência do banco recebedor; zeros quando não informado."),
    ("Dígito Verificador do Prefixo da Agência Recebedora", 173, 173,
     "Dígito verificador do prefixo da agência recebedora."),
    ("Espécie do Título", 174, 175,
     "Espécie do documento: '01' Duplicata Mercantil, '02' Nota Promissória, '03' Nota de Seguro, '05' Recibo, '06' Duplicata Rural, '08' Letra de Câmbio, '09' Warrant, '10' Cheque, '12' Duplicata de Serviço, '13' Nota de Débito, '14' Triplicata Mercantil, '15' Triplicata de Serviço, '18' Fatura, '20' Apólice de Seguro, '21' Mensalidade Escolar, '22' Parcela de Consórcio, '99' Outros."),
    ("Data do Crédito (DDMMAA)", 176, 181,
     "Data em que o valor foi/será creditado ao beneficiário, DDMMAA."),
    ("Valor da Tarifa", 182, 188,
     "Valor da tarifa de cobrança, 7 dígitos (5 inteiros + 2 decimais)."),
    ("Valor de Outras Despesas", 189, 201,
     "Outras despesas (13 dígitos, 2 decimais)."),
    ("Juros do Desconto", 202, 214,
     "Juros do desconto (13 dígitos, 2 decimais)."),
    ("IOF do Desconto", 215, 227,
     "IOF do desconto (13 dígitos, 2 decimais)."),
    ("Valor do Abatimento", 228, 240,
     "Valor de abatimento concedido sobre o título (13 dígitos, 2 decimais)."),
    ("Desconto Concedido (diferença entre valor do título e valor recebido)", 241, 253,
     "Desconto concedido ao pagador (13 dígitos, 2 decimais)."),
    ("Valor Pago (Valor Recebido / Recebido Parcial)", 254, 266,
     "Valor efetivamente recebido do pagador (pode ser parcial), 13 dígitos (2 decimais)."),
    ("Juros de Mora", 267, 279,
     "Juros de mora recebidos junto com o pagamento (13 dígitos, 2 decimais)."),
    ("Valor de Outros Recebimentos", 280, 292,
     "Outros recebimentos (por ex. multa) junto com o pagamento (13 dígitos, 2 decimais)."),
    ("Valor do Abatimento Não Aproveitado pelo Pagador", 293, 305,
     "Abatimento não aproveitado pelo pagador (13 dígitos, 2 decimais)."),
    ("Valor do Lançamento", 306, 318,
     "Valor do lançamento na conta do beneficiário (13 dígitos, 2 decimais)."),
    ("Indicativo Débito/Crédito", 319, 319,
     "Indica se o lançamento é débito ou crédito (a planilha oficial não lista a tabela de códigos)."),
    ("Indicativo do Ajuste (manual: \"Indicativo valor\")", 320, 320,
     "Indicativo associado ao Valor do Ajuste (a planilha oficial não lista a tabela de códigos)."),
    ("Valor do Ajuste", 321, 332,
     "Valor do ajuste, 12 dígitos (10 inteiros + 2 decimais)."),
    ("Uso Reservado (Filler)", 333, 342,
     "Complemento do registro - o sistema retorna com as posições em branco."),
    ("CPF/CNPJ do Pagador", 343, 356,
     "CPF/CNPJ do pagador, 14 dígitos. (A planilha oficial grafa INICIO/FINAL 343-357, mas TAM e máscara são 14 - ver nota no docstring; tratado como 343-356.)"),
    ("Uso Reservado (Filler)", 357, 394,
     "Complemento do registro - o sistema retorna com as posições em branco."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial da linha no arquivo, incrementado em 1 a cada registro."),
]

# ---------------------------------------------------------------------------
# 6. Trailer (Registro tipo 9) - Arquivo de RETORNO (Sicoob -> empresa)
# ---------------------------------------------------------------------------

TRAILER_RETORNO_FIELDS = [
    ("Identificação do Registro (9 = Trailer)", 1, 1,
     "Marca o fim do arquivo. Deve ser sempre o caractere '9'."),
    ("Identificação do Tipo de Serviço (02)", 2, 3,
     "Fixo '02'."),
    ("Número do Banco (756)", 4, 6,
     "Código do Sicoob/Bancoob na câmara de compensação. Fixo '756'."),
    ("Código da Cooperativa Remetente", 7, 10,
     "Código (prefixo) da cooperativa remetente, 4 dígitos."),
    ("Sigla da Cooperativa Remetente", 11, 35,
     "Sigla/nome curto da cooperativa remetente, 25 posições."),
    ("Endereço da Cooperativa Remetente", 36, 85,
     "Endereço da cooperativa remetente, 50 posições."),
    ("Bairro da Cooperativa Remetente", 86, 115,
     "Bairro da cooperativa remetente, 30 posições."),
    ("CEP da Cooperativa Remetente", 116, 123,
     "CEP da cooperativa remetente, 8 posições."),
    ("Cidade da Cooperativa Remetente", 124, 153,
     "Cidade da cooperativa remetente, 30 posições."),
    ("UF da Cooperativa Remetente", 154, 155,
     "Sigla da UF da cooperativa remetente."),
    ("Data do Movimento (DDMMAAAA)", 156, 163,
     "Data do movimento no formato DDMMAAAA (8 dígitos) - diferente do DDMMAA (6 dígitos) usado no restante do arquivo."),
    ("Quantidade de Registros no Detalhe", 164, 171,
     "Quantidade de registros de Detalhe (títulos) do arquivo, 8 dígitos."),
    ("Último Nosso Número do Beneficiário", 172, 182,
     "Último Nosso Número (11 dígitos) utilizado pelo beneficiário."),
    ("Uso Reservado (Filler)", 183, 394,
     "Complemento do registro - o sistema retorna com as posições em branco."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial dessa linha (a última do arquivo), incrementado em 1 a cada registro."),
]

# Compatibilidade com o módulo Sicredi (que tem um único Trailer): alias do
# Trailer de RETORNO. Para Remessa use TRAILER_REMESSA_FIELDS.
TRAILER_FIELDS = TRAILER_RETORNO_FIELDS

# ---------------------------------------------------------------------------
# 7. Tabela de Ocorrências (campo "Comando/Movimento" do Retorno, 109-110)
# ---------------------------------------------------------------------------

OCORRENCIA_CODES = {
    "02": "Confirmação de Entrada de Título",
    "04": "Transferência de Carteira/Entrada",
    "05": "Liquidação Sem Registro",
    "06": "Liquidação Normal",
    "09": "Baixa de Título",
    "10": "Baixa Solicitada (Baixa - Pedido do Beneficiário)",
    "11": "Títulos em Ser (em carteira, vencidos e a vencer)",
    "14": "Alteração de Vencimento",
    "15": "Liquidação em Cartório",
    "23": "Encaminhado a Protesto",
    "27": "Confirmação de Alteração de Dados",
    "48": "Confirmação de Instrução de Transferência de Carteira/Modalidade de Cobrança",
}

# ---------------------------------------------------------------------------
# 8. Tabela de comandos da REMESSA (campo "Comando/Movimento", posições 109-110)
# ---------------------------------------------------------------------------

COMANDO_REMESSA_CODES = {
    "01": "Entrada de Títulos",
    "02": "Solicitação de Baixa",
    "04": "Concessão de Abatimento",
    "05": "Cancelamento de Abatimento",
    "06": "Prorrogação de Vencimento",
    "08": "Alteração de Seu Número",
    "09": "Instrução para Protestar",
    "10": "Desistência do Protesto e Baixar Título",
    "11": "Instrução para Dispensar Juros",
    "12": "Alteração de Pagador",
    "31": "Alteração de Outros Dados",
    "34": "Baixa - Pagamento Direto ao Beneficiário",
}

# ---------------------------------------------------------------------------
# 9. Tabelas auxiliares (Espécie do Título, Instruções, Carteira/Modalidade)
# ---------------------------------------------------------------------------

# Remessa 148-149 e Retorno 174-175
ESPECIE_TITULO_CODES = {
    "01": "Duplicata Mercantil",
    "02": "Nota Promissória",
    "03": "Nota de Seguro",
    "05": "Recibo",
    "06": "Duplicata Rural",
    "08": "Letra de Câmbio",
    "09": "Warrant",
    "10": "Cheque",
    "12": "Duplicata de Serviço",
    "13": "Nota de Débito",
    "14": "Triplicata Mercantil",
    "15": "Triplicata de Serviço",
    "18": "Fatura",
    "20": "Apólice de Seguro",
    "21": "Mensalidade Escolar",
    "22": "Parcela de Consórcio",
    "99": "Outros",
}

# Remessa 157-158 (Primeira Instrução) e 159-160 (Segunda Instrução).
# Regras de impressão: '00'+'00' não imprime nada; '01'+'01' imprime as
# mensagens do Trailer do arquivo; '99'+'99' (posição 82 em branco) imprime a
# mensagem das posições 352-391 do Detalhe; demais combinações imprimem o texto
# padrão da instrução abaixo.
INSTRUCAO_CODES = {
    "00": "Ausência de Instruções",
    "01": "Cobrar Juros",
    "03": "Protestar 3 Dias Após Vencimento",
    "04": "Protestar 4 Dias Após Vencimento",
    "05": "Protestar 5 Dias Após Vencimento",
    "07": "Não Protestar",
    "10": "Protestar 10 Dias Após Vencimento",
    "15": "Protestar 15 Dias Após Vencimento",
    "20": "Protestar 20 Dias Após Vencimento",
    "22": "Conceder Desconto Só Até Data Estipulada",
    "42": "Devolver Após 15 Dias Vencido",
    "43": "Devolver Após 30 Dias Vencido",
    "99": "Mensagem Livre (posições 352-391 do Detalhe)",
}

# Remessa 107-108 e Retorno 107-108
CARTEIRA_MODALIDADE_CODES = {
    "01": "Simples com Registro",
    "03": "Garantida Caucionada",
}

# ---------------------------------------------------------------------------
# 10. Tabela de Motivos - NÃO existe no manual oficial CNAB400 do Sicoob
# ---------------------------------------------------------------------------
# O único campo relacionado é "Código de Baixa/Recusa" (Retorno 81-82) e a
# planilha oficial não traz a tabela de códigos. Mantido vazio de propósito
# (ver nota no docstring do módulo).

MOTIVOS_CODES = {}


def _validate_contiguous(fields, name):
    """Sanity check: positions must run 1..400 with no gaps/overlaps."""
    expected = 1
    for field_name, start, end, _desc in fields:
        if start != expected or end < start:
            raise AssertionError(
                "%s: gap/overlap near field %r (expected start %d, got %d-%d)"
                % (name, field_name, expected, start, end)
            )
        expected = end + 1
    if expected != 401:
        raise AssertionError("%s: fields end at %d, expected 400" % (name, expected - 1))


if __name__ == "__main__":
    _lists = [
        (HEADER_REMESSA_FIELDS, "HEADER_REMESSA_FIELDS"),
        (DETAIL_REMESSA_FIELDS, "DETAIL_REMESSA_FIELDS"),
        (TRAILER_REMESSA_FIELDS, "TRAILER_REMESSA_FIELDS"),
        (HEADER_RETORNO_FIELDS, "HEADER_RETORNO_FIELDS"),
        (DETAIL_RETORNO_FIELDS, "DETAIL_RETORNO_FIELDS"),
        (TRAILER_RETORNO_FIELDS, "TRAILER_RETORNO_FIELDS"),
        (TRAILER_FIELDS, "TRAILER_FIELDS"),
    ]
    for _fields, _name in _lists:
        _validate_contiguous(_fields, _name)
        for _f in _fields:
            assert len(_f) == 4, (_name, _f)
    print("All Sicoob field layouts are contiguous and cover positions 1-400.")
    for _fields, _name in _lists:
        print("%s: %d fields" % (_name, len(_fields)))
    print("OCORRENCIA_CODES: %d entries" % len(OCORRENCIA_CODES))
    print("COMANDO_REMESSA_CODES: %d entries" % len(COMANDO_REMESSA_CODES))
    print("MOTIVOS_CODES: %d entries" % len(MOTIVOS_CODES))
