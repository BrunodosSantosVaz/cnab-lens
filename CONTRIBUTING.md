# Contribuindo com o CNABLens

Obrigado por querer ajudar! Este guia mostra como contribuir sem tropeços. O processo completo
(painéis, branches, releases) está em [docs/processo.md](docs/processo.md).

## Antes de tudo: dados pessoais

Arquivos CNAB reais contêm **nomes, CPF/CNPJ, endereços e valores de terceiros** (dados protegidos
pela LGPD). **Nunca anexe arquivos reais em issues, pull requests ou comentários.** Troque os dados
por fictícios ou informe apenas as posições e os valores envolvidos. Os arquivos de
[`exemplos/`](exemplos/) são 100% fictícios e podem ser usados à vontade.

## Jeitos de contribuir

- **Dúvida de uso, ideia solta ou conversa?** Use o [Discussions](https://github.com/BrunodosSantosVaz/cnab-lens/discussions) (Q&A e Ideas). Assim as Issues ficam só com trabalho concreto. Uma ideia que amadurece vira épico pelas mãos do mantenedor: você **não** precisa abrir o formulário de Épico.
- **Achou um campo errado ou quer um banco novo?** Abra uma issue com o formulário **Layout ou
  banco**, citando a fonte oficial (manual do banco, com versão e data).
- **Achou um bug?** Abra uma issue com o formulário **Bug** (versão, passos para reproduzir, resultado
  esperado × obtido). Sem dados pessoais nas evidências.
- **Achou uma vulnerabilidade?** Não abra issue: use o relato privado ([SECURITY.md](SECURITY.md)).
- **Quer programar?** Comente numa issue existente (ou abra uma) antes de começar, para alinharmos o
  escopo. Issues com a label `good first issue` são um bom começo. **Toda alteração precisa de issue**,
  inclusive uma correção pequena de documentação, porque o número dela vai no nome da branch.

## Ambiente de desenvolvimento

Requer **Python 3.10 ou superior com Tkinter** (o instalador oficial do Python para Windows já
inclui). O programa não usa bibliotecas externas.

```powershell
git clone https://github.com/BrunodosSantosVaz/cnab-lens.git
cd cnab-lens
python src\cnab400_reader.py                       # rodar
python -m unittest discover -s tests -v            # testes
pip install -r requirements-build.txt              # só para gerar o .exe
python scripts\build_exe.py                        # gera em build-local/ (ignorada pelo Git)
```

## Fluxo de trabalho

1. Faça um **fork** e clone-o. A base do trabalho é a branch **`develop`** (não a `main`).
2. Crie a branch a partir da `develop` com o **número da issue**:
   `feature/<n>-<slug>` (tarefa) ou `bugfix/<n>-<slug>` (bug). Ex.: `feature/12-exportar-csv`.
3. Faça mudanças **pequenas e focadas** (um assunto por pull request) e **inclua testes**.
4. Abra o PR **para a `develop`** com `Refs #<n>` na descrição, preenchendo o modelo. O CI (`check`) e o
   `Regras do PR` precisam passar. O primeiro PR de quem é novo no projeto pode esperar a aprovação do
   mantenedor para o CI rodar.
5. Responda à revisão com novos commits na mesma branch.

### O que acontece depois

Só o mantenedor mescla, aprova e publica. Você não mexe em versão, `CHANGELOG.md` nem em release. Quando o PR
é aprovado (label `aprovado`) e todos os PRs da sprint estão aprovados, a esteira monta a release, gera a
candidata `vX.Y.Z-rc.N` e a leva para homologação; testada e aprovada, é publicada e a sua issue é fechada
sozinha. Os seus commits mantêm a sua autoria. Não há prazo garantido (projeto mantido em tempo parcial).
Um PR só entra em uma release se a issue dele estiver em uma sprint (milestone): o mantenedor decide isso.
Se o PR só mexe em documentação, testes ou automação (nada em `src/` nem em `requirements-build.txt`), ele recebe sozinho a label `sem-executavel`: não passa por homologação nem gera versão nova, e chega à `main` quando o mantenedor roda o botão *Publicar sem executável*.

Mensagens de commit: uma linha objetiva, de preferência no formato `tipo: resumo`
(`feat`, `fix`, `docs`, `test`, `chore`, `refactor`).

## Padrões do código

- **Só biblioteca padrão** (nada de dependências novas sem discussão prévia).
- **Layouts**: cada campo é uma tupla `(nome, início, fim, descrição)`, as listas cobrem as posições
  1–400 (ou 1–240) sem lacunas, e a descrição resume o manual oficial. Cite a fonte no docstring do
  módulo. Passo a passo em [README > Adicionando um novo layout](README.md#adicionando-um-novo-layout-outro-banco).
- **Sem dados reais** em código, testes, exemplos ou imagens. Gere exemplos com
  `python scripts/gerar_exemplos.py`.
- **Textos** em português do Brasil, com acentuação correta.

## Testes

`python -m unittest discover -s tests -v` precisa passar. Para um bug, escreva primeiro o teste que
falha (regressão) e depois a correção. Novos layouts precisam de um arquivo fictício em `exemplos/`
(pelo `scripts/gerar_exemplos.py`) e de teste que o carregue com o layout certo.

## Licença

Ao contribuir, você concorda que sua contribuição seja distribuída sob a [Licença MIT](LICENSE) do
projeto. Veja também o [Código de Conduta](CODE_OF_CONDUCT.md).
