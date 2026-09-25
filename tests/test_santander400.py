# -*- coding: utf-8 -*-
"""Layout CNAB 400 do Santander (cnab400_layout_santander): posições e tabelas conferidas com o manual
H7800 v2.37 (fev/2026). Cada asserção cita a posição do manual."""
import unittest

import _caminho  # noqa: F401
import cnab400_layout_santander as s


def campo_em(lista, inicio):
    for campo in lista:
        if campo[1] == inicio:
            return campo
    raise AssertionError(f"nenhum campo começa em {inicio}")


class Posicoes(unittest.TestCase):
    def confere(self, lista, inicio, fim, trecho):
        nome, ini, f, _ = campo_em(lista, inicio)
        self.assertEqual((ini, f), (inicio, fim), nome)
        self.assertIn(trecho.lower(), nome.lower())

    def test_header_remessa(self):
        h = s.HEADER_REMESSA_FIELDS
        self.confere(h, 3, 9, "literal de transmissão")
        self.confere(h, 27, 46, "código de transmissão")
        self.confere(h, 77, 79, "código do banco")
        self.confere(h, 95, 100, "data da geração")
        self.confere(h, 117, 163, "mensagem 1")
        self.confere(h, 305, 351, "mensagem 5")
        self.confere(h, 392, 394, "sequencial do arquivo")
        self.confere(h, 395, 400, "sequencial do registro")

    def test_movimento_remessa(self):
        m = s.DETAIL_REMESSA_FIELDS
        self.confere(m, 4, 17, "inscrição do beneficiário")
        self.confere(m, 63, 70, "nosso número")
        self.confere(m, 108, 108, "tipo de cobrança")
        self.confere(m, 109, 110, "código de movimento")
        self.confere(m, 111, 120, "número do documento")
        self.confere(m, 121, 126, "data de vencimento")
        self.confere(m, 127, 139, "valor nominal")
        self.confere(m, 148, 149, "espécie")
        self.confere(m, 235, 274, "nome do pagador")
        self.confere(m, 275, 314, "endereço do pagador")
        self.confere(m, 392, 393, "protesto")

    def test_movimento_retorno(self):
        m = s.DETAIL_RETORNO_FIELDS
        self.confere(m, 109, 110, "código de movimento")
        self.confere(m, 111, 116, "data da ocorrência")
        self.confere(m, 117, 126, "número do documento")
        self.confere(m, 137, 139, "1ª ocorrência")
        self.confere(m, 143, 145, "3ª ocorrência")
        self.confere(m, 254, 266, "valor pago")
        self.confere(m, 296, 301, "efetivação")
        self.confere(m, 302, 337, "nome do pagador")

    def test_qr_code_pix(self):
        self.confere(s.QRCODE_REMESSA_FIELDS, 121, 155, "txid")
        self.confere(s.QRCODE_REMESSA_FIELDS, 44, 120, "chave dict")
        self.confere(s.QRCODE_RETORNO_FIELDS, 3, 79, "chave dict")
        self.confere(s.QRCODE_RETORNO_FIELDS, 80, 114, "txid")

    def test_mensagens_e_trailers(self):
        self.confere(s.MENSAGEM_REMESSA_FIELDS, 50, 99, "mensagem variável")
        self.confere(s.MENSAGEM_REMESSA_FIELDS, 152, 153, "sub")
        self.confere(s.TRAILER_REMESSA_FIELDS, 8, 20, "valor total")
        self.confere(s.TRAILER_RETORNO_FIELDS, 18, 25, "cobrança simples")

    def test_codigo_do_registro_de_cada_layout(self):
        for lista, codigo in ((s.HEADER_REMESSA_FIELDS, "0"), (s.DETAIL_REMESSA_FIELDS, "1"),
                              (s.QRCODE_REMESSA_FIELDS, "8"), (s.TRAILER_REMESSA_FIELDS, "9"),
                              (s.HEADER_RETORNO_FIELDS, "0"), (s.DETAIL_RETORNO_FIELDS, "1"),
                              (s.QRCODE_RETORNO_FIELDS, "2"), (s.TRAILER_RETORNO_FIELDS, "9")):
            with self.subTest(codigo=codigo, primeiro=lista[0][0]):
                self.assertEqual(lista[0][1:3], (1, 1))
                self.assertIn("registro", lista[0][0].lower())


class Tabelas(unittest.TestCase):
    def test_movimento_remessa_nota_21(self):
        c = s.COMANDO_REMESSA_CODES
        self.assertEqual(len(c), 15)
        self.assertEqual(c["01"], "Entrada do boleto")
        self.assertEqual(c["02"], "Baixa do boleto")
        self.assertEqual(c["09"], "Protestar")
        self.assertEqual(c["49"], "Alteração do valor máximo/percentual")

    def test_movimento_retorno_nota_29(self):
        o = s.OCORRENCIA_CODES
        self.assertEqual(len(o), 33)
        self.assertEqual(o["02"], "Entrada boleto Confirmada")
        self.assertEqual(o["06"], "Liquidação do Boleto Efetivada")
        self.assertEqual(o["09"], "Baixa Automática")
        self.assertEqual(o["38"], "Não Protestar (antes de iniciar o ciclo de protesto)")
        self.assertEqual(o["94"], "Cancelamento do Pagamento Recebido")

    def test_especie_e_instrucao(self):
        self.assertEqual(s.ESPECIE_BOLETO_CODES["01"], "DM Duplicata Mercantil")
        self.assertEqual(s.ESPECIE_BOLETO_CODES["19"], "BCC Boleto de Cartão de Crédito")
        self.assertEqual(s.INSTRUCAO_CODES["06"], "Protestar (Vide posição 392/393)")
        self.assertEqual(s.INSTRUCAO_CODES["00"], "Não há instruções")

    def test_erros_do_retorno_tem_tres_digitos(self):
        e = s.ERRO_OCORRENCIA_CODES
        self.assertTrue(all(len(k) == 3 for k in e))
        self.assertEqual(e["001"], "Nosso Número não numérico")

    def test_sem_asterisco_de_rodape_nas_descricoes(self):
        for tabela in (s.COMANDO_REMESSA_CODES, s.OCORRENCIA_CODES):
            self.assertFalse(any(d.endswith("*") for d in tabela.values()))


if __name__ == "__main__":
    unittest.main()
