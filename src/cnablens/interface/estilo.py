"""Estilo das tabelas: linhas zebradas (branca e cinza-claro alternadas) e texto esmaecido para os campos
de reserva ("Uso Reservado/Filler")."""


# Zebra striping: linhas alternadas branca/cinza-claro para facilitar a
# leitura de tabelas longas.
ROW_COLOR_EVEN = "#ffffff"
ROW_COLOR_ODD = "#f1f3f6"
ROW_COLOR_FILLER = "#c7cbd1"  # texto acinzentado para campos "Uso Reservado/Filler"


def configure_zebra_tags(tree):
    tree.tag_configure("even", background=ROW_COLOR_EVEN)
    tree.tag_configure("odd", background=ROW_COLOR_ODD)
    tree.tag_configure("even-filler", background=ROW_COLOR_EVEN, foreground=ROW_COLOR_FILLER)
    tree.tag_configure("odd-filler", background=ROW_COLOR_ODD, foreground=ROW_COLOR_FILLER)


def zebra_tags(index, is_filler=False):
    base = "even" if index % 2 == 0 else "odd"
    return (f"{base}-filler",) if is_filler else (base,)
