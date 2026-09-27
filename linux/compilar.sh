#!/usr/bin/env bash
# Compila o executável Linux do CNABLens dentro de um container antigo (manylinux_2_28, glibc 2.28),
# para ele rodar em qualquer distro com glibc 2.28 ou mais nova (Ubuntu 20.04+, Debian 10+, Fedora...).
#
#   bash linux/compilar.sh                     # versão atual (src/version.py) em build-local/
#   bash linux/compilar.sh v0.2.0              # a partir da tag v0.2.0
#   bash linux/compilar.sh --saida PASTA       # outra pasta de saída
#   bash linux/compilar.sh --rc 2              # nome de candidata (-rc.2)
#   bash linux/compilar.sh --sem-docker        # compila no próprio computador (só roda em distros
#                                              # com glibc igual ou mais nova que a dele)
#
# Requer Docker (ou, com --sem-docker, o uv: https://docs.astral.sh/uv/). O Python usado é o
# portátil do uv, que já traz o Tk; nada é instalado no sistema. O repositório não é alterado.
set -euo pipefail

IMAGEM="quay.io/pypa/manylinux_2_28_x86_64"
PYTHON="3.12"
RAIZ=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

tag="" saida="$RAIZ/build-local" rc="" sem_docker=false
while [ $# -gt 0 ]; do
  case "$1" in
    --saida) saida="${2:?--saida precisa de uma pasta}"; shift 2 ;;
    --rc) rc="${2:?--rc precisa de um número}"; shift 2 ;;
    --sem-docker) sem_docker=true; shift ;;
    -h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    v[0-9]*) tag="$1"; shift ;;
    *) echo "Argumento desconhecido: $1 (veja: bash linux/compilar.sh --help)" >&2; exit 2 ;;
  esac
done
case "$rc" in ''|*[!0-9]*) [ -z "$rc" ] || { echo "--rc precisa de um número." >&2; exit 2; } ;; esac
mkdir -p "$saida"
saida=$(cd "$saida" && pwd)

tmp=$(mktemp -d "${TMPDIR:-/tmp}/cnab-linux-XXXXXX")
fonte="$RAIZ"
limpar() {
  [ "$fonte" = "$RAIZ" ] || git -C "$RAIZ" worktree remove --force "$fonte" >/dev/null 2>&1 || true
  rm -rf "$tmp"
}
trap limpar EXIT

# Versão antiga: código da tag num worktree temporário, com o compilador Linux atual.
if [ -n "$tag" ]; then
  git -C "$RAIZ" rev-parse -q --verify "refs/tags/$tag" >/dev/null || {
    echo "A tag $tag não existe. Rode 'git fetch --tags' ou confira o nome (ex.: v0.2.0)." >&2; exit 1; }
  fonte="$tmp/fonte"
  git -C "$RAIZ" worktree add -q --detach "$fonte" "$tag"
  mkdir -p "$fonte/linux"
  cp "$RAIZ/linux/build_linux.py" "$fonte/linux/build_linux.py"
fi

args=(--saida /saida)
[ -z "$rc" ] || args+=(--rc "$rc")

# Passos de compilação (iguais no container e no host): Python portátil do uv com Tk, PyInstaller,
# build_linux.py. O código é montado só para leitura; a saída vai para /saida.
compilar='set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_PREFERENCE=only-managed
uv venv -q --python "$PYTHON" "$TMPV/venv"
. "$TMPV/venv/bin/activate"
python -c "import tkinter" || { echo "O Python $PYTHON do uv veio sem Tkinter." >&2; exit 1; }
uv pip install -q -r "$FONTE/requirements-build.txt"
python "$FONTE/linux/build_linux.py" "$@"'

if [ "$sem_docker" = true ]; then
  command -v uv >/dev/null || { echo "Instale o uv (https://docs.astral.sh/uv/) ou use o Docker." >&2; exit 1; }
  echo "Aviso: compilando no próprio computador ($(ldd --version | head -n1))."
  echo "       O executável só roda em distros com essa glibc ou mais nova. Para qualquer distro, use o Docker."
  args=(--saida "$saida"); [ -z "$rc" ] || args+=(--rc "$rc")
  PYTHON="$PYTHON" FONTE="$fonte" TMPV="$tmp" bash -c "$compilar" compilar "${args[@]}"
else
  command -v docker >/dev/null || {
    echo "Docker não encontrado. Instale o Docker ou rode com --sem-docker (o executável só vai rodar" >&2
    echo "em distros tão novas quanto este computador)." >&2; exit 1; }
  docker run --rm \
    -v "$fonte:/fonte:ro" -v "$saida:/saida" \
    -e PYTHON="$PYTHON" -e FONTE=/fonte -e TMPV=/tmp/cnab -e UV_LINK_MODE=copy \
    "$IMAGEM" bash -c "
      set -euo pipefail
      mkdir -p /tmp/cnab
      /opt/python/cp312-cp312/bin/python -m pip install -q --root-user-action=ignore uv
      export PATH=/opt/python/cp312-cp312/bin:\$PATH
      bash -c '$compilar' compilar ${args[*]}
      chown $(id -u):$(id -g) /saida/*"
fi

echo "Pronto: $(ls "$saida"/*-linux-x64)"
