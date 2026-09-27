# -*- coding: utf-8 -*-
"""Gera o executável Linux (arquivo único) do CNABLens. Espelho do scripts/build_exe.py do Windows.

    python linux/build_linux.py                    # build-local/ (ignorada pelo git)
    python linux/build_linux.py --saida PASTA      # outra pasta
    python linux/build_linux.py --rc 2 --saida rc  # release candidata: CNABLens-v<versão>-rc.2-...

Para o executável rodar em qualquer distro, compile pelo linux/compilar.sh (container antigo,
glibc 2.28). Este script compila com o Python que o chamar, que precisa ter Tkinter.

Requer Python 3.10+ (com Tkinter) e PyInstaller (`pip install -r requirements-build.txt`).
Resultado, na pasta de saída:
    CNABLens-v<versão>[-rc.N]-linux-x64
    SHA256SUMS.txt          (hash para conferir o download)
As mesmas opções de empacotamento do Windows; o sufixo -rc.N só aparece no nome do arquivo.
"""
import argparse
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")
sys.path.insert(0, SRC)
from version import __version__  # noqa: E402

NOME = "CNABLens"


def nome_do_arquivo(rc=None):
    """Nome do executável: CNABLens-v0.2.0-linux-x64 (produção) ou CNABLens-v0.2.0-rc.1-linux-x64."""
    sufixo = f"-rc.{int(rc)}" if rc else ""
    return f"{NOME}-v{__version__}{sufixo}-linux-x64"


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Compila o CNABLens para Linux e guarda o executável com o hash SHA-256.")
    parser.add_argument("--saida", help="pasta de destino (padrão: build-local/)")
    parser.add_argument("--rc", type=int, help="número da release candidata (vira -rc.N no nome do arquivo)")
    args = parser.parse_args()
    destino_pasta = os.path.abspath(args.saida) if args.saida else os.path.join(RAIZ, "build-local")
    nome_final = nome_do_arquivo(args.rc)
    with tempfile.TemporaryDirectory(prefix="cnab-build-") as tmp:
        cmd = [
            sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", "--clean", "--noconfirm",
            "--name", NOME,
            "--distpath", os.path.join(tmp, "dist"), "--workpath", os.path.join(tmp, "work"), "--specpath", tmp,
            "--paths", SRC, os.path.join(SRC, "cnab400_reader.py"),
        ]
        print(" ".join(cmd))
        subprocess.run(cmd, check=True, cwd=SRC)
        gerado = os.path.join(tmp, "dist", NOME)
        os.makedirs(destino_pasta, exist_ok=True)
        for antigo in os.listdir(destino_pasta):  # nunca deixar executável/hash de builds anteriores misturados
            if antigo.endswith("-linux-x64") or antigo == "SHA256SUMS.txt":
                os.remove(os.path.join(destino_pasta, antigo))
        final = os.path.join(destino_pasta, nome_final)
        shutil.copyfile(gerado, final)
        os.chmod(final, os.stat(final).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    with open(os.path.join(destino_pasta, "SHA256SUMS.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{sha256(final)}  {nome_final}\n")
    print(f"\nOK: {os.path.relpath(final, RAIZ)}  ({os.path.getsize(final) / 1e6:.1f} MB)")
    print(f"SHA-256: {sha256(final)}")


if __name__ == "__main__":
    main()
