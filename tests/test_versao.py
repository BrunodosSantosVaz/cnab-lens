# -*- coding: utf-8 -*-
"""versao.sh e atualizar_release.arquivo_de_versao: o ponto único que acha a versão, no pacote
(src/cnablens/version.py, v0.3.0+) ou na estrutura antiga (src/version.py, tags até a v0.2.0)."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import _caminho
from _bash import BASH, USAVEL, posix

SCRIPTS = os.path.join(_caminho.RAIZ, ".github", "scripts")
sys.path.insert(0, SCRIPTS)
import atualizar_release  # noqa: E402

VERSAO_SH = posix(os.path.join(SCRIPTS, "versao.sh"))


class Base(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.raiz, ignore_errors=True)

    def escrever(self, caminho, versao="0.3.0"):
        completo = os.path.join(self.raiz, caminho)
        os.makedirs(os.path.dirname(completo), exist_ok=True)
        with open(completo, "w", encoding="utf-8", newline="\n") as f:
            f.write(f'"""Versao."""\n\n__version__ = "{versao}"\n')


@unittest.skipUnless(USAVEL, "bash/git indisponíveis (roda no job scripts (Linux) do CI)")
class VersaoSh(Base):
    def rodar(self, *args):
        return subprocess.run([BASH, VERSAO_SH, *args], cwd=self.raiz, capture_output=True, text=True)

    def test_pacote(self):
        self.escrever("src/cnablens/version.py", "0.3.0")
        self.assertEqual(self.rodar().stdout.strip(), "0.3.0")
        self.assertEqual(self.rodar("--arquivo").stdout.strip(), "src/cnablens/version.py")

    def test_estrutura_antiga(self):
        self.escrever("src/version.py", "0.2.0")
        self.assertEqual(self.rodar().stdout.strip(), "0.2.0")
        self.assertEqual(self.rodar("--arquivo").stdout.strip(), "src/version.py")

    def test_pacote_tem_prioridade(self):
        self.escrever("src/version.py", "0.2.0")
        self.escrever("src/cnablens/version.py", "0.3.0")
        self.assertEqual(self.rodar().stdout.strip(), "0.3.0")

    def test_sem_arquivo_ou_sem_versao_e_erro(self):
        r = self.rodar()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Arquivo de versao nao encontrado", r.stderr)
        os.makedirs(os.path.join(self.raiz, "src"))
        with open(os.path.join(self.raiz, "src", "version.py"), "w", encoding="utf-8") as f:
            f.write("# sem versao\n")
        r = self.rodar()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Nao consegui ler __version__", r.stderr)


class ArquivoDeVersaoPython(Base):
    def test_mesma_regra_do_versao_sh(self):
        self.escrever("src/version.py")
        self.assertEqual(atualizar_release.arquivo_de_versao(self.raiz), os.path.join("src", "version.py"))
        self.escrever("src/cnablens/version.py")
        self.assertEqual(atualizar_release.arquivo_de_versao(self.raiz), os.path.join("src", "cnablens", "version.py"))

    def test_sem_arquivo(self):
        with self.assertRaises(SystemExit):
            atualizar_release.arquivo_de_versao(self.raiz)


class NenhumaLeituraFixa(unittest.TestCase):
    def test_esteira_usa_o_ponto_unico(self):
        pastas = [os.path.join(_caminho.RAIZ, ".github", "scripts"), os.path.join(_caminho.RAIZ, ".github", "workflows")]
        for pasta in pastas:
            for nome in os.listdir(pasta):
                if nome in ("versao.sh", "atualizar_release.py") or not nome.endswith((".sh", ".yml", ".py")):
                    continue
                with open(os.path.join(pasta, nome), encoding="utf-8") as f:
                    texto = f.read()
                with self.subTest(arquivo=nome):
                    self.assertNotRegex(texto, r"sed [^\n]*src/version\.py|git add src/version\.py")


if __name__ == "__main__":
    unittest.main()
