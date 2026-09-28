# -*- coding: utf-8 -*-
"""pyproject.toml: válido, versão lida de src/version.py e sem duplicar a versão nem a dependência de build."""
import os
import re
import unittest

import _caminho

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 (job de compatibilidade): o CI principal roda o teste
    tomllib = None

CAMINHO = os.path.join(_caminho.RAIZ, "pyproject.toml")


@unittest.skipIf(tomllib is None, "tomllib precisa do Python 3.11+")
class Pyproject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CAMINHO, "rb") as f:
            cls.dados = tomllib.load(f)
        cls.projeto = cls.dados["project"]

    def test_metadados_basicos(self):
        self.assertEqual(self.projeto["name"], "cnablens")
        self.assertEqual(self.projeto["license"], "MIT")
        self.assertIn("Windows e Linux", self.projeto["description"])

    def test_versao_so_em_src_version_py(self):
        self.assertNotIn("version", self.projeto)  # nunca fixa a versão aqui
        self.assertEqual(self.projeto["dynamic"], ["version"])
        attr = self.dados["tool"]["setuptools"]["dynamic"]["version"]["attr"]
        modulo = attr.rsplit(".", 1)[0].replace(".", os.sep) + ".py"
        pasta = self.dados["tool"]["setuptools"]["package-dir"][""]
        self.assertTrue(os.path.isfile(os.path.join(_caminho.RAIZ, pasta, modulo)), attr)

    def test_python_minimo_igual_ao_do_readme(self):
        with open(os.path.join(_caminho.RAIZ, "README.md"), encoding="utf-8") as f:
            readme = f.read()
        minimo = re.search(r"python-(\d+\.\d+)%2B", readme).group(1)
        self.assertEqual(self.projeto["requires-python"], f">={minimo}")

    def test_sem_dependencias_duplicadas(self):
        # o programa só usa a biblioteca padrão; o PyInstaller fica só no requirements-build.txt
        self.assertEqual(self.projeto["dependencies"], [])
        self.assertNotIn("optional-dependencies", self.projeto)
        with open(CAMINHO, encoding="utf-8") as f:
            self.assertNotIn("pyinstaller>=", f.read().lower())

    def test_ruff_configurado(self):
        ruff = self.dados["tool"]["ruff"]
        self.assertEqual(ruff["target-version"], "py310")
        self.assertIn("F", ruff["lint"]["select"])


if __name__ == "__main__":
    unittest.main()
