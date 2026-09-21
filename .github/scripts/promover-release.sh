#!/usr/bin/env bash
# Promove a release candidata (RC_TAG) a versao de producao SEM recompilar: baixa o binario da candidata,
# confere o hash, grava releases/vX.Y.Z/ (no diretorio de trabalho) e cria a tag + GitHub Release vX.Y.Z
# com esse MESMO binario (SHA-256 identico) e as notas da secao da versao no CHANGELOG.
# Deixa notas.md no diretorio de trabalho (usado por anunciar-release.sh).
#
# Variaveis: RC_TAG, GH_TOKEN, GITHUB_REPOSITORY, TARGET_SHA (commit da tag; padrao HEAD),
# RELEASE_LATEST (true: marca como Latest; false so em ensaios).
# Saida (em $GITHUB_OUTPUT, se definido): nova=true|false, tag=vX.Y.Z
set -euo pipefail

versao=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' src/version.py)
tag="v${versao}"
rc="${RC_TAG:?}"
alvo="${TARGET_SHA:-$(git rev-parse HEAD)}"
latest="--latest"; [ "${RELEASE_LATEST:-true}" = true ] || latest="--latest=false"
saida() { [ -z "${GITHUB_OUTPUT:-}" ] || echo "$1" >> "$GITHUB_OUTPUT"; }

if gh release view "$tag" >/dev/null 2>&1; then
  echo "Release $tag ja existe; nada a publicar."
  saida "nova=false"; saida "tag=$tag"; exit 0
fi

rc_exe="CNABLens-${rc}-windows-x64.exe"
exe="CNABLens-${tag}-windows-x64.exe"
mkdir -p baixado "releases/${tag}"
gh release download "$rc" --dir baixado --pattern "$rc_exe" --pattern SHA256SUMS.txt
(cd baixado && sha256sum -c SHA256SUMS.txt)
cp "baixado/${rc_exe}" "releases/${tag}/${exe}"
(cd "releases/${tag}" && sha256sum "$exe" > SHA256SUMS.txt)
hash=$(cut -d' ' -f1 "releases/${tag}/SHA256SUMS.txt")

# Notas: secao da versao no CHANGELOG + prova de que e o binario da candidata.
awk -v v="$versao" '
  $0 ~ "^## \\[" v "\\]" { dentro=1; next }
  dentro && /^## \[/ { exit }
  dentro { print }' CHANGELOG.md > notas.md
{
  echo
  echo "### Origem e conferência"
  echo
  echo "Este é o **mesmo binário** da release candidata \`${rc}\` (SHA-256 idêntico: \`${hash}\`), testada em homologação e aprovada para produção."
  echo
  echo '```powershell'
  echo "Get-FileHash .\\${exe} -Algorithm SHA256"
  echo '```'
  echo
  echo "Procedência: \`gh attestation verify ${exe} --repo ${GITHUB_REPOSITORY:-dono/repo}\`"
} >> notas.md

gh release create "$tag" "releases/${tag}/${exe}" "releases/${tag}/SHA256SUMS.txt" \
  --target "$alvo" --title "CNABLens ${tag}" --notes-file notas.md $latest
saida "nova=true"; saida "tag=$tag"
echo "Publicada: $tag (mesmo binario de $rc)."
