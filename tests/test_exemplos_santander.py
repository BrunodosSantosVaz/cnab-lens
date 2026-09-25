# -*- coding: utf-8 -*-
"""Os quatro exemplos do Santander (exemplos/santander*): registros opcionais, QR Code/PIX e totais."""
import unittest

import _caminho
import cnab400_reader as app


def valor_em(registro, inicio):
    return next(f["valor"] for f in registro.fields if f["inicio"] == inicio)


class Santander400(unittest.TestCase):
    def test_remessa_o_primeiro_boleto_leva_qr_code_e_mensagem(self):
        cf = app.CnabFile(_caminho.exemplo("santander400_remessa.rem"))
        primeiro, segundo = cf.detalhes
        self.assertEqual([r.tipo_char for r in primeiro.records], ["1", "8", "2"])
        self.assertEqual([r.tipo_char for r in segundo.records], ["1"])
        qr = primeiro.records[1]
        self.assertEqual(valor_em(qr, 121), "SANTANDERTXID000000000000000042")
        self.assertEqual(valor_em(qr, 44), "chave-pix-ficticia@exemplo.com.br")
        self.assertTrue(valor_em(primeiro.records[2], 50).startswith("PAGUE ATE O VENCIMENTO"))

    def test_retorno_traz_o_registro_2_de_qr_code_no_primeiro_boleto(self):
        cf = app.CnabFile(_caminho.exemplo("santander400_retorno.ret"))
        primeiro, segundo = cf.detalhes
        self.assertEqual([r.tipo_char for r in primeiro.records], ["1", "2"])
        self.assertEqual([r.tipo_char for r in segundo.records], ["1"])
        self.assertTrue(valor_em(primeiro.records[1], 3).startswith("https://pix.exemplo.com.br/qr"))

    def test_trailer_da_remessa_soma_os_boletos(self):
        cf = app.CnabFile(_caminho.exemplo("santander400_remessa.rem"))
        self.assertEqual(cf.trailer.get("Quantidade de registro"), "000006")
        self.assertEqual(app.format_valor_monetario(cf.trailer.get("Valor Total")), "479,70")

    def test_nenhum_registro_fica_sem_descricao(self):
        for nome in ("santander400_remessa.rem", "santander400_retorno.ret"):
            cf = app.CnabFile(_caminho.exemplo(nome))
            for rec in cf.records:
                with self.subTest(arquivo=nome, linha=rec.index):
                    self.assertFalse(rec.tipo_label.startswith("Desconhecido"))
                    self.assertEqual((rec.fields[0]["inicio"], rec.fields[-1]["fim"]), (1, 400))


class Santander240(unittest.TestCase):
    def test_remessa_agrupa_p_q_e_y03(self):
        cf = app.CnabFile(_caminho.exemplo("santander240_remessa.rem"))
        self.assertEqual([[r.segmento for r in g.records] for g in cf.detalhes], [["P", "Q", "Y"], ["P", "Q"]])
        y = cf.detalhes[0].records[2]
        self.assertEqual(y.tipo_label, "Detalhe (Registro 3) - Segmento Y-03")
        self.assertEqual(valor_em(y, 159), "SANTANDERTXID000000000000000042")
        self.assertEqual(cf.detalhes[0].get("Nome do Pagador"), "MARIA EXEMPLO DA SILVA")

    def test_retorno_agrupa_t_u_e_y03(self):
        cf = app.CnabFile(_caminho.exemplo("santander240_retorno.ret"))
        self.assertEqual([[r.segmento for r in g.records] for g in cf.detalhes], [["T", "U", "Y"], ["T", "U"]])
        self.assertEqual(app.format_valor_monetario(cf.detalhes[0].get("Pago")), "159,90")
        self.assertTrue(valor_em(cf.detalhes[0].records[2], 82).startswith("https://pix.exemplo.com.br/qr"))

    def test_header_e_trailer_reunem_arquivo_e_lote(self):
        cf = app.CnabFile(_caminho.exemplo("santander240_retorno.ret"))
        self.assertEqual([r.tipo for r in cf.header.records], ["header_arquivo", "header_lote"])
        self.assertEqual([r.tipo for r in cf.trailer.records], ["trailer_lote", "trailer_arquivo"])
        self.assertEqual(cf.trailer.records[0].get("Quantidade de registros do lote"), "000007")
        self.assertEqual(cf.trailer.records[1].get("Quantidade de registros do arquivo"), "000009")

    def test_todo_campo_de_todo_registro_esta_mapeado(self):
        for nome in ("santander240_remessa.rem", "santander240_retorno.ret"):
            cf = app.CnabFile(_caminho.exemplo(nome))
            for rec in cf.records:
                with self.subTest(arquivo=nome, linha=rec.index):
                    self.assertNotEqual(rec.fields[0]["nome"], "Conteúdo do Registro (não mapeado neste layout)")
                    self.assertEqual((rec.fields[0]["inicio"], rec.fields[-1]["fim"]), (1, 240))

    def test_lotes_e_versoes_do_layout(self):
        cf = app.CnabFile(_caminho.exemplo("santander240_remessa.rem"))
        self.assertEqual(cf.header.records[0].get("Nº da versão do layout do arquivo"), "040")
        self.assertEqual(cf.header.records[1].get("Nº da versão do layout do lote"), "040")


if __name__ == "__main__":
    unittest.main()
