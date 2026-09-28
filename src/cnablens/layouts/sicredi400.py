# -*- coding: utf-8 -*-
"""
CNAB400 Sicredi - field layout reference data.

Unlike most bancos, o Sicredi NÃO usa o layout "genérico" de cobrança CNAB400
(o mesmo que Itaú/BB/Bradesco/Caixa etc. compartilham, representado em
`cnab400_layout.py`). O Sicredi define seu próprio conjunto de campos/posições
para Header, Detalhe e Trailer, tanto na Remessa quanto no Retorno - por isso
este módulo existe separadamente.

Fonte usada (acessada 2026-08-31):
  Sicredi - "Manual CNAB 400 - Cobrança", Versão 2.4 (outubro/2022) - manual
  oficial e mais atual publicado pelo Sicredi.
  https://www.sicredi.com.br/media/produtos/filer_public/2022/09/26/manual_cnab_400_2-4_260922.pdf
  -> Fonte única para HEADER_REMESSA_FIELDS, DETAIL_REMESSA_FIELDS,
     HEADER_RETORNO_FIELDS, DETAIL_RETORNO_FIELDS, TRAILER_FIELDS e
     OCORRENCIA_CODES abaixo (seções 4.4, 4.5, 7.2, 8.1, 8.2, 8.8, 9.1, 9.2 e
     9.4 do manual). As descrições de cada campo (4a coluna das tabelas)
     resumem o texto da coluna "Conteúdo/Descrição" do manual.

Notas sobre o layout do Sicredi (posições que mais chamam atenção por serem
diferentes do padrão FEBRABAN genérico):
  - O Header do Sicredi não tem campo de "Nome da Empresa/Cedente" (esse
    trecho é apenas Filler/branco); em vez disso ele identifica o cedente
    pelo "Código do beneficiário/cedente" (posições 27-31) e pelo CPF/CNPJ
    (32-45), cadastrados previamente na Cooperativa.
  - A data de geração do Header vem em AAAAMMDD (8 posições, 95-102), não em
    DDMMAA (6 posições) como no padrão genérico - `cnab400_reader.py` já
    trata essa variação de formato automaticamente.
  - O "Nosso Número" do Sicredi tem formato próprio "AA/BXXXXX-D" (seção 4.4
    do manual): AA = ano, B = byte de geração, XXXXX = sequencial livre,
    D = dígito verificador por módulo 11 (seção 4.5). No Detalhe de Remessa
    (9 posições, 48-56) esse formato é representado aqui já quebrado em 4
    campos - um por componente - em vez de um único campo de 9 posições,
    para deixar cada parte explícita. No Detalhe de Retorno o campo
    equivalente tem 15 posições ("sem edição") e o manual não documenta uma
    subdivisão própria para esse tamanho maior, por isso ali ele permanece
    como um único campo.
  - O Detalhe de Remessa tem campos específicos do Sicredi sem equivalente
    direto no layout genérico: Tipo de Cobrança, Tipo de Carteira, Tipo de
    Impressão, Tipo de Boleto (Híbrido/QRCode Pix), Tipo de Moeda, Tipo de
    Desconto/Juros (valor x percentual), dados de carnê (parcela/total) e
    campos de Beneficiário Final (posições 340-394).
  - A Tabela de Ocorrências (OCORRENCIA_CODES) do Sicredi usa descrições e um
    subconjunto de códigos próprios (ex.: "07 - Intenção de pagamento",
    "17 - Liquidação após baixa") diferentes da tabela genérica FEBRABAN.
  - A "Tabela de Motivos" (item 7.3 do manual, códigos de 2 dígitos/letras
    usados no campo "Motivos da Ocorrência" do Retorno) não está transcrita
    aqui por ser extensa (mais de 80 códigos); o campo é exibido com o valor
    bruto e uma observação para consulta ao manual.
"""

# ---------------------------------------------------------------------------
# 1. Header (Registro tipo 0) - Arquivo de REMESSA (empresa -> Sicredi)
# ---------------------------------------------------------------------------

HEADER_REMESSA_FIELDS = [
    ("Identificação do Registro (0 = Header)", 1, 1,
     "Marca o início do arquivo. Deve ser sempre o caractere '0'."),
    ("Identificação do Arquivo (1 = Remessa)", 2, 2,
     "Indica que este é um arquivo de Remessa (a empresa envia títulos ao Sicredi). Deve ser sempre '1'."),
    ("Literal Remessa (\"REMESSA\")", 3, 9,
     "Texto fixo 'REMESSA', usado pelo Sicredi para validar o arquivo."),
    ("Código do Serviço de Cobrança", 10, 11,
     "Código do serviço do arquivo; para cobrança o Sicredi usa o valor '1'."),
    ("Literal Cobrança (\"COBRANCA\")", 12, 19,
     "Texto fixo 'COBRANCA'."),
    ("Uso Reservado/Sicredi (Filler)", 20, 26,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Código do Beneficiário/Cedente (cadastrado na Cooperativa)", 27, 31,
     "Código numérico que a Cooperativa/Agência atribui ao beneficiário (cedente) no cadastro, informado pelo Sicredi antes de iniciar a troca de arquivos; também é usado no nome dos arquivos de remessa/retorno."),
    ("CPF/CNPJ do Beneficiário/Cedente", 32, 45,
     "CPF ou CNPJ do beneficiário/cedente, alinhado à direita com zeros à esquerda, sem pontuação."),
    ("Uso Reservado/Sicredi (Filler)", 46, 76,
     "Não usado - deixar em branco (sem preenchimento). Diferente do FEBRABAN genérico, o Header do Sicredi não tem campo de nome da empresa."),
    ("Número do Sicredi (748)", 77, 79,
     "Código do Sicredi na Câmara de Compensação. Deve ser sempre '748'."),
    ("Literal Sicredi (\"SICREDI\")", 80, 94,
     "Texto fixo 'SICREDI'."),
    ("Data de Geração do Arquivo (AAAAMMDD)", 95, 102,
     "Data em que o arquivo de remessa foi gerado, no formato ano-mês-dia (AAAAMMDD, 8 dígitos) - diferente do padrão DDMMAA de 6 dígitos usado por outros bancos."),
    ("Uso Reservado/Sicredi (Filler)", 103, 110,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Número Sequencial da Remessa", 111, 117,
     "Número sequencial do arquivo de remessa: o primeiro arquivo enviado ao Sicredi deve conter '0000001', o segundo '0000002' e assim sucessivamente."),
    ("Uso Reservado/Sicredi (Filler)", 118, 390,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Versão do Sistema (\"2.00\")", 391, 394,
     "Versão do layout utilizada, no formato 'X.XX' com o ponto decimal incluído. Na versão atual do manual: '2.00'."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial da linha dentro do arquivo (o Header é a linha 1), alinhado à direita com zeros à esquerda."),
]

# ---------------------------------------------------------------------------
# 2. Detalhe (Registro tipo 1) - Arquivo de REMESSA (empresa -> Sicredi)
# ---------------------------------------------------------------------------

DETAIL_REMESSA_FIELDS = [
    ("Identificação do Registro (1 = Detalhe/Transação)", 1, 1,
     "Identifica esta linha como um registro de Detalhe (um título). Deve ser sempre '1'."),
    ("Tipo de Cobrança (A = Sicredi com Registro)", 2, 2,
     "Define a modalidade de cobrança do título. Atualmente o Sicredi só opera com 'A' (Sicredi com Registro)."),
    ("Tipo de Carteira (A = Simples)", 3, 3,
     "Define a carteira de cobrança do título. Atualmente o Sicredi só opera com 'A' (Simples)."),
    ("Tipo de Impressão (A = Normal, B = Carnê)", 4, 4,
     "Define o formato de impressão do boleto: 'A' para boleto avulso normal, 'B' para carnê (várias parcelas)."),
    ("Uso Reservado/Sicredi (Filler)", 5, 5,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Tipo de Boleto (H = Híbrido/QRCode Pix)", 6, 6,
     "Preencher com 'H' para gerar um boleto híbrido, com QRCode Pix além do código de barras tradicional; deixar em branco para um boleto tradicional."),
    ("Uso Reservado/Sicredi (Filler)", 7, 16,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Tipo de Moeda (A = Real)", 17, 17,
     "Moeda do título. Atualmente o Sicredi só opera com 'A' (Real)."),
    ("Tipo de Desconto (A = Valor Monetário, B = Percentual)", 18, 18,
     "Define se o campo de desconto por antecipação (posições 83-92) deve ser interpretado como valor em reais ('A') ou como percentual ('B')."),
    ("Tipo de Juros (A = Valor Monetário, B = Percentual)", 19, 19,
     "Define se o campo de juros por dia de atraso (posições 161-173) deve ser interpretado como valor em reais ('A') ou como percentual ('B')."),
    ("Uso Reservado/Sicredi (Filler)", 20, 47,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Nosso Número [Ano - AA]", 48, 49,
     "Dois primeiros dígitos do Nosso Número (formato Sicredi 'AA/BXXXXX-D'): ano de referência do título, que pode ser diferente do ano corrente."),
    ("Nosso Número [Byte de Geração - B]", 50, 50,
     "Terceiro dígito do Nosso Número: identifica quem gerou o número. Só pode ser '1' quando o boleto for pré-impresso pela Cooperativa; nos demais casos, o beneficiário escolhe um dígito de 0 a 9 para não duplicar números já usados."),
    ("Nosso Número [Número Sequencial - XXXXX]", 51, 55,
     "Cinco dígitos seguintes do Nosso Número: sequencial livre (de 00000 a 99999) controlado pelo próprio beneficiário - não pode se repetir, ou seja, não pode haver dois títulos com o mesmo Nosso Número."),
    ("Nosso Número [Dígito Verificador - D, módulo 11]", 56, 56,
     "Dígito verificador do Nosso Número, calculado por módulo 11 (manual, seção 4.5) sobre a sequência Cooperativa/Agência + Posto + Beneficiário + Ano + Byte + Sequencial: multiplica-se cada dígito dessa sequência, da direita para a esquerda, pelos pesos 2,3,4,5,6,7,8,9 (repetindo o ciclo), soma-se todos os resultados e divide-se a soma por 11; o DV é 11 menos o resto dessa divisão - se o resultado for 10 ou 11, o DV vira 0. Se a impressão for feita pelo Sicredi (Tipo de Impressão = A), este campo pode ficar em branco que o banco gera o número; se for pelo beneficiário (B), ele deve calcular e preencher."),
    ("Uso Reservado/Sicredi (Filler)", 57, 62,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Data de Instrução (AAAAMMDD)", 63, 70,
     "Data em que a instrução deste registro (cadastro do título ou comando enviado) foi gerada pela empresa, no formato AAAAMMDD."),
    ("Campo Alterado (só com Instrução \"31\": A/B/C/D/E)", 71, 71,
     "Só é usado quando a Instrução (posições 109-110) for '31' - Alteração de outros dados: informa QUAL dado está sendo alterado ('A' Desconto, 'B' Juros por dia, 'C' Desconto por antecipação, 'D' Data limite para desconto, 'E' Cancelamento de protesto automático). Nos demais casos, deixar em branco."),
    ("Postagem do Título (S = Sicredi, N = Beneficiário/Cedente)", 72, 72,
     "Define quem vai postar/enviar o boleto físico ao pagador: 'S' o próprio Sicredi cuida do envio, 'N' o beneficiário/cedente cuida do envio."),
    ("Uso Reservado/Sicredi (Filler)", 73, 73,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Impressão do Boleto (A = Sicredi, B = Beneficiário/Cedente)", 74, 74,
     "Define quem imprime o boleto: 'A' o Sicredi gera e imprime, 'B' o próprio beneficiário/cedente imprime seguindo o layout do manual. Se o beneficiário imprimir, ele também deve cuidar da postagem (o campo acima não pode ser 'S')."),
    ("Número da Parcela do Carnê", 75, 76,
     "Quando o Tipo de Impressão (posição 4) for 'B' (Carnê): número desta parcela dentro do carnê (ex.: 3 de 12). Nos demais casos, sem uso."),
    ("Número Total de Parcelas do Carnê", 77, 78,
     "Quando o Tipo de Impressão (posição 4) for 'B' (Carnê): quantidade total de parcelas do carnê. Nos demais casos, sem uso."),
    ("Uso Reservado/Sicredi (Filler)", 79, 82,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Valor/Percentual de Desconto por Dia de Antecipação", 83, 92,
     "Desconto concedido por dia de antecipação do pagamento, em reais ou percentual conforme o Tipo de Desconto (posição 18) - ex.: para 1% informar '0000000100', para R$ 0,50 informar '0000000050'. Preencher com zeros se não houver esse desconto."),
    ("Percentual de Multa por Pagamento em Atraso", 93, 96,
     "Percentual de multa aplicado sobre o valor do título em caso de atraso, sempre em percentual (ex.: 1% = '0100'). Preencher com zeros se não houver multa."),
    ("Uso Reservado/Sicredi (Filler)", 97, 108,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Instrução (código do comando a ser executado)", 109, 110,
     "Código de 2 dígitos com o comando que a empresa está enviando ao Sicredi para esse título: '01' Cadastro de Título, '02' Pedido de Baixa, '04' Concessão de Abatimento, '05' Cancelamento de Abatimento, '06' Alteração de Vencimento, '09' Pedido de Protesto, '18' Sustar Protesto e Baixar, '19' Sustar Protesto e Manter em Carteira, '31' Alteração de Outros Dados, '45' Incluir Negativação, '75' Excluir Negativação e Manter em Carteira, '76' Excluir Negativação e Baixar Título."),
    ("Seu Número (nº do documento/nota fiscal dado pela Empresa)", 111, 120,
     "Número do documento definido pela empresa (normalmente o número da nota fiscal). Não pode conter espaço em branco no meio - ex.: '123/4' em vez de '123 4'."),
    ("Data de Vencimento do Título (DDMMAA)", 121, 126,
     "Data de vencimento do título. Deve ser pelo menos 7 dias maior que a Data de Emissão (posições 151-156)."),
    ("Valor do Título", 127, 139,
     "Valor de face do título (o valor original do boleto), alinhado à direita com zeros à esquerda; os 2 últimos dígitos são os centavos."),
    ("Uso Reservado/Sicredi (Filler)", 140, 141,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Uso Reservado/Sicredi (Filler)", 142, 148,
     "Não usado - deixar em branco (sem preenchimento)."),
    ("Espécie de Documento do Título", 149, 149,
     "Código de 1 letra do tipo de documento: A Duplicata Mercantil, B Duplicata Rural, C Nota Promissória, D Nota Promissória Rural, E Nota de Seguros, G Recibo, H Letra de Câmbio, I Nota de Débito, J Duplicata de Serviço, K Outros, O Boleto Proposta (não permite boleto Híbrido)."),
    ("Aceite do Título (S/N)", 150, 150,
     "Indica se o título já foi formalmente aceito pelo pagador: 'S' Sim, 'N' Não."),
    ("Data de Emissão do Título (DDMMAA)", 151, 156,
     "Data de emissão do título/nota fiscal. Deve ser pelo menos 7 dias menor que a Data de Vencimento (posições 121-126)."),
    ("Instrução de Protesto Automático (00/06)", 157, 158,
     "Define se o Sicredi deve protestar automaticamente o título em cartório após vencido: '00' não protestar, '06' protestar automaticamente."),
    ("Número de Dias para Protesto Automático", 159, 160,
     "Quantos dias após o vencimento o protesto automático deve ocorrer (só relevante se a instrução acima for '06'); mínimo '03', máximo '99'. Com '03' ou '04' dias a contagem é em dias úteis; a partir de '05' dias, em dias corridos. Sem protesto automático, preencher com '00'."),
    ("Valor/Percentual de Juros por Dia de Atraso", 161, 173,
     "Juros cobrados por dia de atraso, em reais ou percentual conforme o Tipo de Juros (posição 19) - ex.: para 1% informar '0000000000100', para R$ 0,50 informar '0000000000050'. Preencher com zeros se não houver juros."),
    ("Data Limite para Concessão de Desconto (DDMMAA)", 174, 179,
     "Última data em que o pagador ainda tem direito ao desconto informado abaixo. Preencher com zeros se não houver desconto."),
    ("Valor/Percentual de Desconto a Conceder", 180, 192,
     "Desconto concedido caso o pagamento ocorra até a Data Limite acima, em reais ou percentual conforme o Tipo de Desconto (posição 18). Preencher com zeros se não houver desconto."),
    ("Instrução de Negativação Automática (00/06)", 193, 194,
     "Define se o Sicredi deve negativar automaticamente o CPF/CNPJ do pagador (nos birôs de crédito) após vencido: '00' não negativar, '06' negativar automaticamente. Só disponível para beneficiário Pessoa Jurídica, e não pode ser combinada com protesto automático no mesmo título."),
    ("Número de Dias para Negativação Automática", 195, 196,
     "Quantos dias após o vencimento a negativação automática deve ocorrer; mínimo '03', máximo '99'. Com '03' ou '04' dias a contagem é em dias úteis; a partir de '05' dias, em dias corridos."),
    ("Uso Reservado/Sicredi (Filler)", 197, 205,
     "Não usado - preencher com zeros."),
    ("Valor do Abatimento a Conceder", 206, 218,
     "Valor de abatimento (redução direta do valor do título) a conceder, alinhado à direita com zeros à esquerda. Preencher com zeros se não houver abatimento."),
    ("Tipo de Inscrição do Pagador/Sacado (1=CPF, 2=CNPJ)", 219, 219,
     "Indica o tipo de documento do pagador informado a seguir: '1' Pessoa Física (CPF), '2' Pessoa Jurídica (CNPJ)."),
    ("Uso Reservado/Sicredi (Filler)", 220, 220,
     "Não usado - preencher com zero."),
    ("CPF/CNPJ do Pagador/Sacado", 221, 234,
     "CPF ou CNPJ do pagador, alinhado à direita com zeros à esquerda, sem pontuação; deve ser um documento válido (verificado na homologação com o Sicredi)."),
    ("Nome do Pagador (Sacado)", 235, 274,
     "Nome (ou razão social) de quem deve pagar o título, sem acentuação ou caracteres especiais."),
    ("Endereço do Pagador", 275, 314,
     "Endereço completo do pagador, sem acentuação ou caracteres especiais, usado para impressão/envio do boleto."),
    ("Código do Pagador na Cooperativa Beneficiária", 315, 319,
     "Código do pagador já cadastrado no Sicredi, para quando o sistema da empresa não controla essa informação; preencher com zeros se não aplicável. Depois de cadastrado, o Sicredi devolve esse código no arquivo de retorno para reuso."),
    ("Uso Reservado/Sicredi (Filler)", 320, 325,
     "Não usado - preencher com zero."),
    ("Uso Reservado/Sicredi (Filler)", 326, 326,
     "Não usado - deixar em branco."),
    ("CEP do Pagador", 327, 334,
     "CEP do endereço do pagador (8 dígitos, sem hífen); é obrigatório e precisa ser um CEP válido."),
    ("Código do Pagador junto ao Cliente", 335, 339,
     "Código interno que a própria empresa usa para identificar esse pagador em seu sistema; preencher com zeros se não houver."),
    ("CPF/CNPJ do Beneficiário Final", 340, 353,
     "CPF ou CNPJ de um Beneficiário Final, quando o crédito do título deve ser repassado a um terceiro diferente do beneficiário/cedente do título. Deixar em branco quando não existir Beneficiário Final."),
    ("Nome do Beneficiário Final", 354, 394,
     "Nome do Beneficiário Final descrito acima. Deixar em branco quando não existir Beneficiário Final."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial dessa linha dentro do arquivo (o Header conta como 1, o primeiro Detalhe como 2, e assim por diante)."),
]

# ---------------------------------------------------------------------------
# 3. Header (Registro tipo 0) - Arquivo de RETORNO (Sicredi -> empresa)
# ---------------------------------------------------------------------------

HEADER_RETORNO_FIELDS = [
    ("Identificação do Registro (0 = Header)", 1, 1,
     "Marca o início do arquivo. Deve ser sempre o caractere '0'."),
    ("Identificação do Arquivo (2 = Retorno)", 2, 2,
     "Indica que este é um arquivo de Retorno (o Sicredi devolve o processamento à empresa). Deve ser sempre '2'."),
    ("Literal Retorno (\"RETORNO\")", 3, 9,
     "Texto fixo 'RETORNO', usado para validar o arquivo."),
    ("Código do Serviço de Cobrança", 10, 11,
     "Código do serviço do arquivo; para cobrança o Sicredi usa o valor '01'."),
    ("Literal Cobrança (\"COBRANCA\")", 12, 26,
     "Texto fixo 'COBRANCA'."),
    ("Código do Beneficiário/Cedente", 27, 31,
     "Código do beneficiário/cedente cadastrado na Cooperativa - o mesmo código usado nos arquivos de remessa."),
    ("CPF/CNPJ do Beneficiário/Cedente", 32, 45,
     "CPF ou CNPJ do beneficiário/cedente, alinhado à direita com zeros à esquerda."),
    ("Uso Reservado/Sicredi (Filler)", 46, 76,
     "Não usado - em branco."),
    ("Número do Sicredi (748)", 77, 79,
     "Código do Sicredi na Câmara de Compensação. Sempre '748'."),
    ("Literal (\"BANSICREDI\")", 80, 94,
     "Texto fixo 'BANSICREDI' (diferente do literal 'SICREDI' usado na Remessa)."),
    ("Data de Geração do Arquivo (AAAAMMDD)", 95, 102,
     "Data em que o Sicredi gerou este arquivo de retorno, no formato AAAAMMDD."),
    ("Uso Reservado/Sicredi (Filler)", 103, 110,
     "Não usado - em branco."),
    ("Número Sequencial do Retorno", 111, 117,
     "Número sequencial do arquivo de retorno, alinhado à direita com zeros à esquerda."),
    ("Uso Reservado/Sicredi (Filler)", 118, 389,
     "Não usado - em branco."),
    ("Versão do Sistema (\"99.99\")", 390, 394,
     "Versão do layout, com o ponto decimal incluído."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial da linha dentro do arquivo (o Header é a linha 1), alinhado à direita com zeros à esquerda."),
]

# ---------------------------------------------------------------------------
# 4. Detalhe (Registro tipo 1) - Arquivo de RETORNO (Sicredi -> empresa)
# ---------------------------------------------------------------------------

DETAIL_RETORNO_FIELDS = [
    ("Identificação do Registro (1 = Detalhe/Transação)", 1, 1,
     "Identifica esta linha como um registro de Detalhe (um título). Deve ser sempre '1'."),
    ("Tipo de Carteira (A/B/C/D - só na ocorrência 33/H4)", 2, 2,
     "Só vem preenchido quando a Ocorrência (posições 109-110) for '33' com motivo 'H4': informa a carteira do título - 'A' Simples, 'B' Caucionada, 'C' Descontada, 'D' Vinculada. Nos demais casos, vem em branco."),
    ("Uso Reservado/Sicredi (Filler)", 3, 13,
     "Não usado - em branco."),
    ("Tipo de Cobrança (A = Sicredi Cobrança com Registro)", 14, 14,
     "Modalidade de cobrança do título. Sempre 'A'."),
    ("Código do Pagador na Cooperativa do Beneficiário", 15, 19,
     "Quando o boleto foi impresso pelo Sicredi, é o código com que o pagador foi cadastrado internamente no Sicredi."),
    ("Código do Pagador junto ao Associado", 20, 24,
     "Devolve o código informado no arquivo de remessa no campo 'Código do Pagador junto ao Cliente', para conferência da empresa."),
    ("Boleto DDA (1 = Enviado à CIP/DDA, 2 = Normal)", 25, 25,
     "Indica se o título está registrado no DDA (Débito Direto Autorizado, sistema centralizado da CIP): '1' enviado à CIP/DDA, '2' boleto normal."),
    ("Uso Reservado/Sicredi (Filler)", 26, 47,
     "Não usado - em branco."),
    ("Nosso Número [Sicredi, sem edição]", 48, 62,
     "Nosso Número do título no Sicredi, no mesmo formato conceitual da Remessa (AA ano + B byte de geração + XXXXX sequencial + D dígito verificador por módulo 11), porém armazenado aqui com 15 posições em vez de 9 - o manual não detalha uma subdivisão própria para esse tamanho maior, por isso o campo aparece inteiro. Se o boleto foi impresso pelo Sicredi (Tipo de Impressão = A), vem com o número gerado pelo banco (ou o mesmo informado na remessa, se houver); se foi impresso pelo beneficiário (B), vem com o número que a própria empresa informou na remessa."),
    ("Uso Reservado/Sicredi (Filler)", 63, 108,
     "Não usado - em branco."),
    ("Código da Ocorrência (ver OCORRENCIA_CODES)", 109, 110,
     "Código de 2 dígitos que informa o que aconteceu com o título nesse retorno (ex.: '06' Liquidação Normal, '02' Entrada Confirmada) - ver a tabela de ocorrências do Sicredi, em OCORRENCIA_CODES."),
    ("Data da Ocorrência no Sicredi (DDMMAA)", 111, 116,
     "Data em que o evento acima foi processado pelo Sicredi."),
    ("Seu Número (nº do documento/nota fiscal enviado na Remessa)", 117, 126,
     "Devolve o número do documento (Seu Número) que a empresa enviou na Remessa, para conferência."),
    ("Cooperativa/Agência ou \"COMPE\" que Liquidou o Título", 127, 146,
     "Identifica onde o título foi pago: quando a liquidação ocorreu via compensação bancária (outro banco), traz a palavra 'COMPE'; quando ocorreu dentro da rede Sicredi, traz o número da cooperativa de crédito/agência e o posto que processou o pagamento."),
    ("Data de Vencimento do Título (DDMMAA)", 147, 152,
     "Data de vencimento do título conforme cadastrada no Sicredi (pode já refletir uma alteração de vencimento pedida pela empresa)."),
    ("Valor do Título", 153, 165,
     "Valor de face do título (valor original do boleto), alinhado à direita com zeros à esquerda."),
    ("Uso Reservado/Sicredi (Filler)", 166, 174,
     "Não usado - em branco."),
    ("Espécie de Documento do Título", 175, 175,
     "Devolve o código de espécie de documento informado na Remessa: A Duplicata Mercantil, B Duplicata Rural, C Nota Promissória, D Nota Promissória Rural, E Nota de Seguros, G Recibo, H Letra de Câmbio, I Nota de Débito, J Duplicata de Serviço, K Outros, O Boleto Proposta."),
    ("Despesas de Cobrança", 176, 188,
     "Valor de despesas/tarifas de cobrança debitadas sobre esse título, alinhado à direita com zeros à esquerda."),
    ("Despesas de Custas de Protesto", 189, 201,
     "Valor de custas de cartório cobradas quando o título foi protestado, alinhado à direita com zeros à esquerda."),
    ("Uso Reservado/Sicredi (Filler)", 202, 227,
     "Não usado - preenchido com zeros pelo Sicredi."),
    ("Valor do Abatimento Concedido", 228, 240,
     "Valor de abatimento efetivamente processado pelo Sicredi sobre esse título, alinhado à direita com zeros à esquerda."),
    ("Valor do Desconto Concedido", 241, 253,
     "Valor de desconto por pagamento antecipado efetivamente concedido ao pagador, alinhado à direita com zeros à esquerda."),
    ("Valor Efetivamente Pago pelo Sacado", 254, 266,
     "Valor que o pagador de fato pagou (pode diferir do valor do título por causa de desconto, abatimento, juros, multa ou pagamento parcial), alinhado à direita com zeros à esquerda."),
    ("Valor de Juros de Mora", 267, 279,
     "Valor de juros de mora por atraso efetivamente recebido junto com o pagamento, alinhado à direita com zeros à esquerda."),
    ("Valor de Multa", 280, 292,
     "Valor de multa por atraso efetivamente recebido junto com o pagamento, alinhado à direita com zeros à esquerda."),
    ("Uso Reservado/Sicredi (Filler)", 293, 294,
     "Não usado - em branco."),
    ("Confirmação do Pagador (A = Aceito, D = Desprezado - só na ocorrência 19)", 295, 295,
     "Só vem preenchido quando a Ocorrência for '19': informa se o pedido de protesto foi 'A' Aceito ou 'D' Desprezado (ignorado) pelo Sicredi."),
    ("Uso Reservado/Sicredi (Filler)", 296, 318,
     "Não usado - em branco."),
    ("Motivos da Ocorrência (pares de 2 dígitos - ver manual Sicredi 7.3)", 319, 328,
     "Até 5 códigos de 2 dígitos (ou letra+dígito) que detalham o motivo da ocorrência acima. O código '00' significa 'sem motivo específico'; os demais códigos (rejeições, pendências etc.) estão na Tabela de Motivos do manual do Sicredi (item 7.3), não reproduzida neste app - consulte o manual para decodificar valores diferentes de '00'."),
    ("Data Prevista para Lançamento na Conta Corrente (AAAAMMDD)", 329, 336,
     "Data em que o valor pago será (ou foi) disponibilizado na conta corrente da empresa, no formato AAAAMMDD."),
    ("Uso Reservado/Sicredi (Filler)", 337, 394,
     "Não usado - em branco."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial dessa linha dentro do arquivo (o Header conta como 1, o primeiro Detalhe como 2, e assim por diante)."),
]

# ---------------------------------------------------------------------------
# 5. Trailer (Registro tipo 9) - compartilhado entre Remessa e Retorno
# ---------------------------------------------------------------------------

TRAILER_FIELDS = [
    ("Identificação do Registro (9 = Trailer)", 1, 1,
     "Marca o fim do arquivo. Deve ser sempre o caractere '9'."),
    ("Identificação do Arquivo (1 = Remessa, 02 = Retorno)", 2, 2,
     "Repete o tipo de arquivo do Header: '1' em arquivos de Remessa, '02' em arquivos de Retorno."),
    ("Número do Sicredi (748)", 3, 5,
     "Código do Sicredi na Câmara de Compensação. Sempre '748'."),
    ("Código do Beneficiário/Cedente", 6, 10,
     "Repete o código do beneficiário/cedente informado no Header."),
    ("Uso Reservado/Sicredi (Filler)", 11, 394,
     "Não usado - em branco. O Trailer do CNAB400 de cobrança não carrega totais (diferente do CNAB240)."),
    ("Número Sequencial do Registro no Arquivo", 395, 400,
     "Número sequencial dessa linha (a última do arquivo) - deve ser igual à quantidade total de registros do arquivo (Header + Detalhes + Trailer)."),
]

# ---------------------------------------------------------------------------
# 6. Tabela de Ocorrências (campo "Código da Ocorrência" do Retorno, 109-110)
# ---------------------------------------------------------------------------

OCORRENCIA_CODES = {
    "02": "Entrada Confirmada",
    "03": "Entrada Rejeitada",
    "06": "Liquidação Normal",
    "07": "Intenção de Pagamento",
    "09": "Baixado Automaticamente via Arquivo",
    "10": "Baixado Conforme Instruções da Cooperativa",
    "12": "Abatimento Concedido",
    "13": "Abatimento Cancelado",
    "14": "Vencimento Alterado",
    "15": "Liquidação em Cartório",
    "17": "Liquidação Após Baixa",
    "19": "Confirmação de Recebimento de Instrução de Protesto",
    "20": "Confirmação de Recebimento de Instrução de Sustação de Protesto",
    "23": "Entrada de Título em Cartório",
    "24": "Entrada Rejeitada por CEP Irregular",
    "27": "Baixa Rejeitada",
    "28": "Tarifa",
    "29": "Rejeição do Pagador",
    "30": "Alteração Rejeitada",
    "32": "Instrução Rejeitada",
    "33": "Confirmação de Pedido de Alteração de Outros Dados",
    "34": "Retirado de Cartório e Manutenção em Carteira",
    "35": "Aceite do Pagador",
    "78": "Confirmação de Recebimento de Pedido de Negativação",
    "79": "Confirmação de Recebimento de Pedido de Exclusão de Negativação",
    "80": "Confirmação de Entrada de Negativação",
    "81": "Entrada de Negativação Rejeitada",
    "82": "Confirmação de Exclusão de Negativação",
    "83": "Exclusão de Negativação Rejeitada",
    "84": "Exclusão de Negativação por Outros Motivos",
    "85": "Ocorrência Informacional por Outros Motivos",
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
    _validate_contiguous(HEADER_REMESSA_FIELDS, "HEADER_REMESSA_FIELDS")
    _validate_contiguous(DETAIL_REMESSA_FIELDS, "DETAIL_REMESSA_FIELDS")
    _validate_contiguous(HEADER_RETORNO_FIELDS, "HEADER_RETORNO_FIELDS")
    _validate_contiguous(DETAIL_RETORNO_FIELDS, "DETAIL_RETORNO_FIELDS")
    _validate_contiguous(TRAILER_FIELDS, "TRAILER_FIELDS")
    print("All Sicredi field layouts are contiguous and cover positions 1-400.")
    print("OCORRENCIA_CODES: %d entries" % len(OCORRENCIA_CODES))
