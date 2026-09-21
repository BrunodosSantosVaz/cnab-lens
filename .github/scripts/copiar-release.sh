#!/usr/bin/env bash
# Guarda a copia do executavel de producao em releases/vX.Y.Z/ (commit na branch principal).
# Nunca falha a publicacao: se o push for recusado, so avisa. Variaveis: TAG, BRANCH_MAIN (main).
set -euo pipefail
tag="${TAG:?}"; main="${BRANCH_MAIN:-main}"
git config user.name  >/dev/null 2>&1 || git config user.name  "github-actions[bot]"
git config user.email >/dev/null 2>&1 || git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add "releases/${tag}"
if git diff --cached --quiet; then echo "releases/${tag} ja esta versionado."; exit 0; fi
git commit -q -m "chore(release): copia do executavel ${tag}"
git push origin "HEAD:${main}" || echo "::warning::Nao consegui commitar releases/${tag} na ${main} (o PROJETO_TOKEN do dono e necessario para contornar a protecao). A Release ${tag} ja foi publicada."
