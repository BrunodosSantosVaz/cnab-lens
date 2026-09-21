# -*- coding: utf-8 -*-
"""Ajusta o sys.path para os testes importarem os módulos de src/ e scripts/."""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")
SCRIPTS = os.path.join(RAIZ, "scripts")
EXEMPLOS = os.path.join(RAIZ, "exemplos")

for pasta in (SRC, SCRIPTS):
    if pasta not in sys.path:
        sys.path.insert(0, pasta)


def exemplo(nome):
    return os.path.join(EXEMPLOS, nome)
