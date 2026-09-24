# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versionamento
[SemVer](https://semver.org/lang/pt-BR/).

## [Não lançado]

## [0.2.0] - 2026-09-24

### Adicionado
- Santander CNAB400: módulo de layout (Header, Movimento tipo 1 e Trailer, remessa e retorno) com tabelas de código (#5)
- Santander CNAB400: reconhecer no leitor os registros tipo 8 (QR Code/PIX), 2/4/5/6/7 (mensagens) e o tipo 2 do retorno, com layout por tipo de registro (#6)
- Santander CNAB240: módulo de layout (Headers, Segmentos P, Q, R, S na remessa e T, U no retorno, Trailers) com tabelas de movimento e ocorrência (#7)
- Santander CNAB240: Segmentos Y-03 e Y-53 (remessa) e Y-03 e Y-04 (retorno) com sub-código do segmento Y (#8)
- Registrar os layouts Santander no seletor e na detecção automática pelo banco (033 e 353) (#9)
- Arquivos de exemplo fictícios e testes de leitura para remessa e retorno, 400 e 240, incluindo QR Code e segmento Y (#10)

## [0.1.0] - 2026-09-21

Primeira versão pública do **CNABLens**.

### Adicionado
- Leitura de arquivos **CNAB400** e **CNAB240** de cobrança (remessa e retorno), com detecção
  automática do formato pelo tamanho da linha.
- Layouts de campos: **CNAB400 FEBRABAN (padrão)**, **CNAB400 Sicredi**, **CNAB400 Sicoob** e
  **CNAB240 Sicoob** (segmentos P, Q, R, S, T e U), com seleção automática pelo banco do Header
  e troca manual sem reabrir o arquivo.
- Navegação por pasta, com filtro por extensão e coluna de tipo (REM/RET).
- Grade de lançamentos e painel com todos os campos do registro (nome, posição, valor e
  descrição), com valores monetários e datas convertidos para leitura humana.
- Títulos CNAB240 agrupados por segmento (P+Q+R, T+U), com Header/Trailer de arquivo e de lote.
- **Valores selecionáveis e copiáveis** (Ctrl+C) no painel de campos; Ctrl+C também copia a
  linha selecionada da grade de lançamentos.
- Tabelas de códigos de ocorrência/movimento, bancos e espécies de título.
- Arquivos de exemplo 100% fictícios em `exemplos/` e script para regenerá-los.
- Script de build do executável Windows com cópia versionada e hash SHA-256 em `releases/`.
- Suíte de testes automatizados (`python -m unittest discover -s tests`) e CI no GitHub Actions.
