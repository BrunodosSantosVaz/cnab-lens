"""Rolagem pela roda do mouse, ligada explicitamente em vez de depender do binding implícito do Tk (que
falha em alguns Tk/Windows com o widget dentro de PanedWindow/Frame)."""

# Windows manda <MouseWheel> com delta em múltiplos de 120 por "clique" da roda; o macOS manda deltas
# pequenos (1, 2, 3...). No Linux (X11) a roda chega como os botões 4 (cima) e 5 (baixo).
DELTA_POR_CLIQUE = 120
LINHAS_POR_CLIQUE = 3  # o padrão do Windows


def passos_da_roda(delta):
    """Linhas a rolar para um <MouseWheel>: negativo sobe, positivo desce (ao contrário do delta)."""
    if delta == 0:
        return 0
    cliques = -int(delta / DELTA_POR_CLIQUE) or (-1 if delta > 0 else 1)  # delta pequeno (macOS): 1 clique
    return cliques * LINHAS_POR_CLIQUE


def ligar_roda_do_mouse(widget):
    """Faz a roda do mouse rolar `widget` (Treeview, Text...) na vertical, no Windows, macOS e Linux.
    Devolve "break" para o binding padrão do Tk não rolar de novo (rolagem dobrada)."""

    def rolar(passos):
        if passos:
            widget.yview_scroll(passos, "units")
        return "break"

    widget.bind("<MouseWheel>", lambda e: rolar(passos_da_roda(e.delta)))
    widget.bind("<Button-4>", lambda e: rolar(-LINHAS_POR_CLIQUE))
    widget.bind("<Button-5>", lambda e: rolar(LINHAS_POR_CLIQUE))
