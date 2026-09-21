#!/usr/bin/env bash
# Portao de publicacao: uma versao so chega a producao se existir uma release candidata
# (vX.Y.Z-rc.N, a homologacao) e se o codigo nao mudou depois dela.
#
# Confere: (1) src/version.py legivel; (2) secao "## [X.Y.Z]" no CHANGELOG; (3) existe a tag da
# ultima rc dessa versao; (4) src/, o script de build e as dependencias de build sao identicos
# aos da rc (o binario testado e o que sera publicado).
# Usado pelo CI (PR para a main) e pelo workflow "Publicar release". Grava rc_tag= em GITHUB_OUTPUT.
set -euo pipefail

versao=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' src/version.py)
[ -n "$versao" ] || { echo "::error::Nao consegui ler __version__ em src/version.py."; exit 1; }

grep -q "^## \[${versao}\]" CHANGELOG.md || {
  echo "::error::CHANGELOG.md sem a secao '## [${versao}]'."; exit 1; }

rc_tag=$(git tag -l "v${versao}-rc.*" | sort -V | tail -n 1)
[ -n "$rc_tag" ] || {
  echo "::error::Nao existe release candidata (v${versao}-rc.N). Ela e criada pelo workflow 'Build release candidata' quando a branch release/${versao} (ou hotfix/*) recebe um push. Teste a candidata em homologacao antes de publicar."
  exit 1
}

if ! git diff --quiet "$rc_tag" HEAD -- src scripts/build_exe.py requirements-build.txt; then
  echo "::error::O codigo mudou depois da candidata ${rc_tag}. Envie um push na branch de release para gerar uma nova candidata, teste-a e so entao publique."
  git diff --stat "$rc_tag" HEAD -- src scripts/build_exe.py requirements-build.txt
  exit 1
fi

echo "Versao ${versao} pronta para producao: candidata ${rc_tag} testada, codigo identico."
echo "rc_tag=${rc_tag}" >> "${GITHUB_OUTPUT:-/dev/null}"
