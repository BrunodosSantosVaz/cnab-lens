"""CNABLens: lente para arquivos CNAB (remessa e retorno de cobrança, CNAB 400 e 240).

Pacotes:
    cnablens.layouts   layouts dos bancos (campos, posições e tabelas de códigos) e o registro deles
    cnablens.app       leitura dos arquivos e interface gráfica (Tkinter)

Ponto de entrada: `python -m cnablens` (cnablens/__main__.py), que é também o que os compiladores
de packaging/ empacotam.
"""

from cnablens.version import __version__

__all__ = ["__version__"]
