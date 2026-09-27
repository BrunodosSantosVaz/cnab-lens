#!/usr/bin/env bash
# Promove a release candidata (RC_TAG) a versao de producao SEM recompilar: baixa os dois binarios da
# candidata (Windows e Linux), confere os hashes e cria a tag + GitHub Release vX.Y.Z com esses MESMOS
# binarios (SHA-256 identico) e as notas da secao da versao no CHANGELOG. Os executaveis ficam so na
# Release: nada e gravado no repositorio (os arquivos sao preparados numa pasta temporaria).
# Arquivos da Release: CNABLens-vX.Y.Z-windows-x64.exe + SHA256SUMS.txt e
#                      CNABLens-vX.Y.Z-linux-x64       + SHA256SUMS-linux.txt
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
rc_lin="CNABLens-${rc}-linux-x64"
lin="CNABLens-${tag}-linux-x64"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
baixado="$tmp/baixado" pub="$tmp/publicar"
mkdir -p "$baixado" "$pub"
gh release download "$rc" --dir "$baixado" --pattern "$rc_exe" --pattern SHA256SUMS.txt \
  --pattern "$rc_lin" --pattern SHA256SUMS-linux.txt
for f in "$rc_exe" SHA256SUMS.txt "$rc_lin" SHA256SUMS-linux.txt; do
  [ -f "${baixado}/$f" ] || { echo "::error::A candidata $rc nao tem o arquivo $f. Nada foi publicado."; exit 1; }
done
(cd "$baixado" && sha256sum -c SHA256SUMS.txt && sha256sum -c SHA256SUMS-linux.txt)
cp "${baixado}/${rc_exe}" "${pub}/${exe}"
cp "${baixado}/${rc_lin}" "${pub}/${lin}"
(cd "$pub" && sha256sum "$exe" > SHA256SUMS.txt && sha256sum "$lin" > SHA256SUMS-linux.txt)
hash=$(cut -d' ' -f1 "${pub}/SHA256SUMS.txt")
hash_lin=$(cut -d' ' -f1 "${pub}/SHA256SUMS-linux.txt")

# Notas: secao da versao no CHANGELOG + prova de que e o binario da candidata.
awk -v v="$versao" '
  $0 ~ "^## \\[" v "\\]" { dentro=1; next }
  dentro && /^## \[/ { exit }
  dentro { print }' CHANGELOG.md > notas.md
{
  echo
  echo "### Origem e conferência"
  echo
  echo "Estes são os **mesmos binários** da release candidata \`${rc}\` (SHA-256 idêntico), testados em homologação e aprovados para produção."
  echo
  echo "| Sistema | Arquivo | SHA-256 |"
  echo "|---|---|---|"
  echo "| Windows | \`${exe}\` | \`${hash}\` |"
  echo "| Linux | \`${lin}\` | \`${hash_lin}\` |"
  echo
  echo "Windows (PowerShell):"
  echo
  echo '```powershell'
  echo "Get-FileHash .\\${exe} -Algorithm SHA256"
  echo '```'
  echo
  echo "Linux:"
  echo
  echo '```bash'
  echo "sha256sum -c SHA256SUMS-linux.txt"
  echo "chmod +x ${lin} && ./${lin}"
  echo '```'
  echo
  echo "Procedência do \`.exe\`: \`gh attestation verify ${exe} --repo ${GITHUB_REPOSITORY:-dono/repo}\`"
} >> notas.md

gh release create "$tag" "${pub}/${exe}" "${pub}/SHA256SUMS.txt" "${pub}/${lin}" "${pub}/SHA256SUMS-linux.txt" \
  --target "$alvo" --title "CNABLens ${tag}" --notes-file notas.md $latest
saida "nova=true"; saida "tag=$tag"
echo "Publicada: $tag (mesmos binarios Windows e Linux de $rc)."
