#!/usr/bin/env bash
# Ponto unico para achar a versao do CNABLens (SemVer, "__version__" do arquivo de versao):
#   src/cnablens/version.py  (pacote, a partir da v0.3.0)
#   src/version.py           (estrutura antiga: tags ate a v0.2.0)
# Uso: versao.sh            imprime a versao (ex.: 0.3.0)
#      versao.sh --arquivo  imprime o caminho do arquivo de versao
# Roda na raiz do repositorio (ou de uma copia/worktree dele). Sem arquivo ou sem __version__: erro.
set -euo pipefail

arquivo=""
for candidato in src/cnablens/version.py src/version.py; do
  if [ -f "$candidato" ]; then arquivo="$candidato"; break; fi
done
[ -n "$arquivo" ] || { echo "::error::Arquivo de versao nao encontrado (src/cnablens/version.py ou src/version.py)." >&2; exit 1; }

if [ "${1:-}" = --arquivo ]; then echo "$arquivo"; exit 0; fi
versao=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$arquivo")
[ -n "$versao" ] || { echo "::error::Nao consegui ler __version__ em $arquivo." >&2; exit 1; }
echo "$versao"
