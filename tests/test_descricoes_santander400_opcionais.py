"""Descrições dos registros opcionais do CNAB 400 Santander (8 e 2 do QR Code/Pix; 2 e 4 a 7 das mensagens):
cada campo explica o que é, a partir do manual H7800, em vez de só remeter a uma nota (épico #85)."""
import unittest

import _caminho  # noqa: F401  (põe src/ no caminho)

from cnablens.layouts import santander400 as s

REGISTROS = ("QRCODE_REMESSA_FIELDS", "MENSAGEM_REMESSA_FIELDS", "QRCODE_RETORNO_FIELDS")


def descricao(registro, inicio):
    return next(d for _n, i, _f, d in getattr(s, registro) if i == inicio)


class DescricoesOpcionaisSantander400(unittest.TestCase):
    def test_nenhum_campo_so_remete_ao_manual(self):
        for registro in REGISTROS:
            for nome, inicio, _fim, texto in getattr(s, registro):
                with self.subTest(registro=registro, campo=nome, inicio=inicio):
                    self.assertNotIn("ver nota", texto)
                    self.assertNotIn("conteúdo no manual", texto)
                    if "Uso Reservado" not in nome:
                        self.assertGreaterEqual(len(texto), 25)

    def test_tipo_do_registro_e_conteudo_e_nao_nota(self):
        # a extração tinha lido o conteúdo fixo ("8" e "2") como número de nota
        self.assertIn("'8' identifica", descricao("QRCODE_REMESSA_FIELDS", 1))
        self.assertIn("'2' no retorno", descricao("QRCODE_RETORNO_FIELDS", 1))
        self.assertIn("'01'", descricao("MENSAGEM_REMESSA_FIELDS", 48))

    def test_codigos_do_pix_embutidos(self):
        tipo_pagamento = descricao("QRCODE_REMESSA_FIELDS", 2)
        for codigo in ("'00'", "'01'", "'02'", "'03'"):
            self.assertIn(codigo, tipo_pagamento)
        for registro, inicio in (("QRCODE_REMESSA_FIELDS", 43), ("QRCODE_RETORNO_FIELDS", 2)):
            for codigo in ("'1' CPF", "'2' CNPJ", "'3' celular", "'4' e-mail", "'5' EVP"):
                with self.subTest(registro=registro, codigo=codigo):
                    self.assertIn(codigo, descricao(registro, inicio))

    def test_reserva_segue_a_convencao(self):
        # campos de brancos levam "Uso Reservado (Filler)", para a tela mostrá-los acinzentados
        nomes = [nome for nome, *_ in s.QRCODE_RETORNO_FIELDS]
        self.assertNotIn("Brancos", nomes)
        self.assertIn("Uso Reservado (Filler)", nomes)


if __name__ == "__main__":
    unittest.main()
