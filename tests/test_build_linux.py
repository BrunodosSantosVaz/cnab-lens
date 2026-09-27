# -*- coding: utf-8 -*-
"""Compilador Linux (linux/build_linux.py e linux/compilar.sh). Não roda o PyInstaller nem o Docker."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import _caminho  # noqa: F401
from _bash import BASH, USAVEL, posix
from version import __version__

LINUX = os.path.join(_caminho.RAIZ, "linux")
if LINUX not in sys.path:
    sys.path.insert(0, LINUX)
import build_exe  # noqa: E402
import build_linux  # noqa: E402

COMPILAR = os.path.join(LINUX, "compilar.sh")


class NomeDoArquivo(unittest.TestCase):
    def test_producao_nao_tem_sufixo(self):
        self.assertEqual(build_linux.nome_do_arquivo(), f"CNABLens-v{__version__}-linux-x64")

    def test_candidata_leva_rc_no_nome(self):
        self.assertEqual(build_linux.nome_do_arquivo(3), f"CNABLens-v{__version__}-rc.3-linux-x64")

    def test_mesmo_padrao_do_windows(self):
        for rc in (None, 2):
            self.assertEqual(build_linux.nome_do_arquivo(rc).replace("-linux-x64", ""),
                             build_exe.nome_do_arquivo(rc).replace("-windows-x64.exe", ""))


@unittest.skipUnless(USAVEL, "bash/git indisponíveis (roda no job scripts (Linux) do CI)")
class Compilar(unittest.TestCase):
    def rodar(self, *args):
        return subprocess.run([BASH, posix(COMPILAR), *args], capture_output=True, text=True, timeout=60)

    def test_sintaxe(self):
        r = subprocess.run([BASH, "-n", posix(COMPILAR)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_ajuda(self):
        r = self.rodar("--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("linux/compilar.sh v0.2.0", r.stdout)

    def test_argumento_desconhecido_para(self):
        r = self.rodar("--nao-existe")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Argumento desconhecido", r.stderr)

    def test_rc_precisa_ser_numero(self):
        r = self.rodar("--rc", "x")
        self.assertEqual(r.returncode, 2)

    def test_tag_inexistente_para_sem_gerar_nada(self):
        saida = tempfile.mkdtemp(prefix="cnab-teste-")
        self.addCleanup(shutil.rmtree, saida, True)
        r = self.rodar("v99.99.99", "--saida", posix(saida))
        self.assertEqual(r.returncode, 1)
        self.assertIn("A tag v99.99.99 não existe", r.stderr)
        self.assertEqual(os.listdir(saida), [])


if __name__ == "__main__":
    unittest.main()
