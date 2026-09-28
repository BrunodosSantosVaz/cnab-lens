# -*- coding: utf-8 -*-
"""Equivalência da leitura: a refatoração do épico #58 não pode mudar nada do que o programa mostra.

O retrato (tests/dados/equivalencia.json.gz) foi gerado com o código da v0.2.0, ANTES da refatoração:
para cada arquivo de exemplos/ e cada layout do mesmo tamanho de linha, guarda os dados do arquivo
(tipo, banco, empresa, data), todos os registros (tipo, rótulo e cada campo: nome, posição, valor bruto,
valor formatado como na tela e descrição) e o agrupamento em lançamentos, Header e Trailer.

Regerar SÓ quando uma mudança de comportamento for intencional (layout novo, campo corrigido):
    python tests/test_equivalencia.py --gerar
"""
import gzip
import json
import os
import sys
import unittest

import _caminho

from cnablens.formatacao import formatar_valor_campo
from cnablens.layouts import LAYOUT_ORDER, LAYOUTS
from cnablens.leitura import CnabFile

RETRATO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados", "equivalencia.json.gz")


def _campos(registro):
    return [[c["nome"], c["inicio"], c["fim"], c["valor"], formatar_valor_campo(c["nome"], c["valor"]),
             c["descricao"], bool(c.get("separador"))] for c in registro.fields]


def retrato():
    """Tudo o que a leitura produz para os exemplos, em todos os layouts compatíveis."""
    resultado = {}
    for nome in sorted(os.listdir(_caminho.EXEMPLOS)):
        arquivo = CnabFile(_caminho.exemplo(nome))
        for chave in LAYOUT_ORDER:
            if LAYOUTS[chave].width != arquivo.width:
                continue
            arquivo.apply_layout(chave)
            resultado[f"{nome}|{chave}"] = {
                "arquivo": [arquivo.width, arquivo.tipo_arquivo, arquivo.banco_codigo, arquivo.banco_nome,
                            arquivo.empresa_nome, arquivo.data_geracao, arquivo.layout_key],
                "registros": [[r.index, r.tipo, r.tipo_label, _campos(r)] for r in arquivo.records],
                "header": _campos(arquivo.header) if arquivo.header is not None else None,
                "trailer": _campos(arquivo.trailer) if arquivo.trailer is not None else None,
                "lancamentos": [[d.index, _campos(d)] for d in arquivo.detalhes],
            }
    return resultado


class Equivalencia(unittest.TestCase):
    def test_leitura_identica_a_da_v0_2_0(self):
        with gzip.open(RETRATO, "rt", encoding="utf-8") as f:
            esperado = json.load(f)
        atual = json.loads(json.dumps(retrato()))  # mesma normalização (tuplas viram listas)
        self.assertEqual(sorted(atual), sorted(esperado), "arquivos x layouts diferentes")
        for chave in sorted(esperado):
            with self.subTest(exemplo_e_layout=chave):
                for parte in ("arquivo", "header", "trailer", "lancamentos", "registros"):
                    self.assertEqual(atual[chave][parte], esperado[chave][parte], f"{chave}: {parte}")


if __name__ == "__main__":
    if "--gerar" in sys.argv:
        os.makedirs(os.path.dirname(RETRATO), exist_ok=True)
        with gzip.open(RETRATO, "wt", encoding="utf-8") as f:
            json.dump(retrato(), f, ensure_ascii=False, sort_keys=True)
        print(f"Retrato gravado em {RETRATO}")
    else:
        unittest.main()
