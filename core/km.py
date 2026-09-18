"""Tratamento padronizado de quilometragem rodoviaria.

Formato rodoviario: `45+500` (km 45 e 500 metros) -> valor numerico 45.500
Aceita tambem `045+500`, `45,500`, `45.5`, `km 45+500`.
"""
from __future__ import annotations
import math
import re

_RE_KM_METRO = re.compile(r"^0*(\d+)\s*\+\s*(\d{1,3})$")
_LIMPA = re.compile(r"(?i)\b(km|kms)\b|\s")


def km_para_float(valor) -> float | None:
    """Converte qualquer representacao de km em float comparavel. Retorna None se invalido."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return None if isinstance(valor, float) and math.isnan(valor) else round(float(valor), 3)

    texto = _LIMPA.sub("", str(valor)).replace("–", "-").strip()
    if texto in ("", "-", "nan", "None"):
        return None

    m = _RE_KM_METRO.match(texto)
    if m:
        return round(int(m.group(1)) + int(m.group(2)) / 1000, 3)
    try:
        return round(float(texto.replace(",", ".")), 3)
    except ValueError:
        return None


def float_para_km(valor, casas_metro: int = 3, pad: int = 0) -> str:
    """Converte float em formato rodoviario de apresentacao (45.5 -> '45+500')."""
    v = km_para_float(valor)
    if v is None:
        return "—"
    inteiro = int(v)
    metros = int(round((v - inteiro) * 1000))
    if metros == 1000:
        inteiro, metros = inteiro + 1, 0
    return f"{str(inteiro).zfill(pad)}+{metros:0{casas_metro}d}"


def km_no_intervalo(km, km_inicial, km_final, tolerancia: float = 0.0) -> bool:
    """Verifica se `km` esta dentro do intervalo [km_inicial, km_final] (ordem irrelevante)."""
    k, a, b = km_para_float(km), km_para_float(km_inicial), km_para_float(km_final)
    if k is None or a is None:
        return False
    if b is None:
        return abs(k - a) <= max(tolerancia, 0.001)
    lo, hi = min(a, b), max(a, b)
    return (lo - tolerancia) <= k <= (hi + tolerancia)


def extensao(km_inicial, km_final) -> float | None:
    a, b = km_para_float(km_inicial), km_para_float(km_final)
    if a is None or b is None:
        return None
    return round(abs(b - a), 3)


def distancia_km(km_a, km_b) -> float | None:
    a, b = km_para_float(km_a), km_para_float(km_b)
    if a is None or b is None:
        return None
    return round(abs(a - b), 3)
