#!/usr/bin/env bash
# "Ver paineis": lista, coluna por coluna, as issues abertas deste repositorio nos paineis
# Planejamento, Execucao e Bugs (numero, titulo e Sprint). Somente leitura: nao move nada.
# Existe para quem nao alcanca a API dos paineis (ex.: a IA nas sessoes do Claude Code) ler o
# estado pelo log ou pelo resumo da execucao. O repositorio e publico: o resultado tambem e.
#
# Variaveis: PROJETO_PLANEJAMENTO, PROJETO_EXECUCAO, PROJETO_BUGS (numeros dos paineis; o que
# estiver vazio e pulado), GITHUB_STEP_SUMMARY (opcional: recebe a mesma saida em Markdown).
set -euo pipefail
shopt -s inherit_errexit  # falha do gh dentro de $(...) derruba o script (nao vira "nenhuma issue")

AQUI="$(cd "$(dirname "$0")" && pwd)"
projeto() { bash "$AQUI/projeto.sh" "$@"; }

# painel <nome> <numero>: imprime o painel em Markdown
painel() {
  local nome="$1" numero="$2" colunas quadro coluna linhas
  colunas=$(projeto colunas "$numero")
  quadro=$(projeto quadro "$numero")
  echo "## $nome (painel $numero)"
  echo
  # colunas na ordem do painel; "-" (sem Status) por ultimo
  while IFS= read -r coluna; do
    linhas=$(awk -F'\t' -v c="$coluna" '$1 == c' <<<"$quadro")
    [ -n "$linhas" ] || continue
    if [ "$coluna" = "-" ]; then echo "### (sem coluna)"; else echo "### $coluna"; fi
    echo
    awk -F'\t' '{ printf "- #%s %s", $2, $3; if ($4 != "-") printf " (%s)", $4; print "" }' <<<"$linhas"
    echo
  done <<<"$colunas"$'\n-'
  [ -n "$quadro" ] || { echo "Nenhuma issue aberta."; echo; }
}

saida=$(
  [ -z "${PROJETO_PLANEJAMENTO:-}" ] || painel "Planejamento" "$PROJETO_PLANEJAMENTO"
  [ -z "${PROJETO_EXECUCAO:-}" ] || painel "Execução" "$PROJETO_EXECUCAO"
  [ -z "${PROJETO_BUGS:-}" ] || painel "Bugs" "$PROJETO_BUGS"
)
printf '%s\n' "$saida"
[ -z "${GITHUB_STEP_SUMMARY:-}" ] || printf '%s\n' "$saida" >> "$GITHUB_STEP_SUMMARY"
