# -*- coding: utf-8 -*-
"""Estrutura do pacote cnablens (épico #58): cada parte com uma responsabilidade.

- a leitura, a formatação e os layouts funcionam sem Tkinter (a interface só apresenta);
- nenhum módulo de código passa de ~400 linhas (os módulos de dados de layout são exceção);
- o ponto de entrada é o do pacote."""
import os
import subprocess
import sys
import unittest

import _caminho

PACOTE = os.path.join(_caminho.SRC, "cnablens")
LIMITE_DE_LINHAS = 400
DADOS_DE_LAYOUT = {"febraban400.py", "sicredi400.py", "sicoob400.py", "santander400.py", "sicoob240.py", "santander240.py",
                   "bancos.py"}


class SemInterface(unittest.TestCase):
    def test_leitura_formatacao_e_layouts_nao_dependem_do_tkinter(self):
        codigo = (
            "import sys; sys.modules['tkinter'] = None\n"  # qualquer import do tkinter falha
            "import cnablens.formatacao, cnablens.layouts, cnablens.leitura, cnablens.leitura.pasta\n"
            "from cnablens.leitura import CnabFile\n"
            f"arquivo = CnabFile({_caminho.exemplo('sicredi_retorno.ret')!r})\n"
            "assert arquivo.detalhes, 'sem lançamentos'\n"
            "print('ok')\n"
        )
        r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True,
                           env=dict(os.environ, PYTHONPATH=_caminho.SRC))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "ok")


class TamanhoDosModulos(unittest.TestCase):
    def test_modulos_de_codigo_curtos(self):
        for pasta, _, arquivos in os.walk(PACOTE):
            for nome in arquivos:
                if not nome.endswith(".py") or nome in DADOS_DE_LAYOUT:
                    continue
                caminho = os.path.join(pasta, nome)
                with open(caminho, encoding="utf-8") as f:
                    linhas = sum(1 for _ in f)
                with self.subTest(modulo=os.path.relpath(caminho, _caminho.SRC)):
                    self.assertLessEqual(linhas, LIMITE_DE_LINHAS)


class PontoDeEntrada(unittest.TestCase):
    def test_main_do_pacote(self):
        with open(os.path.join(PACOTE, "__main__.py"), encoding="utf-8") as f:
            self.assertIn("from cnablens.interface.app import main", f.read())
        self.assertFalse(os.path.exists(os.path.join(PACOTE, "app.py")))  # a interface fica em interface/


if __name__ == "__main__":
    unittest.main()
