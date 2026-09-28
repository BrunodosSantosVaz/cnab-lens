# -*- coding: utf-8 -*-
"""Documentação: os links relativos dos documentos principais apontam para arquivos que existem, e
nenhum documento cita a antiga pasta releases/ do repositório (os executáveis ficam só nas Releases)."""
import os
import re
import unittest

import _caminho

DOCUMENTOS = ["README.md", "CONTRIBUTING.md", "SECURITY.md", "docs/processo.md", "packaging/linux/README.md"]
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


class Documentacao(unittest.TestCase):
    def ler(self, doc):
        with open(os.path.join(_caminho.RAIZ, doc), encoding="utf-8") as f:
            return f.read()

    def test_links_relativos_existem(self):
        for doc in DOCUMENTOS:
            base = os.path.dirname(os.path.join(_caminho.RAIZ, doc))
            for alvo in LINK.findall(self.ler(doc)):
                if re.match(r"[a-z]+:", alvo):  # http:, https:, mailto:
                    continue
                with self.subTest(doc=doc, link=alvo):
                    self.assertTrue(os.path.exists(os.path.normpath(os.path.join(base, alvo))), f"{doc}: {alvo}")

    def test_nenhum_documento_cita_a_pasta_releases_do_repositorio(self):
        for doc in DOCUMENTOS:
            texto = re.sub(r"https://github\.com/\S+", "", self.ler(doc))  # as páginas de Release continuam
            with self.subTest(doc=doc):
                self.assertNotRegex(texto, r"(?<![\w/])releases/(?!latest)")

    def test_milestone_e_so_versao_real(self):
        for doc in DOCUMENTOS:
            with self.subTest(doc=doc):
                self.assertNotRegex(self.ler(doc), r"v\d+\.\d+\.\d+-nc")
        processo = self.ler("docs/processo.md")
        self.assertIn("## Sprint não é versão", processo)
        self.assertIn("Milestone é só versão real", processo)

    def test_branch_de_release_e_temporaria_e_rollback_pela_tag(self):
        processo = self.ler("docs/processo.md")
        self.assertIn("### Voltar a uma versão antiga (rollback)", processo)
        self.assertIn("git switch --detach v0.1.0", processo)
        self.assertIn("### Como a `release/x.y.z` é apagada (travas de segurança)", processo)
        self.assertIn("Tags nunca são apagadas nem movidas", processo)
        for doc in DOCUMENTOS:
            with self.subTest(doc=doc):
                self.assertNotRegex(self.ler(doc), r"release/\*`?\s*\n?\s*fica|\*\*fica\*\* como histórico")

    def test_linux_documentado_no_readme(self):
        readme = self.ler("README.md")
        for trecho in ("packaging/linux/README.md", "CNABLens-vX.Y.Z-linux-x64", "SHA256SUMS-linux.txt", "bash packaging/linux/compilar.sh"):
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, readme)


if __name__ == "__main__":
    unittest.main()
