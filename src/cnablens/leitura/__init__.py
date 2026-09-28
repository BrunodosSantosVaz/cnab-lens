"""Leitura dos arquivos CNAB (400 e 240): `CnabFile` lê o arquivo uma vez e aplica o layout escolhido.
Não depende da interface: pode ser usada em scripts e testes sem Tkinter.

As regras de cada formato ficam no leitor dele (padrão Strategy): leitor400.Leitor400 e
leitor240.Leitor240. O CnabFile só lê o arquivo, escolhe o leitor pelo tamanho da linha e delega."""
from collections import Counter

from cnablens import layouts
from cnablens.leitura.leitor240 import Leitor240
from cnablens.leitura.leitor400 import Leitor400
from cnablens.leitura.registro import CnabGroup, CnabRecord

LEITORES = {leitor.largura: leitor for leitor in (Leitor400, Leitor240)}
CODIFICACOES = ("latin-1", "cp1252", "utf-8")


class CnabFile:
    """Lê as linhas do arquivo uma única vez. Os nomes e posições de campo são aplicados à parte, em
    apply_layout(), para o mesmo arquivo poder ser reexibido sob outro layout sem reler o disco."""

    def __init__(self, path):
        self.path = path
        self.records = []
        self.width = 400  # 400 ou 240 posições por linha (detectado no arquivo)
        self.tipo_arquivo = "?"  # Remessa / Retorno
        self.banco_codigo = ""
        self.banco_nome = ""
        self.empresa_nome = ""
        self.data_geracao = ""
        self.header = None
        self.trailer = None
        self.detalhes = []
        self.layout_key = None
        self.layout = None
        self._leitor = None
        self._load()
        self.apply_layout(layouts.auto_layout_key(self.banco_codigo, self.width))

    def _load(self):
        linhas, self.encoding_used = self._read_lines()
        linhas = [ln for ln in linhas if ln.strip("\x1a\x00 ") != ""]
        if not linhas:
            raise ValueError("Arquivo vazio ou sem linhas reconhecíveis.")
        self.width = self._detect_width(linhas)
        self._leitor = LEITORES[self.width]()
        self.records = [self._leitor.registro(i, linha) for i, linha in enumerate(linhas, start=1)]
        self._leitor.identificar(self)

    def _read_lines(self):
        for codificacao in CODIFICACOES:
            try:
                with open(self.path, encoding=codificacao, newline="") as arquivo:
                    return arquivo.read().splitlines(), codificacao
            except (UnicodeDecodeError, LookupError):
                continue
        with open(self.path, "rb") as arquivo:
            return arquivo.read().decode("latin-1", errors="replace").splitlines(), "latin-1 (fallback)"

    @staticmethod
    def _detect_width(lines):
        """400 ou 240 posições, pelo tamanho de linha mais comum. Tolera espaços finais cortados: até 300
        conta como 240."""
        mais_comum = Counter(len(ln) for ln in lines).most_common(1)[0][0]
        return 240 if mais_comum <= 300 else 400

    def apply_layout(self, layout_key):
        """Reaplica nomes e posições de campo segundo o layout (sem reler o arquivo). Um layout de outro
        tamanho de linha é trocado pelo padrão do tamanho do arquivo."""
        layout = layouts.LAYOUTS.get(layout_key)
        if layout is None or layout.width != self.width:
            layout = layouts.LAYOUTS[layouts.default_key_for_width(self.width)]
        self.layout_key = layout.key
        self.layout = layout
        self._leitor.aplicar_layout(self, layout)


__all__ = ["CnabFile", "CnabGroup", "CnabRecord"]
