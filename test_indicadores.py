# -*- coding: utf-8 -*-
"""Testes do motor de indicadores (matemática pura)."""
import unittest

from modules.indicadores import rsi, atr, pressao, txt_rsi, txt_atr, txt_pressao


def _candles_serie(valores):
    """Fabrica candles com closes crescentes/definidos a partir de uma lista."""
    out = []
    for i, v in enumerate(valores):
        out.append({"t": i, "o": v, "h": v + 1, "l": v - 1, "c": v, "v": 10.0, "vb": 5.0})
    return out


class RsiTest(unittest.TestCase):
    def test_sem_dados_retorna_none(self):
        self.assertIsNone(rsi([1.0, 2.0, 3.0], 14))

    def test_so_subidas_vai_para_cem(self):
        closes = [float(i) for i in range(1, 40)]
        self.assertGreater(rsi(closes, 14), 95.0)

    def test_so_quedas_vai_para_zero(self):
        closes = [40.0 - i for i in range(40)]
        self.assertLess(rsi(closes, 14), 5.0)

    def test_lateral_fica_neutro(self):
        closes = [100.0 + (i % 2) * 0.1 for i in range(40)]
        v = rsi(closes, 14)
        self.assertTrue(35.0 <= v <= 65.0)


class AtrTest(unittest.TestCase):
    def test_sem_dados_retorna_none(self):
        self.assertIsNone(atr(_candles_serie([100.0] * 5), 14))

    def test_candles_calmos_tem_atr_menor(self):
        # calm: range 1; wild: range 10
        calm = []
        for i in range(30):
            calm.append({"t": i, "o": 100, "h": 101, "l": 99, "c": 100.5, "v": 1, "vb": 1})
        wild = []
        for i in range(30):
            wild.append({"t": i, "o": 100, "h": 110, "l": 90, "c": 100.5, "v": 1, "vb": 1})
        self.assertLess(atr(calm), atr(wild))

    def test_atr_lado_do_range_basico(self):
        cs = _candles_serie([100.0] * 20)
        # range fixo h-l = 2 → ATR converge pra 2
        self.assertAlmostEqual(atr(cs), 2.0, places=6)


class PressaoTest(unittest.TestCase):
    def test_sem_dados_retorna_none(self):
        self.assertIsNone(pressao([]))

    def test_tudo_comprador(self):
        cs = [{"t": i, "v": 10.0, "vb": 10.0} for i in range(20)]
        pc, pv = pressao(cs)
        self.assertAlmostEqual(pc, 100.0)
        self.assertAlmostEqual(pv, 0.0)

    def test_meio_a_meio(self):
        cs = [{"t": i, "v": 10.0, "vb": 5.0} for i in range(20)]
        pc, pv = pressao(cs)
        self.assertAlmostEqual(pc, 50.0)
        self.assertAlmostEqual(pv, 50.0)

    def test_janela_n(self):
        # 30 candles: primeiros 10 vendedores, últimos 20 compradores.
        # Janela n=20 → deve enxergar somente os 20 compradores.
        cs = [{"t": i, "v": 1.0, "vb": 0.0} for i in range(10)]
        cs += [{"t": i, "v": 1.0, "vb": 1.0} for i in range(20)]
        pc, _ = pressao(cs, n=20)
        self.assertAlmostEqual(pc, 100.0)


class TextosTest(unittest.TestCase):
    def test_txt_rsi_portugues(self):
        self.assertIn("exaltado", txt_rsi(75.0))
        self.assertIn("neutro", txt_rsi(50.0))
        self.assertIn("esgotado", txt_rsi(20.0))

    def test_txt_atr_bandas(self):
        self.assertIn("quieta", txt_atr(1.0, 2000.0))     # 0.05%
        self.assertIn("QUENTE", txt_atr(10.0, 2000.0))    # 0.50%

    def test_txt_pressao_none(self):
        self.assertIn("sem dados", txt_pressao(None))


if __name__ == "__main__":
    unittest.main()
