# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versionamento
[SemVer](https://semver.org/lang/pt-BR/).

## [Não lançado]

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
