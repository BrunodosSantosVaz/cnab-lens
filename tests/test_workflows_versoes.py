"""Workflows das Actions: nenhuma action em versão que ainda roda em Node 20 (aviso "Node.js 20 is deprecated")
e nenhum job em `ubuntu-latest`, que migraria sozinho de Ubuntu (épico #106).

As versões mínimas são as primeiras de cada action que rodam em Node 24 (`runs.using: node24` no action.yml de
cada uma; o attest-build-provenance é composite e passa a usar o actions/attest em Node 24 na v3). Ao subir uma
action, suba aqui também; baixar abaixo do mínimo faz o teste falhar."""
import os
import re
import unittest

import _caminho

WORKFLOWS = os.path.join(_caminho.RAIZ, ".github", "workflows")

VERSAO_MINIMA = {
    "actions/checkout": 5,
    "actions/setup-python": 6,
    "actions/upload-artifact": 6,
    "actions/download-artifact": 7,
    "actions/attest-build-provenance": 3,
    "github/codeql-action/init": 4,
    "github/codeql-action/analyze": 4,
}
RUNNERS_PERMITIDOS = {"ubuntu-24.04", "windows-latest"}

USES = re.compile(r"^\s*-?\s*uses:\s*([\w./-]+)@v(\d+)\s*$", re.M)
RUNS_ON = re.compile(r"^\s*runs-on:\s*(\S+)\s*$", re.M)


def workflows():
    for nome in sorted(os.listdir(WORKFLOWS)):
        if nome.endswith((".yml", ".yaml")):
            with open(os.path.join(WORKFLOWS, nome), encoding="utf-8") as f:
                yield nome, f.read()


class VersoesDosWorkflows(unittest.TestCase):
    def test_actions_em_node_24(self):
        encontradas = set()
        for nome, texto in workflows():
            for action, versao in USES.findall(texto):
                encontradas.add(action)
                with self.subTest(workflow=nome, action=action):
                    self.assertIn(action, VERSAO_MINIMA, "action nova: confira a versão em Node 24 e inclua aqui")
                    self.assertGreaterEqual(int(versao), VERSAO_MINIMA[action])
        self.assertEqual(encontradas, set(VERSAO_MINIMA), "versão mínima de action que nenhum workflow usa mais")

    def test_runner_fixo(self):
        for nome, texto in workflows():
            for runner in RUNS_ON.findall(texto):
                with self.subTest(workflow=nome, runner=runner):
                    self.assertIn(runner, RUNNERS_PERMITIDOS)

    def test_toda_action_tem_versao(self):
        # "uses:" sem @vN (ex.: @main ou um sha) escaparia do teste acima
        for nome, texto in workflows():
            for linha in re.findall(r"^\s*-?\s*uses:\s*(\S+)", texto, re.M):
                with self.subTest(workflow=nome, uses=linha):
                    self.assertRegex(linha, r"@v\d+$")


if __name__ == "__main__":
    unittest.main()
