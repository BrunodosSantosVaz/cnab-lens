# -*- coding: utf-8 -*-
"""Confere todos os layouts: `python -m cnablens.layouts` (a partir de src/, ou com `pip install -e .`).

Cada lista de campos (`*_FIELDS`) de cada módulo de banco precisa cobrir a linha inteira, sem lacunas.
Os testes (tests/test_layouts.py) fazem a mesma conferência a cada PR."""
from cnablens.layouts import febraban400, santander240, santander400, sicoob240, sicoob400, sicredi400
from cnablens.layouts.base import validar_contiguidade

MODULOS = ((febraban400, 400), (sicredi400, 400), (sicoob400, 400), (santander400, 400),
           (sicoob240, 240), (santander240, 240))


def listas_de_campos(modulo):
    """As listas de campos de um módulo de banco: as variáveis `*_FIELDS`."""
    return [(nome, valor) for nome, valor in sorted(vars(modulo).items())
            if nome.endswith("_FIELDS") and isinstance(valor, list)]


def main():
    for modulo, largura in MODULOS:
        for nome, campos in listas_de_campos(modulo):
            validar_contiguidade(campos, largura, f"{modulo.__name__}.{nome}")
            print(f"OK  {modulo.__name__.rsplit('.', 1)[-1]:<13} {nome:<46} {len(campos):>3} campos, 1-{largura}")
    print("Todos os layouts cobrem a linha inteira, sem lacunas.")


if __name__ == "__main__":
    main()
