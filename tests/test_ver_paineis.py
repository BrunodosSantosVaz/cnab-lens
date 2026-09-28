"""ver-paineis.sh (e projeto.sh colunas / quadro): lista as issues abertas de cada coluna dos painéis,
na ordem do painel, com `gh` de mentira. Somente leitura: nenhuma mutação é chamada."""
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest

import _caminho
from _bash import BASH, USAVEL, posix

SCRIPT = posix(_caminho.RAIZ + "/.github/scripts/ver-paineis.sh")
PROJETO = posix(_caminho.RAIZ + "/.github/scripts/projeto.sh")

PAINEL = {"data": {"repositoryOwner": {"projectV2": {"id": "PVT_1", "field": {"options": [
    {"name": "A fazer"}, {"name": "Feature"}, {"name": "Code"}, {"name": "Aprovado"}]}}}}}


def item(numero, titulo, status=None, sprint=None, estado="OPEN", repo="dono/repo"):
    return {"status": {"name": status} if status else None, "sprint": {"title": sprint} if sprint else None,
            "content": {"number": numero, "title": titulo, "state": estado, "repository": {"nameWithOwner": repo}}}


ITENS = {"data": {"node": {"items": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": [
    item(12, "Tarefa em código", "Code", "Sprint 2"),
    item(10, "Tarefa nova", "A fazer"),
    item(11, "Outra nova", "A fazer", "Sprint 2"),
    item(13, "Sem coluna"),
    item(14, "Já publicada", "Aprovado", estado="CLOSED"),
    item(99, "De outro repositório", "Code", repo="dono/outro"),
]}}}}

# Responde conforme a consulta e aplica o --jq de verdade (jq), como o gh faria.
GH_FALSO = r'''#!/usr/bin/env bash
printf 'gh %s\n' "$(printf '%q ' "$@")" >> "$FIX/chamadas.log"
filtro="" consulta=""
args=("$@")
for ((i = 0; i < ${#args[@]}; i++)); do
  case "${args[i]}" in
    --jq) filtro="${args[i+1]}" ;;
    query=*) consulta="${args[i]}" ;;
  esac
done
if [[ "$consulta" == *"items("* ]]; then json=$(cat "$FIX/itens.json")
else json=$(cat "$FIX/painel.json"); fi
if [ -n "$filtro" ]; then jq -r "$filtro" <<<"$json"; else echo "$json"; fi
'''


@unittest.skipUnless(USAVEL and shutil.which("jq"), "bash/git/jq indisponíveis (roda no job scripts (Linux) do CI)")
class VerPaineis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.fix = os.path.join(self.tmp, "fix")
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.fix)
        os.makedirs(self.bin)
        gh = os.path.join(self.bin, "gh")
        with open(gh, "w", encoding="utf-8", newline="\n") as f:
            f.write(GH_FALSO)
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IXUSR)
        for nome, dados in (("painel.json", PAINEL), ("itens.json", ITENS)):
            with open(os.path.join(self.fix, nome), "w", encoding="utf-8") as f:
                json.dump(dados, f)
        self.resumo = os.path.join(self.tmp, "resumo.md")

    def rodar(self, script, *args, **extra):
        env = dict(os.environ, PATH=posix(self.bin) + os.pathsep + os.environ["PATH"], FIX=posix(self.fix),
                   PROJETO_OWNER="dono", GITHUB_REPOSITORY="dono/repo", PROJETO_PLANEJAMENTO="",
                   PROJETO_EXECUCAO="", PROJETO_BUGS="", GITHUB_STEP_SUMMARY="")
        env.update(extra)
        return subprocess.run([BASH, script, *args], env=env, capture_output=True, text=True)

    def chamadas(self):
        with open(os.path.join(self.fix, "chamadas.log"), encoding="utf-8") as f:
            return f.read()

    def test_colunas_na_ordem_do_painel(self):
        r = self.rodar(PROJETO, "colunas", "11")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines(), ["A fazer", "Feature", "Code", "Aprovado"])

    def test_quadro_so_issues_abertas_deste_repositorio(self):
        r = self.rodar(PROJETO, "quadro", "11")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines(), [
            "Code\t12\tTarefa em código\tSprint 2",
            "A fazer\t10\tTarefa nova\t-",
            "A fazer\t11\tOutra nova\tSprint 2",
            "-\t13\tSem coluna\t-",
        ])

    def test_lista_por_coluna_e_grava_o_resumo(self):
        r = self.rodar(SCRIPT, PROJETO_EXECUCAO="11", GITHUB_STEP_SUMMARY=posix(self.resumo))
        self.assertEqual(r.returncode, 0, r.stderr)
        esperado = ("## Execução (painel 11)\n\n"
                    "### A fazer\n\n- #10 Tarefa nova\n- #11 Outra nova (Sprint 2)\n\n"
                    "### Code\n\n- #12 Tarefa em código (Sprint 2)\n\n"
                    "### (sem coluna)\n\n- #13 Sem coluna\n")
        self.assertEqual(r.stdout, esperado)
        with open(self.resumo, encoding="utf-8") as f:
            self.assertEqual(f.read(), esperado)
        self.assertNotIn("Feature", r.stdout)  # coluna vazia não aparece
        self.assertNotIn("#14", r.stdout)       # fechada
        self.assertNotIn("#99", r.stdout)       # outro repositório

    def test_paineis_na_ordem_e_vazio_e_pulado(self):
        r = self.rodar(SCRIPT, PROJETO_PLANEJAMENTO="10", PROJETO_BUGS="12")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertLess(r.stdout.index("## Planejamento (painel 10)"), r.stdout.index("## Bugs (painel 12)"))
        self.assertNotIn("Execução", r.stdout)

    def test_painel_sem_issues(self):
        with open(os.path.join(self.fix, "itens.json"), "w", encoding="utf-8") as f:
            json.dump({"data": {"node": {"items": {"pageInfo": {"hasNextPage": False}, "nodes": []}}}}, f)
        r = self.rodar(SCRIPT, PROJETO_EXECUCAO="11")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Nenhuma issue aberta.", r.stdout)

    def test_somente_leitura(self):
        self.rodar(SCRIPT, PROJETO_PLANEJAMENTO="10", PROJETO_EXECUCAO="11", PROJETO_BUGS="12")
        self.assertNotIn("mutation", self.chamadas())


if __name__ == "__main__":
    unittest.main()
