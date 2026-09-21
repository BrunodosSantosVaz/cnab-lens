# -*- coding: utf-8 -*-
"""Os arquivos de exemplos/ têm que sair idênticos do scripts/gerar_exemplos.py."""
import os
import tempfile
import unittest

import _caminho
import gerar_exemplos


class ExemplosEmDia(unittest.TestCase):
    def test_gerador_reproduz_os_exemplos_versionados(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = gerar_exemplos.SAIDA
            gerar_exemplos.SAIDA = tmp
            try:
                gerar_exemplos.main()
            finally:
                gerar_exemplos.SAIDA = original
            gerados = sorted(os.listdir(tmp))
            versionados = sorted(os.listdir(_caminho.EXEMPLOS))
            self.assertEqual(gerados, versionados)
            for nome in gerados:
                with self.subTest(arquivo=nome):
                    with open(os.path.join(tmp, nome), "rb") as a, open(_caminho.exemplo(nome), "rb") as b:
                        self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
