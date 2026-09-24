# -*- coding: utf-8 -*-
"""CNAB 240 Santander no leitor: segmentos com sub-código (Y-03, Y-53, Y-04 e os dois formatos do S),
agrupados por título, com arquivos sintéticos e dados fictícios."""
import os
import tempfile
import unittest

import _caminho  # noqa: F401
import cnab400_reader as reader


def valor_em(registro, inicio):
    """Valor do campo que começa na posição `inicio` (os nomes de campo podem se repetir dentro de um registro)."""
    return next(f["valor"] for f in registro.fields if f["inicio"] == inicio)


def linha(*pares):
    buf = [" "] * 240
    for inicio, valor in pares:
        for i, ch in enumerate(valor):
            buf[inicio - 1 + i] = ch
    return "".join(buf)


BANCO = (1, "033")


def header_arquivo(tipo):
    return linha(BANCO, (4, "0000"), (8, "0"), (73, "EMPRESA FICTICIA LTDA"), (103, "BANCO SANTANDER"),
                 (143, "1" if tipo == "Remessa" else "2"), (144, "21092026"), (164, "040"))


def header_lote(tipo):
    return linha(BANCO, (4, "0001"), (8, "1"), (9, "R" if tipo == "Remessa" else "T"), (10, "01"), (14, "040"))


def segmento(letra, seq, *pares, lote="0001"):
    return linha(BANCO, (4, lote), (8, "3"), (9, f"{seq:05d}"), (14, letra), *pares)


def trailer_lote(qtd):
    return linha(BANCO, (4, "0001"), (8, "5"), (18, f"{qtd:06d}"))


def trailer_arquivo(qtd):
    return linha(BANCO, (4, "9999"), (8, "9"), (18, "000001"), (24, f"{qtd:06d}"))


class ArquivoTemporario(unittest.TestCase):
    def abrir(self, linhas, layout=None):
        fd, caminho = tempfile.mkstemp(suffix=".rem")
        with os.fdopen(fd, "w", encoding="latin-1", newline="") as f:
            f.write("\r\n".join(linhas) + "\r\n")
        self.addCleanup(os.remove, caminho)
        cf = reader.CnabFile(caminho)  # o layout vem do banco do Header (033)
        if layout:
            cf.apply_layout(layout)
        return cf


class RemessaSantander240(ArquivoTemporario):
    TXID = "SANTANDERTXID000000000000000042"

    def arquivo(self):
        return self.abrir([
            header_arquivo("Remessa"), header_lote("Remessa"),
            segmento("P", 1, (16, "01"), (45, "0000000001234"), (58, "5"), (63, "NF-1001"),
                     (78, "25102026"), (86, "000000000015990")),
            segmento("Q", 2, (16, "01"), (18, "2"), (34, "CLIENTE FICTICIO")),
            segmento("Y", 3, (16, "01"), (18, "03"), (81, "1"), (82, "chave-pix-ficticia"), (159, self.TXID)),
            segmento("P", 4, (16, "01"), (45, "0000000001235"), (63, "NF-1002"), (78, "26102026"), (86, "000000000020000")),
            segmento("Q", 5, (16, "01"), (34, "OUTRO CLIENTE")),
            trailer_lote(7), trailer_arquivo(9),
        ])

    def test_layout_e_tipo(self):  # sem escolher o layout: a detecção automática pelo banco 033 basta
        cf = self.arquivo()
        self.assertEqual((cf.tipo_arquivo, cf.banco_codigo, cf.width), ("Remessa", "033", 240))
        self.assertEqual(cf.layout_key, "santander240")
        self.assertEqual(cf.layout.label, "CNAB240 Santander")

    def test_segmento_y_entra_no_titulo_e_leva_o_sub_codigo_no_rotulo(self):
        cf = self.arquivo()
        self.assertEqual(len(cf.detalhes), 2)
        primeiro = cf.detalhes[0]
        self.assertEqual([r.segmento for r in primeiro.records], ["P", "Q", "Y"])
        self.assertEqual([r.tipo_label for r in primeiro.records], [
            "Detalhe (Registro 3) - Segmento P", "Detalhe (Registro 3) - Segmento Q", "Detalhe (Registro 3) - Segmento Y-03"])

    def test_campos_do_y03_e_resumo_do_titulo(self):
        primeiro = self.arquivo().detalhes[0]
        y03 = primeiro.records[2]
        self.assertEqual(valor_em(y03, 81), "1")  # tipo de chave
        self.assertEqual(valor_em(y03, 82), "chave-pix-ficticia")
        self.assertEqual(valor_em(y03, 159), self.TXID)
        self.assertEqual(reader.format_data(primeiro.get("Data de Vencimento")), "25/10/2026")
        self.assertEqual(reader.format_valor_monetario(primeiro.get("Valor Nominal")), "159,90")
        self.assertEqual(primeiro.get("Número do Documento"), "NF-1001")
        self.assertEqual(primeiro.get("Código de Movimento"), "01")
        self.assertEqual(primeiro.get("Nome do Pagador"), "CLIENTE FICTICIO")

    def test_y_com_sub_codigo_desconhecido_cai_no_registro_bruto(self):
        cf = self.abrir([header_arquivo("Remessa"), header_lote("Remessa"),
                         segmento("P", 1, (63, "NF-1")), segmento("Y", 2, (18, "99")), trailer_lote(4), trailer_arquivo(6)])
        y = cf.detalhes[0].records[1]
        self.assertEqual(y.tipo_label, "Detalhe (Registro 3) - Segmento Y-99")
        self.assertEqual(y.fields[0]["nome"], "Conteúdo do Registro (não mapeado neste layout)")

    def test_y53_tipo_de_pagamento(self):
        cf = self.abrir([header_arquivo("Remessa"), header_lote("Remessa"), segmento("P", 1, (63, "NF-1")),
                         segmento("Y", 2, (18, "53"), (20, "01"), (22, "03"), (24, "2"), (25, "000000000012345")),
                         trailer_lote(4), trailer_arquivo(6)])
        y53 = cf.detalhes[0].records[1]
        self.assertEqual(y53.tipo_label, "Detalhe (Registro 3) - Segmento Y-53")
        self.assertEqual(y53.get("Quantidade de Pagamentos"), "03")
        self.assertEqual(y53.get("Valor Máximo"), "000000000012345")

    def test_segmento_s_escolhe_o_formato_pela_posicao_18(self):
        cf = self.abrir([header_arquivo("Remessa"), header_lote("Remessa"),
                         segmento("P", 1, (63, "NF-1")),
                         segmento("S", 2, (18, "1"), (19, "05"), (21, "2"), (22, "MENSAGEM LINHA CINCO")),
                         segmento("S", 3, (18, "2"), (19, "MENSAGEM CINCO")),
                         trailer_lote(5), trailer_arquivo(7)])
        s1, s2 = cf.detalhes[0].records[1:]
        self.assertEqual(s1.tipo_label, "Detalhe (Registro 3) - Segmento S-1")
        self.assertEqual(s1.get("Número da linha"), "05")
        self.assertEqual(s1.get("Mensagem a ser impressa"), "MENSAGEM LINHA CINCO")
        self.assertEqual(s2.tipo_label, "Detalhe (Registro 3) - Segmento S-2")
        self.assertEqual(s2.get("Mensagem 5"), "MENSAGEM CINCO")

    def test_trocar_de_layout_restaura_os_rotulos(self):
        cf = self.arquivo()
        cf.apply_layout("sicoob240")
        y = cf.detalhes[0].records[2]
        self.assertEqual(y.tipo_label, "Detalhe (Registro 3) - Segmento Y")
        self.assertEqual(y.fields[0]["nome"], "Conteúdo do Registro (não mapeado neste layout)")
        cf.apply_layout("santander240")
        self.assertEqual(cf.detalhes[0].records[2].tipo_label, "Detalhe (Registro 3) - Segmento Y-03")

    def test_header_e_trailer(self):
        cf = self.arquivo()
        self.assertEqual(cf.header.get("Nome da empresa"), "EMPRESA FICTICIA LTDA")
        self.assertEqual(cf.header.get("Nº da versão do layout do arquivo"), "040")
        nomes = " ".join(f["nome"] for f in cf.trailer.fields)
        self.assertIn("Quantidade de lotes", nomes)


class RetornoSantander240(ArquivoTemporario):
    def arquivo(self, tipo_inscricao_pagador="2"):
        return self.abrir([
            header_arquivo("Retorno"), header_lote("Retorno"),
            segmento("T", 1, (16, "06"), (41, "0000000001234"), (55, "NF-1001"), (70, "25102026"),
                     (78, "000000000015990"), (128, tipo_inscricao_pagador), (144, "CLIENTE FICTICIO")),
            segmento("U", 2, (16, "06"), (78, "000000000015990"), (138, "21092026"), (146, "22092026")),
            segmento("Y", 3, (16, "06"), (18, "03"), (82, "https://pix.exemplo.fictício/qr/abc"), (159, "TXIDRETORNO")),
            trailer_lote(5), trailer_arquivo(7),
        ])

    def test_retorno_agrupa_t_u_e_y03(self):
        cf = self.arquivo()
        self.assertEqual(cf.tipo_arquivo, "Retorno")
        self.assertEqual(len(cf.detalhes), 1)
        self.assertEqual([r.segmento for r in cf.detalhes[0].records], ["T", "U", "Y"])
        self.assertTrue(cf.detalhes[0].get("URL do QR Code").startswith("https://pix"))

    def test_resumo_de_retorno(self):
        grupo = self.arquivo().detalhes[0]
        self.assertEqual(grupo.get("Código de Movimento"), "06")
        self.assertEqual(reader.format_data(grupo.get("Data de Vencimento")), "25/10/2026")
        self.assertEqual(reader.format_valor_monetario(grupo.get("Pago")), "159,90")

    def test_descricao_do_movimento_vem_da_tabela_de_retorno(self):
        cf = self.arquivo()
        self.assertEqual(cf.layout.ocorrencia_codes["06"], "Liquidação do Boleto Efetivada")

    def test_y04_de_cheque(self):
        cf = self.abrir([header_arquivo("Retorno"), header_lote("Retorno"),
                         segmento("T", 1, (16, "06"), (55, "NF-1")), segmento("U", 2, (16, "06")),
                         segmento("Y", 3, (16, "06"), (18, "04"), (20, "CHEQUE FICTICIO 0001")),
                         trailer_lote(5), trailer_arquivo(7)])
        y04 = cf.detalhes[0].records[2]
        self.assertEqual(y04.tipo_label, "Detalhe (Registro 3) - Segmento Y-04")
        self.assertEqual(y04.get("Identificação do Cheque 1"), "CHEQUE FICTICIO 0001")
        self.assertEqual(y04.get("Identificação do Cheque 6"), "")


if __name__ == "__main__":
    unittest.main()
