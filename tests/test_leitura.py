# -*- coding: utf-8 -*-
"""Leitura dos arquivos de exemplo: formato, tipo, banco, layout automático e resumo dos lançamentos."""
import os
import tempfile
import unittest

import _caminho
import cnab400_reader as app

# arquivo -> (layout automático, tipo, largura, banco)
ESPERADO = {
    "febraban_remessa.rem": ("febraban", "Remessa", 400, "341"),
    "febraban_retorno.ret": ("febraban", "Retorno", 400, "341"),
    "sicredi_remessa.rem": ("sicredi", "Remessa", 400, "748"),
    "sicredi_retorno.ret": ("sicredi", "Retorno", 400, "748"),
    "sicoob400_remessa.rem": ("sicoob400", "Remessa", 400, "756"),
    "sicoob400_retorno.ret": ("sicoob400", "Retorno", 400, "756"),
    "sicoob240_remessa.rem": ("sicoob240", "Remessa", 240, "756"),
    "sicoob240_retorno.ret": ("sicoob240", "Retorno", 240, "756"),
    "santander400_remessa.rem": ("santander400", "Remessa", 400, "033"),
    "santander400_retorno.ret": ("santander400", "Retorno", 400, "033"),
    "santander240_remessa.rem": ("santander240", "Remessa", 240, "033"),
    "santander240_retorno.ret": ("santander240", "Retorno", 240, "033"),
}


def ocorrencia(rec):
    return (rec.get("Código da Ocorrência") or rec.get("Identificação da Ocorrência")
            or rec.get("Código de Movimento") or rec.get("comando"))


class ArquivosDeExemplo(unittest.TestCase):
    def test_layout_tipo_e_banco_detectados(self):
        for nome, (layout, tipo, largura, banco) in ESPERADO.items():
            with self.subTest(arquivo=nome):
                cf = app.CnabFile(_caminho.exemplo(nome))
                self.assertEqual(cf.layout_key, layout)
                self.assertEqual(cf.tipo_arquivo, tipo)
                self.assertEqual(cf.width, largura)
                self.assertEqual(cf.banco_codigo, banco)
                self.assertEqual(cf.data_geracao, "21/09/2026")
                self.assertEqual(len(cf.detalhes), 2)
                self.assertIsNotNone(cf.header)
                self.assertIsNotNone(cf.trailer)

    def test_resumo_dos_lancamentos(self):
        for nome in ESPERADO:
            with self.subTest(arquivo=nome):
                cf = app.CnabFile(_caminho.exemplo(nome))
                rec = cf.detalhes[0]
                self.assertEqual(app.format_data(rec.get("Data de Vencimento")), "25/10/2026")
                self.assertEqual(app.format_valor_monetario(rec.get("Valor Nominal") or rec.get("Valor do Título")), "159,90")
                self.assertTrue((rec.get("Número do Documento") or rec.get("Seu Número")).startswith("NF-"))
                self.assertIn(ocorrencia(rec), ("01", "06"))

    def test_retorno_traz_ocorrencias_de_liquidacao(self):
        for nome, (_, tipo, *_resto) in ESPERADO.items():
            if tipo != "Retorno":
                continue
            with self.subTest(arquivo=nome):
                cf = app.CnabFile(_caminho.exemplo(nome))
                self.assertEqual([ocorrencia(r) for r in cf.detalhes], ["06", "02"])
                pago = cf.detalhes[0].get("Pago", "0")
                self.assertEqual(app.format_valor_monetario(pago), "159,90")

    def test_lista_de_arquivos_mostra_remessa_ou_retorno(self):
        for nome, (_, tipo, *_resto) in ESPERADO.items():
            with self.subTest(arquivo=nome):
                self.assertEqual(app.peek_tipo_arquivo(_caminho.exemplo(nome)), "REM" if tipo == "Remessa" else "RET")


class Cnab240(unittest.TestCase):
    def test_titulo_agrupa_os_segmentos(self):
        rem = app.CnabFile(_caminho.exemplo("sicoob240_remessa.rem"))
        self.assertEqual([[r.segmento for r in g.records] for g in rem.detalhes], [["P", "Q"], ["P", "Q"]])
        ret = app.CnabFile(_caminho.exemplo("sicoob240_retorno.ret"))
        self.assertEqual([[r.segmento for r in g.records] for g in ret.detalhes], [["T", "U"], ["T", "U"]])

    def test_pagador_vem_do_segmento_q_e_valor_pago_do_u(self):
        rem = app.CnabFile(_caminho.exemplo("sicoob240_remessa.rem"))
        self.assertEqual(rem.detalhes[0].get("Nome do Pagador"), "MARIA EXEMPLO DA SILVA")
        ret = app.CnabFile(_caminho.exemplo("sicoob240_retorno.ret"))
        self.assertEqual(app.format_valor_monetario(ret.detalhes[0].get("Pago")), "159,90")

    def test_header_e_trailer_reunem_arquivo_e_lote(self):
        cf = app.CnabFile(_caminho.exemplo("sicoob240_retorno.ret"))
        self.assertEqual([r.tipo for r in cf.header.records], ["header_arquivo", "header_lote"])
        self.assertEqual([r.tipo for r in cf.trailer.records], ["trailer_lote", "trailer_arquivo"])

    def test_painel_lista_todos_os_campos_com_separador_por_segmento(self):
        cf = app.CnabFile(_caminho.exemplo("sicoob240_remessa.rem"))
        separadores = [f for f in cf.detalhes[0].fields if f.get("separador")]
        self.assertEqual(len(separadores), 2)
        self.assertIn("Segmento P", separadores[0]["nome"])

    def test_todo_campo_de_todo_registro_esta_mapeado(self):
        cf = app.CnabFile(_caminho.exemplo("sicoob240_remessa.rem"))
        for rec in cf.records:
            with self.subTest(linha=rec.index):
                self.assertEqual(rec.fields[0]["inicio"], 1)
                self.assertEqual(rec.fields[-1]["fim"], 240)


class Robustez(unittest.TestCase):
    def escrever(self, conteudo, nome="x.txt"):
        pasta = tempfile.mkdtemp()
        caminho = os.path.join(pasta, nome)
        with open(caminho, "w", encoding="latin-1", newline="") as f:
            f.write(conteudo)
        self.addCleanup(lambda: (os.remove(caminho), os.rmdir(pasta)))
        return caminho

    def test_arquivo_vazio_gera_erro_claro(self):
        with self.assertRaises(ValueError):
            app.CnabFile(self.escrever(""))

    def test_linhas_curtas_nao_quebram(self):
        cf = app.CnabFile(self.escrever("0" + "1" * 30 + "\r\n1abc\r\n9\r\n"))
        self.assertEqual(len(cf.records), 3)

    def test_troca_de_layout_reaplica_sem_reler(self):
        cf = app.CnabFile(_caminho.exemplo("sicredi_retorno.ret"))
        cf.apply_layout("febraban")
        self.assertEqual(cf.layout_key, "febraban")
        cf.apply_layout("sicredi")
        self.assertEqual(cf.layout_key, "sicredi")

    def test_layout_de_outra_largura_cai_no_padrao_da_largura(self):
        cf = app.CnabFile(_caminho.exemplo("sicredi_retorno.ret"))
        cf.apply_layout("sicoob240")
        self.assertEqual(cf.layout_key, "febraban")


if __name__ == "__main__":
    unittest.main()
