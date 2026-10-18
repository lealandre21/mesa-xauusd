# -*- coding: utf-8 -*-
"""Bipes da Mesa: WAV gerado à mão (sem dependência) pra avisar estado.

- "atencao"  → blip suave grave (setup quase lá, R:R ainda ruim)
- "gatilho"  → 3 notas subindo (cartão pronto: pode armar com R:R ok)
- "fechou"   → nota dupla descendo (posição fechada)  [reservado]

Puro wave/struct/math — sem pip novo. Toca UMA vez só na transição
de estado (nunca em loop: bip infinito deixaria ninguém são).
"""
import io
import math
import struct
import wave

SR = 24000  # samples por segundo


def _nota(freq: float, dur: float, vol: float, gap: float = 0.10) -> list[int]:
    n = int(SR * dur)
    pausa = int(SR * gap)
    frames = []
    for i in range(n):
        t = i / SR
        # envelope: entra rápido, sai suave (evita "estalo")
        env = min(1.0, i / (SR * 0.012), (n - i) / (SR * 0.045))
        env = max(0.0, env)
        frames.append(int(32767 * vol * env * math.sin(2 * math.pi * freq * t)))
    frames.extend([0] * pausa)
    return frames


# (frequência, duração, volume) por estado
_TONS = {
    "atencao": [(660, 0.30, 0.30)],
    "gatilho": [(880, 0.16, 0.35), (1175, 0.16, 0.35), (1568, 0.30, 0.40)],
    "fechou": [(1175, 0.16, 0.30), (880, 0.30, 0.30)],
}


def beep(tipo: str = "gatilho") -> bytes | None:
    """Gera WAV mono em memória. Retorna bytes ou None se tipo estranho."""
    notas = _TONS.get(tipo)
    if not notas:
        return None
    frames: list[int] = []
    for freq, dur, vol in notas:
        frames.extend(_nota(freq, dur, vol))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", f) for f in frames))
    return buf.getvalue()
