#!/usr/bin/env bash
# Le o corpo de um epico (stdin) e imprime a resposta do campo "Muda o programa?" do formulario:
# "sim", "nao" ou vazio (campo ausente ou sem resposta: epicos antigos). Vazio e tratado como
# "muda o programa" pela esteira (o caminho seguro, que exige versao).
# Usado por kanban.sh e iniciar-sprint.sh; testado em tests/test_muda_programa.py.
set -euo pipefail
tr -d '\r' | awk '
  /^###[[:space:]]+/ { dentro = ($0 ~ /^###[[:space:]]+Muda o programa\?[[:space:]]*$/); next }
  dentro && NF {
    linha = tolower($0)
    if (linha ~ /^[[:space:]]*sim/) { print "sim"; exit }
    if (linha ~ /^[[:space:]]*n(ã|a)o/) { print "nao"; exit }
  }'
