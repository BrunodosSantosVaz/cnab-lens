#!/usr/bin/env bash
# "Iniciar sprint": cria o milestone da versao, move os epicos de "Proxima sprint" para
# "Em desenvolvimento" e cria, para cada um, as tarefas da secao "Tarefas previstas" do corpo do
# epico: sub-issues label "task", ligadas ao epico e ao milestone, com cartao em "A fazer" no
# painel de Execucao. Epico SEM tarefas previstas nao e movido (fica em "Proxima sprint" com um
# aviso). Idempotente: tarefas ja criadas (mesmo titulo, como sub-issue do epico) nao se repetem,
# e se o milestone ja existe ele e reaproveitado.
#
# Os criterios de aceite e os testes de cada tarefa saem como esqueleto para preencher no
# refinamento (ver docs/processo.md).
#
# Variaveis: VERSAO (v0.6.0), DATA (opcional, AAAA-MM-DD), SIMULAR=true,
# PROJETO_PLANEJAMENTO, PROJETO_EXECUCAO.
set -euo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd)"
PLAN="${PROJETO_PLANEJAMENTO:?}"; EXEC="${PROJETO_EXECUCAO:?}"
R="$GITHUB_REPOSITORY"; OWNER="${R%%/*}"; REPO="${R##*/}"
v="${VERSAO:?informe a versao}"; v="${v#v}"; tag="v$v"
DATA="${DATA:-}"
SIMULAR="${SIMULAR:-false}"
[ "$SIMULAR" = true ] && export DRY_RUN=1
run() { if [ "$SIMULAR" = true ]; then echo "[simulado] $*"; else "$@"; fi; }
projeto() { bash "$AQUI/projeto.sh" "$@"; }
gql() { gh api graphql -H "GraphQL-Features: sub_issues" "$@"; }

[[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "::error::Versao '$v' invalida (use x.y.z)."; exit 1; }
if [ -n "$DATA" ] && ! [[ "$DATA" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "::error::Data '$DATA' invalida (use AAAA-MM-DD)."; exit 1
fi

# ---- epicos da proxima sprint e as tarefas previstas de cada um
mapfile -t epicos < <(projeto cartoes "$PLAN" "Próxima sprint")
milestone=$(gh api "repos/$R/milestones?state=all&per_page=100" --paginate \
  --jq ".[] | select(.title==\"$tag\") | .number" | head -1)
if [ "${#epicos[@]}" -eq 0 ]; then
  if [ -n "$milestone" ]; then echo "Milestone $tag ja existe e nao ha epicos em 'Próxima sprint'; nada a fazer."; exit 0; fi
  echo "::error::Nenhum epico na coluna 'Próxima sprint'. Escolha os epicos da sprint antes de iniciar."; exit 1
fi

iniciar=(); sem_tarefas=(); descricao_epicos=""
declare -A titulo_epico
for n in "${epicos[@]}"; do
  titulo_epico[$n]=$(gh api "repos/$R/issues/$n" --jq .title)
  qtd=$(gh api "repos/$R/issues/$n" --jq '.body // ""' | bash "$AQUI/tarefas-do-epico.sh" | wc -l)
  if [ "$qtd" -eq 0 ]; then
    sem_tarefas+=("$n")
  else
    iniciar+=("$n"); descricao_epicos+="- #$n ${titulo_epico[$n]}"$'\n'
  fi
done
for n in "${sem_tarefas[@]:-}"; do
  [ -n "$n" ] || continue
  echo "::warning::Epico #$n (${titulo_epico[$n]}) nao tem a secao 'Tarefas previstas' com itens: continua em 'Próxima sprint'. Liste as tarefas no corpo do epico e rode de novo."
done
if [ "${#iniciar[@]}" -eq 0 ]; then
  echo "::error::Nenhum epico de 'Próxima sprint' tem 'Tarefas previstas'. Nada foi iniciado."; exit 1
fi

# ---- milestone (cria se nao existe)
if [ -z "$milestone" ]; then
  descricao="Sprint $tag

Épicos:
$descricao_epicos"
  args=(-f "title=$tag" -f "description=$descricao")
  [ -z "$DATA" ] || args+=(-f "due_on=${DATA}T12:00:00Z")
  if [ "$SIMULAR" = true ]; then
    echo "[simulado] criar milestone $tag com os epicos: ${iniciar[*]}"
  else
    milestone=$(gh api -X POST "repos/$R/milestones" "${args[@]}" --jq .number)
    echo "Milestone criado: $tag (#$milestone)"
  fi
else
  echo "Milestone $tag ja existe (#$milestone); reaproveitado."
fi

# ---- para cada epico: cria as tarefas (sub-issues) e move o epico
for n in "${iniciar[@]}"; do
  echo "== Epico #$n: ${titulo_epico[$n]}"
  epico_node=$(gh api "repos/$R/issues/$n" --jq .node_id)
  existentes=$(gql -f o="$OWNER" -f r="$REPO" -F n="$n" -f query='
    query($o:String!,$r:String!,$n:Int!){ repository(owner:$o,name:$r){ issue(number:$n){
      subIssues(first:100){ nodes{ title } } } } }' --jq '.data.repository.issue.subIssues.nodes[].title')
  while IFS= read -r tarefa; do
    [ -n "$tarefa" ] || continue
    if grep -qxF -- "$tarefa" <<<"$existentes"; then
      echo "  ja existe: $tarefa"; continue
    fi
    if [ "$SIMULAR" = true ]; then
      echo "  [simulado] criar tarefa '$tarefa' (task, $tag, sub-issue de #$n, cartao em 'A fazer')"; continue
    fi
    corpo="### Épico
#$n — ${titulo_epico[$n]}

### O que fazer
$tarefa

### Critérios de aceite
- [ ] 
- [ ] 

### Testes automatizados (obrigatório)
- [ ] Unitário: 
- [ ] Integração: 

### Impacto
Detalhar ao refinar a tarefa."
    url=$(gh issue create --repo "$R" --title "$tarefa" --label task --milestone "$tag" --body "$corpo")
    num="${url##*/}"
    tarefa_node=$(gh api "repos/$R/issues/$num" --jq .node_id)
    gql -f e="$epico_node" -f t="$tarefa_node" -f query='
      mutation($e:ID!,$t:ID!){ addSubIssue(input:{issueId:$e, subIssueId:$t}){ issue{ number } } }' >/dev/null
    projeto mover "$EXEC" "$num" "A fazer" "-" >/dev/null
    echo "  criada #$num: $tarefa"
  done < <(gh api "repos/$R/issues/$n" --jq '.body // ""' | bash "$AQUI/tarefas-do-epico.sh")
  projeto mover "$PLAN" "$n" "Em desenvolvimento" "Próxima sprint"
done

echo "Sprint $tag iniciada: ${#iniciar[@]} epico(s) em desenvolvimento."
[ "${#sem_tarefas[@]}" -eq 0 ] || echo "Epicos que ficaram em 'Próxima sprint' por falta de 'Tarefas previstas': ${sem_tarefas[*]}"
echo "Proximo passo: refinar as tarefas (criterios de aceite e testes) e rodar a acao 'Criar branches das tarefas' para abrir as branches e mover os cartoes para Feature."
