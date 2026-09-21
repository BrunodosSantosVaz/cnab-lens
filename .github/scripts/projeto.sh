#!/usr/bin/env bash
# Auxiliar dos workflows: mover cartoes nos paineis (GitHub Projects v2).
#
# Subcomandos:
#   projeto.sh mover  <painel> <issue> "<Status>" ["<De1|De2>"]
#       Adiciona a issue ao painel (se nao estiver) e define o Status.
#       Com o 4o argumento, so move se o Status ATUAL estiver na lista
#       (use "-" para "sem status"); evita mandar o cartao para tras.
#   projeto.sh cartoes <painel> "<Status>"
#       Imprime os numeros das issues deste repositorio que estao no Status.
#   projeto.sh remover <painel> <issue>
#       Tira a issue do painel.
#
# Ambiente: GH_TOKEN (com escopo "project"), PROJETO_OWNER (dono dos paineis),
# GITHUB_REPOSITORY (owner/repo). <painel> e o NUMERO do projeto.
# DRY_RUN=1 apenas imprime o que faria (nao altera nada).
set -euo pipefail

: "${PROJETO_OWNER:?defina PROJETO_OWNER}"
: "${GITHUB_REPOSITORY:?defina GITHUB_REPOSITORY}"

projeto_id() {
  gh api graphql -F n="$1" -f o="$PROJETO_OWNER" -f query='
    query($o:String!,$n:Int!){ repositoryOwner(login:$o){
      ... on ProjectV2Owner { projectV2(number:$n){ id } } } }' \
    --jq '.data.repositoryOwner.projectV2.id'
}

# imprime: <id-do-campo-Status>\t<id-da-opcao>  (para o Status pedido)
status_ids() {
  gh api graphql -F n="$1" -f o="$PROJETO_OWNER" -f query='
    query($o:String!,$n:Int!){ repositoryOwner(login:$o){
      ... on ProjectV2Owner { projectV2(number:$n){
        field(name:"Status"){ ... on ProjectV2SingleSelectField { id options{ id name } } } } } } }' \
  | jq -r --arg s "$2" '.data.repositoryOwner.projectV2.field as $f
      | ($f.options[] | select(.name==$s) | .id) as $o | "\($f.id)\t\($o)"'
}

mover() {
  local painel="$1" issue="$2" destino="$3" de="${4:-}"
  local pid node item atual ids campo opcao
  if [ "${DRY_RUN:-}" = 1 ]; then
    echo "[simulado] painel $painel: #$issue -> '$destino' (somente de: ${de:-qualquer})"
    return 0
  fi
  pid=$(projeto_id "$painel")
  node=$(gh api "repos/$GITHUB_REPOSITORY/issues/$issue" --jq '.node_id')
  item=$(gh api graphql -f p="$pid" -f c="$node" -f query='
    mutation($p:ID!,$c:ID!){ addProjectV2ItemById(input:{projectId:$p, contentId:$c}){ item{ id } } }' \
    --jq '.data.addProjectV2ItemById.item.id')
  atual=$(gh api graphql -f i="$item" -f query='
    query($i:ID!){ node(id:$i){ ... on ProjectV2Item {
      fieldValueByName(name:"Status"){ ... on ProjectV2ItemFieldSingleSelectValue { name } } } } }' \
    --jq '.data.node.fieldValueByName.name // "-"')
  if [ -n "$de" ] && ! printf '%s' "|$de|" | grep -qF "|$atual|"; then
    echo "#$issue no painel $painel: '$atual' fora de [$de]; mantido."
    return 0
  fi
  if [ "$atual" = "$destino" ]; then
    echo "#$issue no painel $painel: ja esta em '$destino'."
    return 0
  fi
  ids=$(status_ids "$painel" "$destino")
  campo="${ids%%$'\t'*}"; opcao="${ids##*$'\t'}"
  if [ -z "$opcao" ] || [ "$opcao" = "$ids" ]; then
    echo "Status '$destino' nao existe no painel $painel." >&2; return 1
  fi
  gh api graphql -f p="$pid" -f i="$item" -f f="$campo" -f o="$opcao" -f query='
    mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){ updateProjectV2ItemFieldValue(input:{
      projectId:$p, itemId:$i, fieldId:$f, value:{singleSelectOptionId:$o}}){ projectV2Item{ id } } }' >/dev/null
  echo "#$issue no painel $painel: '$atual' -> '$destino'."
}

cartoes() {
  local painel="$1" status="$2" pid
  pid=$(projeto_id "$painel")
  gh api graphql --paginate -f id="$pid" -f query='
    query($id:ID!,$endCursor:String){ node(id:$id){ ... on ProjectV2 {
      items(first:100, after:$endCursor){ pageInfo{ hasNextPage endCursor } nodes{
        fieldValueByName(name:"Status"){ ... on ProjectV2ItemFieldSingleSelectValue { name } }
        content{ ... on Issue { number repository{ nameWithOwner } } } } } } } }' \
    --jq ".data.node.items.nodes[]
      | select(.fieldValueByName.name==\"$status\" and .content.repository.nameWithOwner==\"$GITHUB_REPOSITORY\")
      | .content.number"
}

remover() {
  local painel="$1" issue="$2" pid node item
  if [ "${DRY_RUN:-}" = 1 ]; then echo "[simulado] remover #$issue do painel $painel"; return 0; fi
  pid=$(projeto_id "$painel")
  node=$(gh api "repos/$GITHUB_REPOSITORY/issues/$issue" --jq '.node_id')
  item=$(gh api graphql -f p="$pid" -f c="$node" -f query='
    mutation($p:ID!,$c:ID!){ addProjectV2ItemById(input:{projectId:$p, contentId:$c}){ item{ id } } }' \
    --jq '.data.addProjectV2ItemById.item.id')
  gh api graphql -f p="$pid" -f i="$item" -f query='
    mutation($p:ID!,$i:ID!){ deleteProjectV2Item(input:{projectId:$p, itemId:$i}){ deletedItemId } }' >/dev/null
  echo "#$issue removida do painel $painel."
}

cmd="${1:-}"; shift || true
case "$cmd" in
  mover)   mover "$@" ;;
  cartoes) cartoes "$@" ;;
  remover) remover "$@" ;;
  *) sed -n '2,18p' "$0"; exit 2 ;;
esac
