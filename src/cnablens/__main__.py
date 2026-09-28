"""Ponto de entrada do CNABLens: `python -m cnablens`, ou este arquivo direto (é o que o PyInstaller
empacota nos compiladores de packaging/)."""
import os
import sys

if __package__ in (None, ""):
    # rodado como script (python src/cnablens/__main__.py ou executável do PyInstaller): torna o pacote
    # importável a partir da pasta que contém cnablens/
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cnablens.interface.app import main  # noqa: E402

if __name__ == "__main__":
    main()
