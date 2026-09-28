# -*- coding: utf-8 -*-
"""Arquivos de uma pasta: a lista com metadados e uma espiada rápida no tipo (Remessa/Retorno) de cada um,
para a lista de arquivos da tela. Não depende da interface."""
import os
from datetime import datetime

from cnablens.leitura.registro import safe_slice


SEM_EXTENSAO = "(sem extensão)"


def escanear_pasta(folder_path):
    """Lista os arquivos (não-recursivo) de uma pasta, com metadados básicos
    (extensão, tamanho, data de modificação). O 'tipo' (Remessa/Retorno) só é
    calculado sob demanda (é preciso abrir o arquivo), então começa como None."""
    arquivos = []
    with os.scandir(folder_path) as it:
        entradas = sorted(it, key=lambda e: e.name.lower())
        for entry in entradas:
            if not entry.is_file():
                continue
            ext = os.path.splitext(entry.name)[1].lower() or SEM_EXTENSAO
            try:
                stat = entry.stat()
                tamanho = stat.st_size
                modificado = datetime.fromtimestamp(stat.st_mtime)
            except OSError:
                tamanho = 0
                modificado = None
            arquivos.append({
                "path": entry.path, "nome": entry.name, "ext": ext,
                "tamanho": tamanho, "modificado": modificado, "tipo": None,
            })
    return arquivos


def peek_tipo_arquivo(path):
    """Espia só a primeira linha do arquivo (rápido, não lê o arquivo
    inteiro) para descobrir se é Remessa ou Retorno, para mostrar na lista."""
    try:
        with open(path, "r", encoding="latin-1", errors="replace") as fh:
            primeira_linha = fh.readline()
    except OSError:
        return "?"
    primeira_linha = primeira_linha.rstrip("\r\n")
    if len(primeira_linha) <= 300 and primeira_linha[7:8] == "0":
        # CNAB240: Header de Arquivo (tipo de registro 0 na posição 8);
        # posição 143 = 1 (Remessa) ou 2 (Retorno).
        return {"1": "REM", "2": "RET"}.get(safe_slice(primeira_linha, 143, 143), "?")
    if primeira_linha[0:1] != "0":
        return "?"
    codigo = safe_slice(primeira_linha, 2, 2)
    if codigo == "1":
        return "REM"
    if codigo == "2":
        return "RET"
    upper = primeira_linha.upper()
    if "REMESSA" in upper:
        return "REM"
    if "RETORNO" in upper:
        return "RET"
    return "?"
