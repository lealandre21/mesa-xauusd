# -*- coding: utf-8 -*-
"""Testes da NOTA DA MESA (modules/nota.py).

Cobertura: acerto alta/baixa, erro, filtro de ruído, ignora lateral,
dedupe por hora, futuro não fechado, data inválida. Tudo sem rede:
os candles são sintéticos (mock) — a lógica pura é a que está em jogo.
Rodar:  python -m unittest -v test_nota
"""
import unittest
from datetime import datetime, timedelta, timezone

from modules import alerts, nota

_BRT = timezone(timedelta(hours=-3))
_HORA = 3_600_000


def _ts(quando: str) -> int:
    dt = datetime.strptime(quando, "%Y-%m-%d %H:%M").replace(tzinfo=_BRT)
    return int(dt.timestamp() * 1000)


def _candle(t_ms: int, abertura: float, fechamento: float) -> dict:
    return {
        "t": t_ms,
        "o": abertura,
        "h": max(abertura, fechamento) + 1.0,
        "l": min(abertura, fechamento) - 1.0,
        "c": fechamento,
    }


def _linha(quando: str, direcao: str) -> dict:
    return {"quando_brt": quando, "fluxo_1h": direcao}


class NotaAvaliarTest(unittest.TestCase):
    """modules.nota.avaliar — lógica pura, fixtures sintéticas."""

    def setUp(self):
        self.quando = "2026-10-18 15:00"

    def _cenario(self, fechamento1: float, fechamento2: float) -> list[dict]:
        """3 candles: o momento da leitura + 2 pra frente (janela)."""
        t0 = _ts(self.quando)
        return [
            _candle(t0, 100.0, 100.0),
            _candle(t0 + _HORA, 100.0, 100.5),
            _candle(t0 + 2 * _HORA, 100.0, fechamento2),
        ]

    def test_alta_com_subida_e_acerto(self):
        cand = self._cenario(100.0, 102.0)  # abre hora 100, fecha +2h em 102
        acertos, erros, ruidos, exemplos = nota.avaliar(
            [_linha(self.quando, "alta")], cand
        )
        self.assertEqual((acertos, erros, ruidos), (1, 0, 0))
        self.assertEqual(exemplos[0][3], "✅")
        self.assertEqual(exemplos[0][2], 2.0)

    def test_baixa_com_queda_e_acerto(self):
        cand = self._cenario(100.0, 98.0)  # delta -2
        acertos, erros, ruidos, exemplos = nota.avaliar(
            [_linha(self.quando, "baixa")], cand
        )
        self.assertEqual((acertos, erros, ruidos), (1, 0, 0))
        self.assertEqual(exemplos[0][3], "✅")

    def test_chamada_errada_conta_erro(self):
        cand = self._cenario(100.0, 102.0)  # mercado subiu...
        acertos, erros, _, _ = nota.avaliar([_linha(self.quando, "baixa")], cand)
        self.assertEqual((acertos, erros), (0, 1))  # ...mas a mesa chamou baixa

    def test_ruido_pequeno_nao_conta_como_nem_acerto_nem_erro(self):
        cand = self._cenario(100.0, 100.3)  # delta +0.30 < US$ 0,50
        acertos, erros, ruidos, exemplos = nota.avaliar(
            [_linha(self.quando, "alta")], cand
        )
        self.assertEqual((acertos, erros, ruidos, len(exemplos)), (0, 0, 1, 0))

    def test_lateral_e_direcao_lixo_sao_ignorados(self):
        cand = self._cenario(100.0, 105.0)
        linhas = [
            _linha(self.quando, "lateral"),
            _linha(self.quando, ""),
            _linha(self.quando, "QUALQUER-COISA"),
        ]
        acertos, erros, ruidos, exemplos = nota.avaliar(linhas, cand)
        self.assertEqual((acertos, erros, ruidos, len(exemplos)), (0, 0, 0, 0))

    def test_dedupe_duas_linhas_mesma_hora_contam_uma(self):
        cand = self._cenario(100.0, 103.0)
        linhas = [
            _linha(self.quando, "alta"),          # 15:00
            _linha("2026-10-18 15:25", "alta"),   # 15:25 — mesmo candle 1h
        ]
        acertos, erros, ruidos, exemplos = nota.avaliar(linhas, cand)
        self.assertEqual((acertos, erros), (1, 0))  # só UMA avaliação
        self.assertEqual(len(exemplos), 1)

    def test_futuro_nao_fechado_avalia_nada(self):
        t0 = _ts(self.quando)
        cand = [
            _candle(t0, 100.0, 100.0),
            _candle(t0 + _HORA, 100.0, 100.0),
        ]  # só 1 candle pra frente — janela incompleta
        acertos, erros, ruidos, exemplos = nota.avaliar(
            [_linha(self.quando, "alta")], cand
        )
        self.assertEqual((acertos, erros, ruidos, len(exemplos)), (0, 0, 0, 0))

    def test_data_invalida_nao_quebra_nada(self):
        cand = self._cenario(100.0, 102.0)
        linhas = [_linha("bananada", "alta"), _linha(self.quando, "alta")]
        acertos, _, _, exemplos = nota.avaliar(linhas, cand)
        self.assertEqual(acertos, 1)  # a válida avaliou; a lixeira foi ignorada
        self.assertEqual(len(exemplos), 1)

    def test_horas_diferentes_sao_duas_avaliacoes(self):
        t0 = _ts("2026-10-18 15:00")
        cand = [
            _candle(t0, 100.0, 100.0),            # 15h (janela fecha 17h → 102)
            _candle(t0 + _HORA, 100.0, 101.0),
            _candle(t0 + 2 * _HORA, 100.0, 102.0),  # 17h (janela fecha 19h → 104)
            _candle(t0 + 3 * _HORA, 102.0, 103.0),
            _candle(t0 + 4 * _HORA, 103.0, 104.0),
        ]
        linhas = [
            _linha("2026-10-18 15:00", "alta"),   # +2.00 → ✅
            _linha("2026-10-18 17:00", "baixa"),  # +4.00 → ❌ (chamou baixa, subiu)
        ]
        acertos, erros, ruidos, exemplos = nota.avaliar(linhas, cand)
        self.assertEqual((acertos, erros), (1, 1))
        self.assertEqual(len(exemplos), 2)
        marcas = {e[3] for e in exemplos}
        self.assertEqual(marcas, {"✅", "❌"})


class NotaResumoTest(unittest.TestCase):
    """modules.nota.resumo — mensagens honestas com dados vazios."""

    def test_mensagem_com_diario_epoca(self):
        # lint: I/O de rede é inerente ao resumo; aqui só garantimos a forma
        texto, exemplos = nota.resumo()
        self.assertIsInstance(texto, str)
        self.assertTrue(len(texto) > 10)
        self.assertIsInstance(exemplos, list)


class AlertsVarreduraTest(unittest.TestCase):
    """modules.alerts.houve_varredura — a física da varrida (sem rede)."""

    def test_bsl_pavio_em_cima_corpo_volta_e_varredura(self):
        candle = {"o": 100.0, "h": 101.2, "l": 99.5, "c": 99.8}  # pavio 101 > 100, corpo < 100
        self.assertTrue(alerts.houve_varredura("BSL", 100.0, candle))

    def test_pavio_sem_voltar_nao_e_varredura(self):
        candle = {"o": 100.5, "h": 101.2, "l": 100.1, "c": 101.0}  # corpo fechou EM CIMA
        self.assertFalse(alerts.houve_varredura("BSL", 100.0, candle))

    def test_ssl_pavio_abaixo_corpo_volta_e_varredura(self):
        candle = {"o": 100.0, "h": 100.6, "l": 98.7, "c": 100.2}  # pavio < 99, corpo volta
        self.assertTrue(alerts.houve_varredura("SSL", 99.0, candle))

    def test_sigla_desconhecida_nao_explode(self):
        self.assertFalse(alerts.houve_varredura("XYZ", 100.0, {"h": 2, "l": 1, "c": 3}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
