# Instruções para agentes de IA (AGENTS.md)

Este arquivo orienta qualquer IA que trabalhe no CNABLens (Claude Code, Copilot, Codex, Cursor…).
O `CLAUDE.md` só importa este arquivo. **Mantenha-o atualizado** quando o processo, os comandos ou a
estrutura mudarem: ele faz parte da documentação e tem teste (`tests/test_documentacao.py`).

## O projeto em uma frase

Leitor de arquivos CNAB 400 e 240 (remessa e retorno de cobrança) com interface Tkinter, compilado em
um `.exe` (Windows) e num executável Linux. Roda 100% local, é somente leitura e usa só a biblioteca
padrão do Python.

## `pyproject.toml` é a referência

Consulte **sempre** o `pyproject.toml` antes de assumir qualquer coisa sobre o projeto:

- **Python mínimo** (`requires-python`): não use recursos de versões mais novas que ele.
- **Versão**: o `pyproject.toml` a lê do `src/cnablens/version.py`. Nunca escreva a versão em outro lugar, e
  nunca a altere à mão: é a esteira que sobe a versão ao integrar uma release.
- **Estilo e qualidade**: a configuração do Ruff (`[tool.ruff]`). Rode `uvx ruff check .` no que você mexer.
- **Dependências**: o programa não tem dependências de execução (`dependencies = []`). A de build (o
  PyInstaller) fica **só** no `requirements-build.txt`. Não a duplique no `pyproject.toml`.
- Se precisar de uma configuração nova de ferramenta, ela vai no `pyproject.toml`, e não em arquivos soltos.

## Comandos

| Para… | Rode |
|---|---|
| Rodar o programa | `python src/cnablens/__main__.py` (ou `python -m cnablens` com `pip install -e .`) |
| Testes (obrigatório antes de todo commit) | `python -m unittest discover -s tests` |
| Lint (roda na CI; tem que ficar sem avisos) | `uvx ruff check .` |
| Regenerar os exemplos fictícios | `python scripts/gerar_exemplos.py` (o CI confere que `exemplos/` está em dia) |
| Compilar para Windows | `python packaging/windows/build_exe.py` (num Windows, com `pip install -r requirements-build.txt`) |
| Compilar para Linux | `bash packaging/linux/compilar.sh` (Docker; veja `packaging/linux/README.md`) |
| Instalar para desenvolver | `pip install -e .` |

A saída dos compiladores vai para `build-local/`, que é ignorada pelo Git. Apague o que você gerou
(`build-local/`, `__pycache__/`) ao terminar: o clone do dono deve ficar limpo.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `src/cnablens/` | O programa (pacote). Mexer aqui **muda o executável** e exige uma versão nova. |
| `src/cnablens/leitura/` | Leitura dos arquivos: `CnabFile` e um leitor por formato (`leitor400.py`, `leitor240.py`). Sem Tkinter. |
| `src/cnablens/layouts/` | Layouts dos bancos: dados em um módulo por banco, blocos em `base.py`, registro no `__init__.py`. |
| `src/cnablens/formatacao.py` | Valores em R$ e datas. Sem Tkinter. |
| `src/cnablens/interface/` | A tela (Tkinter). Só apresenta: não põe regra de leitura aqui. |
| `tests/` | Testes (`unittest`), inclusive dos scripts da esteira. |
| `packaging/windows/`, `packaging/linux/` | Compiladores. |
| `scripts/` | Utilitários (`gerar_exemplos.py`) e configuração do GitHub (`processo/`). |
| `exemplos/` | Arquivos CNAB **fictícios**. |
| `.github/` | Workflows e scripts da esteira, modelos de issue e PR. |
| `docs/processo.md` | O processo completo. Leia antes de mexer na esteira. |

## Processo (resumo; completo em `docs/processo.md`)

1. **Tudo nasce de um épico**, refinado com "Muda o programa?", escopo, critérios de aceite e *Tarefas previstas*.
2. **Iniciar sprint** e **Criar branches** são botões (`gh workflow run iniciar-sprint.yml` / `criar-branches.yml`).
   Rode **sempre com `-f simular=true` antes**. Não crie issues, milestones nem branches de tarefa à mão.
3. **Sprint não é versão.** O milestone `vX.Y.Z` existe só para o que muda o programa (`src/` ou
   `requirements-build.txt`). Tudo o mais é `sem-executavel`: roda sem versão e sem milestone.
4. **Uma tarefa = uma branch `feature/<n>-<slug>` = um PR para a `develop`**, com `Refs #<n>` (nunca
   `Closes`: as issues fecham sozinhas na publicação).
5. **Para ver as colunas dos painéis**, rode o botão *Ver painéis* (`gh workflow run ver-paineis.yml`, somente
   leitura) e leia o resumo da execução. Na sessão do Claude Code a API dos painéis não é alcançável.
6. **Ao começar a programar uma tarefa, mova o cartão para *Code*:**
   `PROJETO_OWNER=BrunodosSantosVaz GITHUB_REPOSITORY=BrunodosSantosVaz/cnab-lens bash .github/scripts/projeto.sh mover 11 <n> "Code"`.
7. **Todo PR tem testes** e a CI verde (`check` e `regras` são obrigatórios).
8. **PR `sem-executavel` não leva a label `aprovado`**: é mesclado direto na `develop` (merge commit, na
   ordem das dependências) e finalizado por *Publicar sem executável*. PR que muda o programa leva
   `aprovado`, e a esteira integra a release e gera a candidata para homologação.

## O que a IA nunca faz sem pedido explícito do dono

- Aprovar PR (label `aprovado`), mover cartão para *Aprovado*/*Reprovado*, aprovar o ambiente `producao`
  ou rodar *Publicar em produção* / *Publicar sem executável*. Uma autorização vale **só** para a sprint
  em que foi dada.
- Commitar direto na `main` ou na `develop`, forçar push, reescrever histórico ou apagar tags.
- Mudar o comportamento do programa numa tarefa `sem-executavel`, ou tocar `src/` fora de uma versão.
- Alterar `packaging/windows/build_exe.py` sem necessidade: ele gera o `.exe` oficial e o portão da
  produção o compara com o da candidata.

## Regras de código

- **Dados fictícios sempre.** Arquivos CNAB reais têm dados pessoais (LGPD): nunca os versione, cite ou
  use em teste. A pasta `arquivos/` é ignorada por isso.
- **Nomes, comentários, commits e documentação em português do Brasil**, como o resto do projeto. Commits
  no formato `tipo: resumo` (`feat`, `fix`, `docs`, `test`, `refactor`, `build`, `chore`).
- **Layouts citam a fonte oficial** (manual do banco, versão e data) e cobrem todas as posições sem
  lacunas (há teste de contiguidade).
- Código simples: funções curtas, uma responsabilidade por módulo, sem repetição. Prefira ajustar o que
  já existe a criar outro caminho para a mesma coisa.
- **Onde fica cada coisa**: regra de formato na leitura (o leitor do formato), dado de banco no módulo do
  layout, formatação em `formatacao.py`, tela em `interface/`. A interface nunca lê o arquivo nem formata
  sozinha, e a leitura nunca importa Tkinter (há teste para isso).
- **Banco novo** = módulo de dados em `layouts/` + entrada no registro (`layouts/__init__.py`). A leitura
  e a tela não mudam.
- **Refatoração não muda comportamento**: o teste de equivalência (`tests/test_equivalencia.py`) compara
  a leitura com um retrato guardado. Só regenere o retrato (`--gerar`) quando a mudança de comportamento
  for intencional, e diga isso no PR.
- Os campos de "Uso Reservado (Filler)", os nomes de campo usados na grade (`Nosso Número`, `Valor
  Nominal`, `Data de Vencimento`…) e a formatação de valores e datas seguem as convenções do README
  ("Adicionando um novo layout").
