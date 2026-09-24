# -*- coding: utf-8 -*-
"""Layout CNAB 240 do Santander (cnab240_layout_santander): posições e tabelas conferidas com o manual
H7815 v8.5 (fev/2026). Cada asserção cita a posição do manual."""
import unittest

import _caminho  # noqa: F401
import cnab240_layout_santander as s


def campo_em(lista, inicio):
    for campo in lista:
        if campo[1] == inicio:
            return campo
    raise AssertionError(f"nenhum campo começa em {inicio}")


class Base(unittest.TestCase):
    def confere(self, lista, inicio, fim, trecho):
        nome, ini, f, _ = campo_em(lista, inicio)
        self.assertEqual((ini, f), (inicio, fim), nome)
        self.assertIn(trecho.lower(), nome.lower())


class Headers(Base):
    def test_header_de_arquivo_remessa(self):
        h = s.HEADER_ARQUIVO_REMESSA_FIELDS
        self.confere(h, 1, 3, "código do banco")
        self.confere(h, 18, 32, "inscrição da empresa")
        self.confere(h, 33, 47, "código de transmissão")
        self.confere(h, 73, 102, "nome da empresa")
        self.confere(h, 103, 132, "nome do banco")
        self.confere(h, 143, 143, "código remessa")
        self.confere(h, 144, 151, "data de geração")
        self.confere(h, 164, 166, "versão do layout")

    def test_header_de_arquivo_retorno(self):
        h = s.HEADER_ARQUIVO_RETORNO_FIELDS
        self.confere(h, 33, 36, "agência")
        self.confere(h, 38, 46, "conta corrente")
        self.confere(h, 53, 61, "código do beneficiário")
        self.confere(h, 143, 143, "retorno")

    def test_header_de_lote(self):
        r = s.HEADER_LOTE_REMESSA_FIELDS
        self.confere(r, 14, 16, "versão do layout do lote")
        self.confere(r, 54, 68, "código de transmissão")
        self.confere(r, 74, 103, "nome do beneficiário")
        self.confere(r, 104, 143, "mensagem 1")
        self.confere(r, 184, 191, "número remessa")
        t = s.HEADER_LOTE_RETORNO_FIELDS
        self.confere(t, 34, 42, "código do beneficiário")
        self.confere(t, 54, 57, "agência")
        self.confere(t, 184, 191, "número do retorno")


class Segmentos(Base):
    def test_segmento_p(self):
        p = s.SEGMENTO_P_REMESSA_FIELDS
        self.confere(p, 14, 14, "segmento")
        self.confere(p, 16, 17, "código de movimento")
        self.confere(p, 45, 57, "nosso número")
        self.confere(p, 58, 58, "tipo de cobrança")
        self.confere(p, 59, 59, "cadastramento")
        self.confere(p, 60, 60, "tipo de documento")
        self.confere(p, 63, 77, "número do documento")
        self.confere(p, 78, 85, "data de vencimento")
        self.confere(p, 86, 100, "valor nominal")
        self.confere(p, 107, 108, "espécie")
        self.confere(p, 118, 118, "juros de mora")
        self.confere(p, 142, 142, "desconto 1")
        self.confere(p, 196, 220, "identificação do boleto na empresa")
        self.confere(p, 221, 221, "protesto")

    def test_segmento_q_e_r(self):
        q = s.SEGMENTO_Q_REMESSA_FIELDS
        self.confere(q, 18, 18, "tipo de inscrição do pagador")
        self.confere(q, 34, 73, "nome do pagador")
        self.confere(q, 74, 113, "endereço")
        self.confere(q, 154, 154, "beneficiário final")
        r = s.SEGMENTO_R_REMESSA_FIELDS
        self.confere(r, 18, 18, "desconto 2")
        self.confere(r, 66, 66, "multa")
        self.confere(r, 100, 139, "mensagem 3")

    def test_segmento_s_tem_dois_formatos_pela_posicao_18(self):
        s1, s2 = s.SEGMENTO_S_1_REMESSA_FIELDS, s.SEGMENTO_S_2_REMESSA_FIELDS
        self.assertEqual(s1[:7], s2[:7])  # posições 1-17 são comuns
        self.confere(s1, 18, 18, "identificação da impressão")
        self.confere(s1, 22, 121, "mensagem a ser impressa")
        self.confere(s2, 18, 18, "identificação da impressão")
        self.confere(s2, 19, 58, "mensagem 5")
        self.confere(s2, 179, 218, "mensagem 9")

    def test_segmento_t(self):
        t = s.SEGMENTO_T_RETORNO_FIELDS
        self.confere(t, 16, 17, "código de movimento")
        self.confere(t, 41, 53, "nosso número")
        self.confere(t, 54, 54, "carteira")
        self.confere(t, 55, 69, "número do documento")
        self.confere(t, 70, 77, "data de vencimento")
        self.confere(t, 78, 92, "valor nominal")
        self.confere(t, 144, 183, "nome do pagador")
        self.confere(t, 194, 208, "tarifa")
        self.confere(t, 209, 218, "rejeições")

    def test_segmento_u(self):
        u = s.SEGMENTO_U_RETORNO_FIELDS
        self.confere(u, 18, 32, "juros")
        self.confere(u, 48, 62, "abatimento")
        self.confere(u, 78, 92, "valor pago")
        self.confere(u, 93, 107, "liquido")
        self.confere(u, 138, 145, "data da ocorrência")
        self.confere(u, 146, 153, "efetivação")
        self.confere(u, 154, 157, "código da ocorrência do pagador")

    def test_trailers(self):
        self.confere(s.TRAILER_LOTE_REMESSA_FIELDS, 18, 23, "quantidade de registros")
        self.confere(s.TRAILER_ARQUIVO_REMESSA_FIELDS, 18, 23, "lotes")
        self.confere(s.TRAILER_ARQUIVO_REMESSA_FIELDS, 24, 29, "registros do arquivo")
        t = s.TRAILER_LOTE_RETORNO_FIELDS
        self.confere(t, 24, 29, "cobrança simples")
        self.confere(t, 30, 46, "valor total")
        self.confere(t, 99, 115, "descontada")
        self.confere(t, 116, 123, "aviso de lançamento")

    def test_segmento_y(self):
        y03 = s.SEGMENTO_Y03_REMESSA_FIELDS
        self.confere(y03, 14, 14, "segmento")
        self.confere(y03, 18, 19, "identificação registro")
        self.confere(y03, 81, 81, "tipo de chave pix")
        self.confere(y03, 82, 158, "chave pix")
        self.confere(y03, 159, 193, "qr code")
        y53 = s.SEGMENTO_Y53_REMESSA_FIELDS
        self.confere(y53, 18, 19, "identificação registro")
        self.confere(y53, 20, 21, "tipo de pagamento")
        self.confere(y53, 22, 23, "quantidade de pagamentos")
        self.confere(y53, 25, 39, "máximo")
        self.confere(y53, 41, 55, "mínimo")
        r03 = s.SEGMENTO_Y03_RETORNO_FIELDS
        self.confere(r03, 82, 158, "url do qr code")
        self.confere(r03, 159, 193, "qr code")
        y04 = s.SEGMENTO_Y04_RETORNO_FIELDS
        self.confere(y04, 18, 19, "identificação registro")
        self.confere(y04, 20, 53, "cheque 1")
        self.confere(y04, 190, 223, "cheque 6")
        for lista, codigo in ((y03, "03"), (y53, "53"), (r03, "03"), (y04, "04")):
            self.assertIn(f"conteúdo no manual: {codigo}", campo_em(lista, 18)[3])

    def test_registros_e_segmentos_mapeados(self):
        self.assertEqual(sorted(s.SEGMENTOS), [("Remessa", "P"), ("Remessa", "Q"), ("Remessa", "R"), ("Remessa", "S-1"),
                                               ("Remessa", "S-2"), ("Remessa", "Y-03"), ("Remessa", "Y-53"),
                                               ("Retorno", "T"), ("Retorno", "U"), ("Retorno", "Y-03"),
                                               ("Retorno", "Y-04")])
        self.assertEqual(sorted(s.REGISTROS), [(t, c) for t in ("Remessa", "Retorno") for c in "0159"])
        for lista in list(s.SEGMENTOS.values()) + list(s.REGISTROS.values()):
            self.assertEqual(lista[0][1], 1)

    def test_tipo_de_registro_na_posicao_8(self):
        for (tipo, codigo), lista in s.REGISTROS.items():
            with self.subTest(tipo=tipo, registro=codigo):
                self.assertIn("tipo de registro", campo_em(lista, 8)[0].lower())
        for chave, lista in s.SEGMENTOS.items():
            with self.subTest(segmento=chave):
                self.assertIn("tipo de registro", campo_em(lista, 8)[0].lower())
                self.assertIn("segmento", campo_em(lista, 14)[0].lower())


class Tabelas(unittest.TestCase):
    def test_movimento_remessa_nota_14(self):
        m = s.MOVIMENTO_REMESSA_CODES
        self.assertEqual(len(m), 20)
        self.assertEqual(m["01"], "Entrada de boleto")
        self.assertEqual(m["02"], "Pedido de baixa")
        self.assertEqual(m["07"], "Alteração da identificação do boleto na empresa (Controle Participante)")
        self.assertEqual(m["18"], "Pedido de Sustação de Protesto")
        self.assertEqual(m["31"], "Alteração de outros dados")

    def test_movimento_retorno_nota_40(self):
        m = s.MOVIMENTO_RETORNO_CODES
        self.assertEqual(len(m), 32)
        self.assertEqual(m["02"], "Entrada confirmada")
        self.assertEqual(m["06"], "Liquidação do Boleto Efetivada")
        self.assertEqual(m["09"], "Baixa")
        self.assertEqual(m["A4"], "Pagador DDA")

    def test_especie_rejeicao_liquidacao_e_baixa(self):
        self.assertEqual(s.ESPECIE_BOLETO_CODES["02"], "DM - DUPLICATA MERCANTIL")
        self.assertEqual(s.ESPECIE_BOLETO_CODES["32"], "BDP – BOLETO DE PROPOSTA")
        self.assertEqual(s.REJEICAO_CODES["09"], "nosso numero duplicado")
        self.assertEqual(s.REJEICAO_CODES["P6"], "Identificador (TXID) em duplicidade")
        self.assertEqual(s.LIQUIDACAO_CODES["61"], "Liquidação por pagamento PIX")
        self.assertEqual(s.BAIXA_CODES["92"], "Baixa por pagamento PIX")
        self.assertEqual(s.LIQUIDACAO_CODES["09"], "Pagamento Parcial")  # o 09 existe nas duas tabelas
        self.assertEqual(s.BAIXA_CODES["09"], "Comandada banco")

    def test_descricao_do_movimento_lista_os_codigos(self):
        descricao = campo_em(s.SEGMENTO_P_REMESSA_FIELDS, 16)[3]
        self.assertIn("01 Entrada de boleto", descricao)
        self.assertIn("98 Não Protestar", descricao)


if __name__ == "__main__":
    unittest.main()
