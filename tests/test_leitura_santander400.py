# -*- coding: utf-8 -*-
"""CNAB 400 Santander no leitor: registros opcionais (8 e 2/4-7 na remessa; 2 no retorno) agrupados sob o
Detalhe (tipo 1), com arquivos sintéticos e dados fictícios."""
import os
import tempfile
import unittest

import _caminho  # noqa: F401
import cnab400_reader as reader


def linha(*pares, largura=400):
    buf = [" "] * largura
    for inicio, valor in pares:
        for i, ch in enumerate(valor):
            buf[inicio - 1 + i] = ch
    return "".join(buf)


def header(tipo, banco="033"):
    return linha((1, "0"), (2, "1" if tipo == "Remessa" else "2"), (3, tipo.upper()), (10, "01"), (12, "COBRANCA"),
                 (47, "EMPRESA FICTICIA LTDA"), (77, banco), (80, "SANTANDER"), (95, "210926"), (395, "000001"))


def movimento(seq, doc, tipo="Remessa", movimento_cod="01", vencimento="251026", valor="0000000015990", pago=None):
    campos = [(1, "1"), (2, "02"), (4, "12345678000190"), (63, "00001234"), (108, "5"), (109, movimento_cod),
              (395, f"{seq:06d}")]
    if tipo == "Remessa":
        campos += [(111, doc), (121, vencimento), (127, valor), (235, "CLIENTE FICTICIO")]
    else:
        campos += [(117, doc), (147, vencimento), (153, valor), (302, "CLIENTE FICTICIO")]
        if pago:
            campos.append((254, pago))
    return linha(*campos)


def registro8(seq, txid):
    return linha((1, "8"), (2, "01"), (121, txid), (395, f"{seq:06d}"))


def registro(codigo, seq, **posicoes):
    return linha((1, codigo), *[(int(k[1:]), v) for k, v in posicoes.items()], (395, f"{seq:06d}"))


def trailer(seq):
    return linha((1, "9"), (395, f"{seq:06d}"))


class ArquivoTemporario(unittest.TestCase):
    def abrir(self, linhas):
        fd, caminho = tempfile.mkstemp(suffix=".rem")
        with os.fdopen(fd, "w", encoding="latin-1", newline="") as f:
            f.write("\r\n".join(linhas) + "\r\n")
        self.addCleanup(os.remove, caminho)
        return reader.CnabFile(caminho)


class RemessaSantander(ArquivoTemporario):
    TXID = "SANTANDERTXID000000000000000042"

    def arquivo(self):
        return self.abrir([
            header("Remessa"),
            movimento(2, "NF-1001"),
            registro8(3, self.TXID),
            registro("2", 4, p50="MENSAGEM FICTICIA DO RECIBO"),
            movimento(5, "NF-1002"),
            trailer(6),
        ])

    def test_reconhece_o_banco_e_escolhe_o_layout(self):
        cf = self.arquivo()
        self.assertEqual((cf.tipo_arquivo, cf.banco_codigo, cf.width), ("Remessa", "033", 400))
        self.assertEqual(cf.layout_key, "santander400")
        self.assertEqual(cf.layout.label, "CNAB400 Santander")

    def test_codigo_legado_353_tambem_escolhe_o_layout(self):
        cf = self.abrir([header("Remessa", banco="353"), movimento(2, "NF-1"), trailer(3)])
        self.assertEqual(cf.layout_key, "santander400")

    def test_registros_opcionais_ficam_no_lancamento_do_detalhe(self):
        cf = self.arquivo()
        self.assertEqual(len(cf.detalhes), 2)  # dois boletos, não quatro linhas
        primeiro, segundo = cf.detalhes
        self.assertEqual([r.tipo_char for r in primeiro.records], ["1", "8", "2"])
        self.assertEqual([r.tipo_char for r in segundo.records], ["1"])
        self.assertEqual(primeiro.index, 2)

    def test_rotulos_e_campos_de_cada_registro(self):
        primeiro = self.arquivo().detalhes[0]
        rotulos = [r.tipo_label for r in primeiro.records]
        self.assertEqual(rotulos[0], "Detalhe (Registro 1)")
        self.assertIn("Registro 8", rotulos[1])
        self.assertIn("QR Code", rotulos[1])
        self.assertIn("Registro 2", rotulos[2])
        self.assertIn("Mensagem", rotulos[2])
        self.assertEqual(primeiro.get("TXID"), self.TXID)
        self.assertTrue(primeiro.get("Mensagem variável por boleto (1ª").startswith("MENSAGEM FICTICIA"))

    def test_resumo_da_grade_le_o_registro_1(self):
        primeiro = self.arquivo().detalhes[0]
        self.assertEqual(reader.format_data(primeiro.get("Data de Vencimento")), "25/10/2026")
        self.assertEqual(reader.format_valor_monetario(primeiro.get("Valor Nominal")), "159,90")
        self.assertEqual(primeiro.get("Número do Documento"), "NF-1001")
        self.assertEqual(primeiro.get("Código de Movimento"), "01")
        self.assertEqual(primeiro.get("Nome do Pagador"), "CLIENTE FICTICIO")
        self.assertEqual(primeiro.get_concat("Nosso Número [") or primeiro.get("Nosso Número"), "00001234")

    def test_painel_mostra_separadores_entre_os_registros(self):
        nomes = [c["nome"] for c in self.arquivo().detalhes[0].fields if c.get("separador")]
        self.assertEqual(len(nomes), 3)
        self.assertTrue(all("linha" in n for n in nomes))

    def test_trocar_de_layout_desfaz_o_agrupamento_e_os_rotulos(self):
        cf = self.arquivo()
        cf.apply_layout("febraban")
        self.assertEqual(len(cf.detalhes), 2)
        self.assertTrue(all(isinstance(r, reader.CnabRecord) for r in cf.detalhes))
        extras = [r for r in cf.records if r.tipo_char in ("8", "2")]
        self.assertTrue(all(r.tipo_label.startswith("Desconhecido") for r in extras))
        cf.apply_layout("santander400")
        self.assertEqual(len(cf.detalhes[0].records), 3)
        self.assertIn("QR Code", cf.detalhes[0].records[1].tipo_label)

    def test_header_e_trailer_usam_os_campos_do_santander(self):
        cf = self.arquivo()
        self.assertEqual(cf.header.get("Código de Transmissão"), "")
        self.assertEqual(cf.header.get("Nome do Banco"), "SANTANDER")
        self.assertIn("Quantidade de registro", " ".join(f["nome"] for f in cf.trailer.fields))

    def test_registro_sem_descricao_nao_entra_no_lancamento(self):
        cf = self.abrir([header("Remessa"), movimento(2, "NF-1"), linha((1, "3"), (395, "000003")), trailer(4)])
        self.assertEqual(len(cf.detalhes), 1)
        self.assertEqual(len(cf.detalhes[0].records), 1)

    def test_registro_opcional_solto_antes_de_um_detalhe_nao_quebra(self):
        cf = self.abrir([header("Remessa"), registro8(2, self.TXID), movimento(3, "NF-1"), trailer(4)])
        self.assertEqual(len(cf.detalhes), 1)


class RetornoSantander(ArquivoTemporario):
    URL = "https://pix.exemplo.fictício/qr/abc123"

    def arquivo(self):
        return self.abrir([
            header("Retorno"),
            movimento(2, "NF-1001", tipo="Retorno", movimento_cod="06", pago="0000000015990"),
            registro("2", 3, p3=self.URL, p80="TXIDRETORNO000000000000000000001"),
            linha((1, "8"), (395, "000004")),  # o registro 8 não existe no retorno
            trailer(5),
        ])

    def test_retorno_agrupa_o_registro_2_de_qr_code(self):
        cf = self.arquivo()
        self.assertEqual(cf.tipo_arquivo, "Retorno")
        self.assertEqual(len(cf.detalhes), 1)
        grupo = cf.detalhes[0]
        self.assertEqual([r.tipo_char for r in grupo.records], ["1", "2"])  # o 8 não é do retorno
        self.assertIn("QR Code", grupo.records[1].tipo_label)
        self.assertTrue(grupo.get("Chave DICT").startswith("https://pix"))
        self.assertTrue(grupo.get("TXID").startswith("TXIDRETORNO"))

    def test_resumo_de_retorno(self):
        grupo = self.arquivo().detalhes[0]
        self.assertEqual(grupo.get("Código de Movimento"), "06")
        self.assertEqual(reader.format_valor_monetario(grupo.get("Pago")), "159,90")
        self.assertEqual(reader.format_data(grupo.get("Data de Vencimento")), "25/10/2026")

    def test_descricao_do_movimento_vem_da_tabela_do_retorno(self):
        cf = self.arquivo()
        self.assertEqual(cf.layout.ocorrencia_codes["06"], "Liquidação do Boleto Efetivada")


if __name__ == "__main__":
    unittest.main()
