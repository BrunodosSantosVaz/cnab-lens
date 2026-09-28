# -*- coding: utf-8 -*-
"""Ajusta o sys.path para os testes importarem os módulos de src/, scripts/ e dos compiladores (packaging/)."""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")
SCRIPTS = os.path.join(RAIZ, "scripts")
PACKAGING = os.path.join(RAIZ, "packaging")
EXEMPLOS = os.path.join(RAIZ, "exemplos")

for pasta in (SRC, SCRIPTS, os.path.join(PACKAGING, "windows"), os.path.join(PACKAGING, "linux")):
    if pasta not in sys.path:
        sys.path.insert(0, pasta)


def exemplo(nome):
    return os.path.join(EXEMPLOS, nome)
