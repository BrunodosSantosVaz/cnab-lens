# -*- coding: utf-8 -*-
"""
CNAB400 (FEBRABAN/CNAB - Cobrança Bancaria) field layout reference data.

Sources used (accessed 2026-08-31):
  1. Itau Unibanco - "Cobrança Bancaria - Intercambio Eletronico de Arquivos -
     Layout de Arquivos - CNAB 400" (Janeiro/2017), official bank manual.
     https://download.itau.com.br/bankline/layout_cobranca_400bytes_cnab_itau.pdf
     -> Primary source for HEADER_FIELDS, TRAILER_FIELDS, DETAIL_REMESSA_FIELDS,
        DETAIL_RETORNO_FIELDS and OCORRENCIA_CODES. Itau explicitly states this
        layout "segue padronizacao estabelecida pelo CNAB (Centro Nacional de
        Automação Bancaria), orgao tecnico da FEBRABAN, com algumas adaptacoes",
        i.e. it is the generic FEBRABAN CNAB400 cobranca layout used (with only
        minor, mostly cosmetic, differences) by nearly all Brazilian banks.
  2. Banco do Brasil - "Layout para arquivo de retorno CNAB 400"
     https://www.bb.com.br/docs/pub/emp/empl/dwn/Doc2628CBR643Pos7.pdf
     -> Cross-checked field positions/names for header, detail and trailer.
  3. Grafeno - "Grafeno CNAB 400 - Remessa" / "Grafeno CNAB 400 - Retorno"
     https://8949671.fs1.hubspotusercontent-na1.net/hubfs/8949671/Layouts%20-%20Grafeno/
     Grafeno%20CNAB%20400%20-%20Remessa_v2_9.pdf /
     Grafeno%20CNAB%20400%20-%20Retorno_v2_9.pdf
     -> Modern, bank-agnostic restatement of the same FEBRABAN layout; used to
        confirm the generic/common field names and occurrence-code positions
        (109-110) across banks.
  4. glauberportella/cnab-layouts (GitHub) - community-maintained YAML CNAB
     layouts for multiple banks (Itau, Bradesco, BB, Caixa, Santander, etc.)
     https://github.com/glauberportella/cnab-layouts
     -> Used to confirm which segments are considered "common/shared" across
        banks vs bank-specific extensions.

Notes on confidence:
  - HEADER_FIELDS / DETAIL_REMESSA_FIELDS / DETAIL_RETORNO_FIELDS positions
    below are transcribed directly from the Itau CNAB400 manual (source #1),
    which matches the generic FEBRABAN layout used by BB, Bradesco, Caixa,
    Santander, Sicredi, Sicoob, etc. for the vast majority of fields.
  - TRAILER_FIELDS is intentionally minimal (position 1 = "9", positions
    2-394 = filler/blank, 395-400 = sequential number) because that is what
    the FEBRABAN/CNAB400 cobranca standard defines - unlike CNAB240, the
    CNAB400 trailer record carries no totals. A few banks reuse small
    portions of the filler for internal control; those bytes are still
    rendered here as "Uso Reservado/Banco (Preenchimento generico)".
  - Positions 101-119 of HEADER_FIELDS are blank/filler in REMESSA files but
    carry real content (densidade de gravacao, numero sequencial do arquivo
    de retorno, data de credito) in RETORNO files. Both interpretations are
    noted in the field label since this module intentionally uses ONE
    generic header layout for both file types, as requested.
  - OCORRENCIA_CODES reflects the codes documented by Itau (source #1),
    which is one of the most complete published tables. Some banks do not
    use every code, and a handful of codes (>= 51) are bank/tariff-specific
    and may carry a slightly different meaning at other institutions - those
    are marked implicitly by being tariff/custas related. Codes considered
    "core"/most universal across all banks: 02, 03, 06, 09, 10, 11, 12, 13,
    14, 15, 16, 17, 19, 20, 21, 24, 25, 32.
  - Bank-specific REMESSA "optional" detail segments (registro tipo 2, 4, 5 -
    multa, rateio de credito, e-mail/sacador-avalista) and the RETORNO
    "cheque devolvido/compensado" optional segment exist in the Itau manual
    but are NOT included here, since the task only asked for the single
    mandatory Detalhe (tipo 1) record for remessa and retorno.
  - A 4a coluna foi acrescentada a cada tabela de campos com uma descrição
    mais longa (o que o campo significa, como o banco costuma calculá-lo ou
    usá-lo). Nomes de dígito verificador (DAC) no FEBRABAN genérico não têm
    uma fórmula única documentada aqui porque o algoritmo varia de banco
    para banco (normalmente módulo 11) - quando o cálculo é conhecido e
    fixo (caso do Sicredi), ele está descrito em `cnab400_layout_sicredi.py`.
"""

# ---------------------------------------------------------------------------
# 1. Bank names (COMPE codes)
# ---------------------------------------------------------------------------

BANK_NAMES = {
    "001": "Banco do Brasil",
    "003": "Banco da Amazonia",
    "004": "Banco do Nordeste do Brasil",
    "021": "Banestes",
    "025": "Banco Alfa",
    "033": "Santander",
    "037": "Banpara",
    "041": "Banrisul",
    "047": "Banese",
    "070": "BRB - Banco de Brasilia",
    "077": "Banco Inter",
    "084": "Uniprime Norte do Parana",
    "085": "Ailos (Cooperativa Central de Crédito)",
    "104": "Caixa Economica Federal",
    "121": "Banco Agibank",
    "136": "Unicred do Brasil",
    "151": "Banco Nossa Caixa (incorporado ao Banco do Brasil)",
    "175": "Banco Rabobank",
    "212": "Banco Original",
    "224": "Banco Fibra",
    "237": "Bradesco",
    "246": "Banco ABC Brasil",
    "260": "Nu Pagamentos (Nubank)",
    "290": "PagSeguro Internet (PagBank)",
    "318": "Banco BMG",
    "336": "Banco C6 (C6 Bank)",
    "341": "Itau Unibanco",
    "348": "Banco XP",
    "356": "Banco Real (incorporado ao Santander)",
    "380": "PicPay",
    "399": "HSBC Bank Brasil",
    "403": "Cora Sociedade de Crédito Direto",
    "422": "Banco Safra",
    "456": "Banco MUFG Brasil",
    "604": "Banco Industrial do Brasil",
    "623": "Banco Pan (ex-Panamericano)",
    "633": "Banco Rendimento",
    "655": "Banco Votorantim (BV)",
    "707": "Banco Daycoval",
    "745": "Banco Citibank",
    "748": "Sicredi",
    "756": "Sicoob (Bancoob)",
}

# ---------------------------------------------------------------------------
# 2. Header (Registro tipo 0) - generic layout shared by Remessa and Retorno
# ---------------------------------------------------------------------------

HEADER_FIELDS = [
    ("Identificação do Registro (0 = Header)", 1, 1,
     "Marca o início do arquivo. Deve ser sempre o caractere '0'; é o primeiro registro de todo arquivo CNAB400."),
    ("Identificação do Arquivo (1=Remessa, 2=Retorno)", 2, 2,
     "Indica o sentido do arquivo: '1' quando a empresa envia os títulos ao banco (Remessa), '2' quando o banco devolve o processamento (Retorno)."),
    ("Literal de Remessa/Retorno (\"REMESSA\"/\"RETORNO\")", 3, 9,
     "Texto fixo 'REMESSA' ou 'RETORNO', deve bater com o valor da posição 2 - é uma checagem redundante que o banco usa para validar o arquivo."),
    ("Código do Serviço (01 = Cobrança)", 10, 11,
     "Código do tipo de serviço do arquivo; para cobrança bancária o valor padrão é '01'."),
    ("Literal de Serviço (ex.: \"COBRANCA\")", 12, 26,
     "Texto fixo descrevendo o serviço (normalmente 'COBRANCA'), preenchido à esquerda e completado com brancos."),
    ("Agência do Cedente/Beneficiário", 27, 30,
     "Número da agência bancária onde a empresa (cedente/beneficiário) mantém a conta usada na cobrança."),
    ("Complemento de Registro (Zeros)", 31, 32,
     "Preenchimento fixo com zeros, sem uso - mantido apenas para respeitar o tamanho de 400 posições do registro."),
    ("Conta Corrente do Cedente/Beneficiário", 33, 37,
     "Número da conta corrente da empresa na agência informada acima, sem o dígito verificador."),
    ("Dígito Verificador da Agência/Conta (DAC)", 38, 38,
     "Dígito verificador calculado pelo banco sobre agência+conta, para confirmar que os dois números acima não foram digitados errado. O algoritmo de cálculo (normalmente módulo 11) é específico de cada banco - consulte o manual do banco emissor."),
    ("Complemento de Registro (Brancos)", 39, 46,
     "Preenchimento com espaços em branco, sem uso."),
    ("Nome da Empresa/Cedente", 47, 76,
     "Razão social ou nome fantasia da empresa (cedente/beneficiário) que está enviando a cobrança."),
    ("Código do Banco na Câmara de Compensação", 77, 79,
     "Código de 3 dígitos do banco perante o Banco Central/Câmara de Compensação (ex.: 341 = Itaú, 748 = Sicredi); é o campo que o app usa para identificar automaticamente o banco emissor."),
    ("Nome do Banco", 80, 94,
     "Nome (ou sigla) do banco por extenso, associado ao código de compensação acima."),
    ("Data de Gravação do Arquivo (DDMMAA)", 95, 100,
     "Data em que o arquivo foi gerado, no formato dia/mês/ano com 2 dígitos cada (DDMMAA). Alguns bancos gravam AAAAMMDD (8 posições) nesta mesma posição inicial - o app tenta as duas variações automaticamente."),
    ("Densidade de Gravação do Arquivo (uso do Banco, geralmente em Retorno)", 101, 105,
     "Uso interno do banco: densidade de gravação da fita/mídia original usada no processamento em lote. Raramente relevante em arquivos modernos em texto simples."),
    ("Unidade de Densidade de Gravação (uso do Banco, geralmente em Retorno)", 106, 108,
     "Uso interno do banco: unidade de medida da densidade de gravação acima (ex.: BPI)."),
    ("Número Sequencial do Arquivo de Retorno (uso do Banco, so em Retorno)", 109, 113,
     "Uso interno do banco: número sequencial que o banco atribui a cada arquivo de retorno gerado para essa empresa."),
    ("Data de Crédito dos Lancamentos (DDMMAA, uso do Banco, so em Retorno)", 114, 119,
     "Uso interno do banco (só em Retorno): data em que os créditos dos títulos liquidados nesse arquivo serão disponibilizados na conta da empresa."),
    ("Uso Reservado/Banco (Complemento do Registro)", 120, 394,
     "Trecho reservado para uso interno do banco; normalmente preenchido com brancos ou zeros, sem padronização entre instituições."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial da linha dentro do arquivo, começando em 1 no Header e incrementando a cada registro até o Trailer - serve para o banco detectar linhas faltando ou fora de ordem."),
]

# ---------------------------------------------------------------------------
# 3. Trailer (Registro tipo 9) - generic layout shared by Remessa and Retorno
# ---------------------------------------------------------------------------

TRAILER_FIELDS = [
    ("Identificação do Registro (9 = Trailer)", 1, 1,
     "Marca o fim do arquivo. Deve ser sempre o caractere '9'; é sempre o último registro do arquivo."),
    ("Uso Reservado/Banco (Preenchimento generico/brancos)", 2, 394,
     "No CNAB400 de cobrança (diferente do CNAB240), o Trailer não carrega totais - esse trecho fica em branco/zerado, ou é usado de forma não padronizada por alguns bancos para controle interno."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial dessa linha (a última do arquivo) - deve ser igual à quantidade total de registros do arquivo (Header + Detalhes + Trailer)."),
]

# ---------------------------------------------------------------------------
# 4. Detalhe (Registro tipo 1) - Arquivo de RETORNO (banco -> empresa)
# ---------------------------------------------------------------------------

DETAIL_RETORNO_FIELDS = [
    ("Identificação do Registro (1 = Detalhe/Transação)", 1, 1,
     "Identifica esta linha como um registro de Detalhe (um título/lançamento). Deve ser sempre '1'."),
    ("Código de Inscrição da Empresa (01=CPF, 02=CNPJ)", 2, 3,
     "Indica o tipo de documento da empresa cedente informado a seguir: '01' para CPF, '02' para CNPJ."),
    ("Número de Inscrição da Empresa (CPF/CNPJ)", 4, 17,
     "CPF ou CNPJ da empresa cedente, alinhado à direita com zeros à esquerda."),
    ("Agência Mantenedora da Conta", 18, 21,
     "Agência bancária da conta da empresa usada nessa cobrança."),
    ("Complemento de Registro (Zeros)", 22, 23,
     "Preenchimento fixo com zeros, sem uso."),
    ("Número da Conta Corrente da Empresa", 24, 28,
     "Número da conta corrente da empresa na agência acima, sem dígito verificador."),
    ("Dígito Verificador da Agência/Conta (DAC)", 29, 29,
     "Dígito verificador de agência+conta, calculado pelo banco (algoritmo específico de cada instituição, normalmente módulo 11)."),
    ("Uso da Empresa (Complemento de Registro)", 30, 37,
     "Espaço reservado para uso livre da empresa; o banco apenas devolve o que foi enviado na Remessa (quando aplicável) ou preenche com brancos."),
    ("Uso da Empresa (Identificação do Título na Empresa)", 38, 62,
     "Identificador do título de uso interno da empresa (ex.: número de controle próprio), devolvido pelo banco tal como foi enviado na Remessa."),
    ("Nosso Número (Identificação do Título no Banco)", 63, 70,
     "Número que o banco atribuiu ao título no momento do registro - é a chave que o banco usa para identificar essa cobrança; deve ser citado em qualquer instrução futura sobre esse título."),
    ("Complemento de Registro (Brancos)", 71, 82,
     "Preenchimento com espaços em branco, sem uso."),
    ("Número da Carteira", 83, 85,
     "Código da carteira de cobrança contratada (ex.: cobrança simples, caucionada, descontada) - o significado exato dos códigos varia por banco."),
    ("Nosso Número (Identificação do Título no Banco, repeticao)", 86, 93,
     "Repetição do Nosso Número (posições 63-70), usada por alguns bancos como campo de conferência em outro formato/posição."),
    ("Dígito Verificador do Nosso Número (DAC)", 94, 94,
     "Dígito verificador calculado pelo banco sobre o Nosso Número, para validar que ele não foi digitado errado. O algoritmo (geralmente módulo 11) é específico de cada banco."),
    ("Complemento de Registro (Brancos)", 95, 107,
     "Preenchimento com espaços em branco, sem uso."),
    ("Código da Carteira", 108, 108,
     "Identifica o tipo de carteira de cobrança de forma resumida (1 posição) - ex.: '1' Simples, '2' Vinculada/Caucionada, '3' Descontada; a tabela exata é do banco emissor."),
    ("Código da Ocorrência (ver OCORRENCIA_CODES)", 109, 110,
     "Código de 2 dígitos que informa o que aconteceu com o título nesse retorno (ex.: '06' Liquidação Normal, '02' Entrada Confirmada) - ver a tabela de ocorrências do banco, em OCORRENCIA_CODES."),
    ("Data da Ocorrência no Banco (DDMMAA)", 111, 116,
     "Data em que o evento acima (ocorrência) foi processado pelo banco."),
    ("Número do Documento (Número do Título dado pela Empresa)", 117, 126,
     "Número/identificador do título (nota fiscal, fatura etc.) definido pela própria empresa no momento do envio, devolvido aqui para conferência."),
    ("Nosso Número (Confirmação do Número do Título no Banco)", 127, 134,
     "Nova confirmação do Nosso Número do título, repetida pelo banco neste ponto do registro."),
    ("Complemento de Registro (Brancos)", 135, 146,
     "Preenchimento com espaços em branco, sem uso."),
    ("Data de Vencimento do Título (DDMMAA)", 147, 152,
     "Data de vencimento do título conforme cadastrada no banco (pode já refletir uma alteração de vencimento pedida pela empresa)."),
    ("Valor Nominal do Título", 153, 165,
     "Valor de face do título (o valor original do boleto), em centavos sem separador decimal - os 2 últimos dígitos são os centavos."),
    ("Código do Banco Cobrador na Câmara de Compensação", 166, 168,
     "Código do banco que efetivamente recebeu o pagamento, quando diferente do banco emissor do arquivo (pagamento em outra rede/compensação)."),
    ("Agência Cobradora (Agência de Liquidação/Baixa)", 169, 172,
     "Agência que recebeu/processou o pagamento do título."),
    ("Dígito Verificador da Agência Cobradora (DAC)", 173, 173,
     "Dígito verificador calculado sobre a agência cobradora acima."),
    ("Espécie do Título", 174, 175,
     "Código que indica o tipo de documento de cobrança (ex.: duplicata mercantil, nota promissória, recibo) - ver a tabela de espécies do banco emissor."),
    ("Tarifa de Cobrança (Valor da Despesa de Cobrança)", 176, 188,
     "Valor cobrado pelo banco como tarifa/despesa de cobrança sobre esse título, em centavos."),
    ("Complemento de Registro (Brancos)", 189, 214,
     "Preenchimento com espaços em branco, sem uso."),
    ("Valor do IOF a ser Recolhido (Notas de Seguro)", 215, 227,
     "Valor de IOF a recolher, aplicável apenas quando a espécie do título é Nota de Seguro; nos demais casos vem zerado."),
    ("Valor do Abatimento Concedido", 228, 240,
     "Valor de abatimento (redução direta do valor do título) concedido pela empresa e processado pelo banco, em centavos."),
    ("Valor do Desconto Concedido", 241, 253,
     "Valor de desconto por pagamento antecipado efetivamente concedido ao pagador, em centavos."),
    ("Valor Principal (Valor Lançado em Conta Corrente/Valor Pago)", 254, 266,
     "Valor efetivamente pago pelo sacado e lançado na conta da empresa (pode ser diferente do valor nominal por causa de desconto, abatimento, juros ou pagamento parcial)."),
    ("Valor de Juros de Mora e Multa Recebidos", 267, 279,
     "Valor de juros de mora e/ou multa por atraso, efetivamente recebido junto com o pagamento."),
    ("Valor de Outros Créditos", 280, 292,
     "Outros valores creditados relacionados a esse título que não se encaixam nas categorias acima; uso específico de cada banco."),
    ("Indicador de Boleto DDA", 293, 293,
     "Indica se o título está registrado no DDA - Débito Direto Autorizado (sistema da CIP que centraliza boletos): '1' título em DDA, outro valor indica boleto normal."),
    ("Complemento de Registro (Brancos)", 294, 295,
     "Preenchimento com espaços em branco, sem uso."),
    ("Data de Crédito desta Liquidação (DDMMAA)", 296, 301,
     "Data em que o valor pago será (ou foi) disponibilizado na conta da empresa."),
    ("Código da Instrução Cancelada", 302, 305,
     "Quando a ocorrência informada se refere ao cancelamento de uma instrução anterior, aqui vem o código dessa instrução cancelada."),
    ("Complemento de Registro (Brancos)", 306, 311,
     "Preenchimento com espaços em branco, sem uso."),
    ("Complemento de Registro (Zeros)", 312, 324,
     "Preenchimento fixo com zeros, sem uso."),
    ("Nome do Pagador (Sacado)", 325, 354,
     "Nome (ou razão social) de quem deve pagar o título."),
    ("Complemento de Registro (Brancos)", 355, 377,
     "Preenchimento com espaços em branco, sem uso."),
    ("Motivos das Ocorrências / Mensagem Informativa (até 4 codigos de erro)", 378, 385,
     "Até 4 códigos de 2 dígitos que detalham o motivo de uma rejeição/instrução não aceita (ex.: título não encontrado, valor inválido) - a tabela de motivos é específica de cada banco."),
    ("Complemento de Registro (Brancos)", 386, 392,
     "Preenchimento com espaços em branco, sem uso."),
    ("Código de Liquidação (meio pelo qual o titulo foi liquidado)", 393, 394,
     "Código que indica o canal usado para o pagamento (ex.: casa lotérica, internet banking, compensação eletrônica) - a tabela de códigos varia por banco."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial dessa linha dentro do arquivo (o Header conta como 1, o primeiro Detalhe como 2, e assim por diante)."),
]

# ---------------------------------------------------------------------------
# 5. Detalhe (Registro tipo 1) - Arquivo de REMESSA (empresa -> banco)
# ---------------------------------------------------------------------------

DETAIL_REMESSA_FIELDS = [
    ("Identificação do Registro (1 = Detalhe/Transação)", 1, 1,
     "Identifica esta linha como um registro de Detalhe (um título). Deve ser sempre '1'."),
    ("Código de Inscrição da Empresa (01=CPF, 02=CNPJ)", 2, 3,
     "Indica o tipo de documento da empresa cedente informado a seguir: '01' para CPF, '02' para CNPJ."),
    ("Número de Inscrição da Empresa (CPF/CNPJ)", 4, 17,
     "CPF ou CNPJ da empresa cedente, alinhado à direita com zeros à esquerda."),
    ("Agência Mantenedora da Conta", 18, 21,
     "Agência bancária da conta da empresa usada nessa cobrança."),
    ("Complemento de Registro (Zeros)", 22, 23,
     "Preenchimento fixo com zeros, sem uso."),
    ("Número da Conta Corrente da Empresa", 24, 28,
     "Número da conta corrente da empresa na agência acima, sem dígito verificador."),
    ("Dígito Verificador da Agência/Conta (DAC)", 29, 29,
     "Dígito verificador de agência+conta, calculado pelo banco (algoritmo específico de cada instituição, normalmente módulo 11)."),
    ("Complemento de Registro (Brancos)", 30, 33,
     "Preenchimento com espaços em branco, sem uso."),
    ("Código da Instrução/Alegação a ser Cancelada", 34, 37,
     "Preenchido apenas quando a Identificação da Ocorrência (posições 109-110) pede o cancelamento de uma instrução anterior - código da instrução a cancelar."),
    ("Uso da Empresa (Identificação do Título na Empresa)", 38, 62,
     "Identificador do título de uso interno/livre da empresa (ex.: número de controle próprio); o banco apenas armazena e devolve esse valor no retorno."),
    ("Nosso Número (Identificação do Título no Banco)", 63, 70,
     "Número que identifica o título perante o banco. Se a empresa ainda não tiver um Nosso Número, alguns bancos aceitam esse campo em branco/zerado para que o próprio banco gere o número no registro do título."),
    ("Quantidade de Moeda Variável", 71, 83,
     "Usado apenas quando o título é indexado a uma moeda diferente do Real (ex.: dólar, UFIR); informa a quantidade dessa moeda equivalente ao valor do título. Fica zerado para títulos em Real."),
    ("Número da Carteira no Banco", 84, 86,
     "Código da carteira de cobrança contratada com o banco para esse título (ex.: cobrança simples, caucionada, descontada)."),
    ("Uso do Banco (Identificação da Operação no Banco)", 87, 107,
     "Espaço reservado para uso interno do banco; a empresa normalmente deixa em branco no envio."),
    ("Código da Carteira", 108, 108,
     "Identifica o tipo de carteira de cobrança de forma resumida (1 posição); a tabela exata de códigos é do banco emissor."),
    ("Identificação da Ocorrência (codigo de instrucao/comando)", 109, 110,
     "Código de 2 dígitos com a instrução que a empresa está enviando ao banco para esse título (ex.: '01' Entrada de Título, '02' Pedido de Baixa, '06' Alteração de Vencimento) - ver a tabela de instruções do banco emissor."),
    ("Número do Documento (Número do Título/Duplicata/NP dado pela Empresa)", 111, 120,
     "Número do título (nota fiscal, duplicata, fatura etc.) definido pela própria empresa; aparece novamente no arquivo de retorno para conferência."),
    ("Data de Vencimento do Título (DDMMAA)", 121, 126,
     "Data de vencimento do título que a empresa está cadastrando/alterando no banco."),
    ("Valor Nominal do Título", 127, 139,
     "Valor de face do título (o valor original do boleto), em centavos sem separador decimal."),
    ("Código do Banco Cobrador na Câmara de Compensação", 140, 142,
     "Preenchido quando o título pode ser pago em outro banco (cobrança interbancária); código desse banco cobrador."),
    ("Agência Cobradora (definida pelo CEP do Sacado)", 143, 147,
     "Agência cobradora sugerida com base no CEP do pagador, usada em cobrança interbancária/compartilhada."),
    ("Espécie do Título", 148, 149,
     "Código do tipo de documento de cobrança (ex.: duplicata mercantil, nota promissória, recibo) - ver a tabela de espécies do banco emissor."),
    ("Identificação de Título Aceito ou Não Aceito (A/N)", 150, 150,
     "Indica se o sacado já aceitou formalmente o título: 'A' Aceito, 'N' Não aceito."),
    ("Data de Emissão do Título (DDMMAA)", 151, 156,
     "Data em que o título (nota fiscal/duplicata) foi emitido pela empresa."),
    ("1a Instrução de Cobrança", 157, 158,
     "Primeira instrução automática que o banco deve aplicar ao título (ex.: protestar após X dias de atraso) - os códigos são definidos por cada banco."),
    ("2a Instrução de Cobrança", 159, 160,
     "Segunda instrução automática, complementar à primeira (ex.: não cobrar juros/multa) - os códigos são definidos por cada banco."),
    ("Valor de Mora por Dia de Atraso (Juros de 1 Dia)", 161, 173,
     "Valor de juros de mora cobrado por 1 dia de atraso após o vencimento, em centavos; o banco multiplica esse valor pelos dias corridos de atraso."),
    ("Data Limite para Concessao de Desconto (DDMMAA)", 174, 179,
     "Data até a qual o sacado tem direito ao desconto por pagamento antecipado informado abaixo."),
    ("Valor do Desconto a ser Concedido", 180, 192,
     "Valor do desconto concedido caso o sacado pague até a data limite acima, em centavos."),
    ("Valor do IOF Recolhido (Notas de Seguro)", 193, 205,
     "Valor de IOF a recolher, aplicável apenas quando a espécie do título é Nota de Seguro."),
    ("Valor do Abatimento a ser Concedido", 206, 218,
     "Valor de abatimento (redução direta do valor do título, sem relação com prazo de pagamento) a ser concedido pelo banco, em centavos."),
    ("Código de Inscrição do Sacado (01=CPF, 02=CNPJ)", 219, 220,
     "Indica o tipo de documento do pagador informado a seguir: '01' para CPF, '02' para CNPJ."),
    ("Número de Inscrição do Sacado (CPF/CNPJ)", 221, 234,
     "CPF ou CNPJ do pagador (sacado), alinhado à direita com zeros à esquerda."),
    ("Nome do Sacado (Pagador)", 235, 264,
     "Nome (ou razão social) de quem deve pagar o título."),
    ("Complemento de Registro (Brancos)", 265, 274,
     "Preenchimento com espaços em branco, sem uso."),
    ("Endereço do Sacado (Logradouro, Número e Complemento)", 275, 314,
     "Endereço completo do pagador, usado para impressão do boleto e eventual protesto/negativação."),
    ("Bairro do Sacado", 315, 326,
     "Bairro do endereço do pagador."),
    ("CEP do Sacado", 327, 334,
     "CEP do endereço do pagador (8 dígitos, sem hífen)."),
    ("Cidade do Sacado", 335, 349,
     "Cidade do endereço do pagador."),
    ("UF (Estado) do Sacado", 350, 351,
     "Sigla do estado (UF) do endereço do pagador."),
    ("Nome do Sacador/Avalista", 352, 381,
     "Nome de quem avaliza/garante o título (fiador), quando houver; campo opcional."),
    ("Complemento de Registro (Brancos)", 382, 385,
     "Preenchimento com espaços em branco, sem uso."),
    ("Data da Mora (DDMMAA)", 386, 391,
     "Data a partir da qual o cálculo de juros de mora passa a valer, quando diferente da data de vencimento."),
    ("Prazo (Quantidade de Dias para Protesto/Negativação)", 392, 393,
     "Quantidade de dias de atraso após os quais o banco deve protestar/negativar o título automaticamente, se essa instrução tiver sido pedida."),
    ("Complemento de Registro (Brancos)", 394, 394,
     "Preenchimento com espaço em branco, sem uso."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial dessa linha dentro do arquivo (o Header conta como 1, o primeiro Detalhe como 2, e assim por diante)."),
]

# ---------------------------------------------------------------------------
# 6. Occurrence codes used in the "Código de Ocorrência" field of Retorno
#    detail records (position 109-110 above).
# ---------------------------------------------------------------------------

OCORRENCIA_CODES = {
    "02": "Entrada Confirmada (com possibilidade de mensagem)",
    "03": "Entrada Rejeitada",
    "04": "Alteração de Dados - Nova Entrada ou Alteração/Exclusão de Dados Acatada",
    "05": "Alteração de Dados - Baixa",
    "06": "Liquidação Normal",
    "07": "Liquidação Parcial - Cobrança Inteligente (B2B)",
    "08": "Liquidação em Cartório",
    "09": "Baixa Simples",
    "10": "Baixa por Ter Sido Liquidado",
    "11": "Título em Ser (somente no retorno mensal)",
    "12": "Abatimento Concedido",
    "13": "Abatimento Cancelado",
    "14": "Vencimento Alterado",
    "15": "Baixas Rejeitadas",
    "16": "Instruções Rejeitadas",
    "17": "Alteração/Exclusão de Dados Rejeitados",
    "18": "Cobrança Contratual - Instruções/Alterações Rejeitadas/Pendentes",
    "19": "Confirma Recebimento de Instrução de Protesto",
    "20": "Confirma Recebimento de Instrução de Sustação de Protesto/Tarifa",
    "21": "Confirma Recebimento de Instrução de Não Protestar",
    "23": "Título Enviado a Cartório/Tarifa",
    "24": "Instrução de Protesto Rejeitada/Sustada/Pendente",
    "25": "Alegações do Pagador",
    "26": "Tarifa de Aviso de Cobrança",
    "27": "Tarifa de Extrato de Posição",
    "28": "Tarifa de Relação das Liquidações",
    "29": "Tarifa de Manutenção de Títulos Vencidos",
    "30": "Débito Mensal de Tarifas (para Entradas e Baixas)",
    "32": "Baixa por Ter Sido Protestado",
    "33": "Custas de Protesto",
    "34": "Custas de Sustação",
    "35": "Custas de Cartório Distribuidor",
    "36": "Custas de Edital",
    "37": "Tarifa de Emissão de Boleto/Tarifa de Envio de Duplicata",
    "38": "Tarifa de Instrução",
    "39": "Tarifa de Ocorrências",
    "40": "Tarifa Mensal de Emissão de Boleto/Envio de Duplicata",
    "41": "Débito Mensal de Tarifas - Extrato de Posição",
    "42": "Débito Mensal de Tarifas - Outras Instruções",
    "43": "Débito Mensal de Tarifas - Manutenção de Títulos Vencidos",
    "44": "Débito Mensal de Tarifas - Outras Ocorrências",
    "45": "Débito Mensal de Tarifas - Protesto",
    "46": "Débito Mensal de Tarifas - Sustação de Protesto",
    "47": "Baixa com Transferência para Desconto",
    "48": "Custas de Sustação Judicial",
    "51": "Tarifa Mensal Referente a Entradas em Bancos Correspondentes na Carteira",
    "52": "Tarifa Mensal de Baixas na Carteira",
    "53": "Tarifa Mensal de Baixas em Bancos Correspondentes na Carteira",
    "54": "Tarifa Mensal de Liquidações na Carteira",
    "55": "Tarifa Mensal de Liquidações em Bancos Correspondentes na Carteira",
    "56": "Custas de Irregularidade",
    "57": "Instrução Cancelada",
    "59": "Baixa por Crédito em Conta Corrente via SISPAG",
    "60": "Entrada Rejeitada - Carnê",
    "61": "Tarifa de Emissão de Aviso de Movimentação de Títulos",
    "62": "Débito Mensal de Tarifa - Aviso de Movimentação de Títulos",
    "63": "Título Sustado Judicialmente",
    "64": "Entrada Confirmada com Rateio de Crédito",
    "65": "Pagamento com Cheque - Aguardando Compensação",
    "69": "Cheque Devolvido",
    "71": "Entrada Registrada, Aguardando Avaliação",
    "72": "Baixa por Crédito em Conta Corrente via SISPAG sem Título Correspondente",
    "73": "Confirmação de Entrada na Cobrança Simples - Entrada Não Aceita na Cobrança Contratual",
    "74": "Instrução de Negativação Expressa Rejeitada",
    "75": "Confirmação de Recebimento de Instrução de Entrada em Negativação Expressa",
    "76": "Cheque Compensado",
    "77": "Confirmação de Recebimento de Instrução de Exclusão de Entrada em Negativação Expressa",
    "78": "Confirmação de Recebimento de Instrução de Cancelamento de Negativação Expressa",
    "79": "Negativação Expressa Informacional",
    "80": "Confirmação de Entrada em Negativação Expressa - Tarifa",
    "82": "Confirmação do Cancelamento de Negativação Expressa - Tarifa",
    "83": "Confirmação de Exclusão de Entrada em Negativação Expressa por Liquidação - Tarifa",
    "85": "Tarifa por Boleto (até 3 envios) - Cobrança Ativa Eletronica",
    "86": "Tarifa de E-mail - Cobrança Ativa Eletronica",
    "87": "Tarifa de SMS - Cobrança Ativa Eletronica",
    "88": "Tarifa Mensal por Boleto (até 3 envios) - Cobrança Ativa Eletronica",
    "89": "Tarifa Mensal de E-mail - Cobrança Ativa Eletronica",
    "90": "Tarifa Mensal de SMS - Cobrança Ativa Eletronica",
    "91": "Tarifa Mensal de Exclusão de Entrada de Negativação Expressa",
    "92": "Tarifa Mensal de Cancelamento de Negativação Expressa",
    "93": "Tarifa Mensal de Exclusão de Negativação Expressa por Liquidação",
}


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
    _validate_contiguous(HEADER_FIELDS, "HEADER_FIELDS")
    _validate_contiguous(TRAILER_FIELDS, "TRAILER_FIELDS")
    _validate_contiguous(DETAIL_RETORNO_FIELDS, "DETAIL_RETORNO_FIELDS")
    _validate_contiguous(DETAIL_REMESSA_FIELDS, "DETAIL_REMESSA_FIELDS")
    print("All field layouts are contiguous and cover positions 1-400.")
    print("BANK_NAMES: %d entries" % len(BANK_NAMES))
    print("HEADER_FIELDS: %d fields" % len(HEADER_FIELDS))
    print("TRAILER_FIELDS: %d fields" % len(TRAILER_FIELDS))
    print("DETAIL_RETORNO_FIELDS: %d fields" % len(DETAIL_RETORNO_FIELDS))
    print("DETAIL_REMESSA_FIELDS: %d fields" % len(DETAIL_REMESSA_FIELDS))
    print("OCORRENCIA_CODES: %d entries" % len(OCORRENCIA_CODES))
