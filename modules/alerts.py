# -*- coding: utf-8 -*-
"""Alertas de AÇÃO da mesa: varrida de liquidez em tempo real.

Varredura real = pavio ATRAVESSA o nível de liquidez e o corpo VOLTA
(behavioral: stop hunt pega os ansiosos e o preço regressa).
Dedupe por candle: mesma varredura não reaparece a cada tick de 60s.
"""
from modules import data, smc

_POR_TIPO = {
    "BSL": ("⬆️ BSL varrida", "pavio entrou acima da liquidez de compradores e o corpo voltou — armadilha de alta provável."),
    "SSL": ("⬇️ SSL varrida", "pavio afundou abaixo da liquidez de vendedores e o corpo voltou — armadilha de baixa provável."),
}


def houve_varredura(sigla: str, nivel: float, candle: dict) -> bool:
    """Pura: pavio atravessa o nível e o CORPO volta pro outro lado."""
    if sigla == "BSL":
        return candle["h"] > nivel > candle["c"]
    if sigla == "SSL":
        return candle["l"] < nivel < candle["c"]
    return False


def varredura() -> tuple[str, str, str, int] | None:
    """Primeira varredura fresca em 15m/1h — (chave, título, texto, candle_t)."""
    bsl, ssl, _, _ = smc.liquidity_map()
    niveis = []
    if bsl:
        niveis.append(("BSL", bsl))
    if ssl:
        niveis.append(("SSL", ssl))
    if not niveis or not niveis[0][1]:
        return None

    for tf, limite in (("15m", 6), ("1h", 4)):
        cand = data.candles(tf, limite)
        if not cand:
            continue
        for c in reversed(cand[-4:]):  # os 4 candles mais recentes
            for sigla, nivel in niveis:
                if houve_varredura(sigla, nivel, c):
                    tipo, texto = _POR_TIPO[sigla]
                    chave = f"{tf}:{sigla}:{c['t']}"
                    return (chave, f"{tipo} ({tf})", texto, c["t"])

    return None
