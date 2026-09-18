"""Filtros interativos e dependentes reutilizaveis (Unidade -> Rodovia -> Municipio)."""
from __future__ import annotations
import pandas as pd
import streamlit as st

from core.data import municipios_disponiveis, normalizar_rodovia, rodovias_da_unidade, unidades_disponiveis

TODAS = "Todas"


def filtro_unidade(dados, chave: str, incluir_todas: bool = True, label: str = "Unidade"):
    ops = ([TODAS] if incluir_todas else []) + unidades_disponiveis(dados)
    return st.selectbox(label, ops, key=f"{chave}_uni")


def filtro_rodovia(dados, unidade, chave: str, incluir_todas: bool = True, label: str = "Rodovia"):
    ops = ([TODAS] if incluir_todas else []) + rodovias_da_unidade(dados, unidade)
    if not ops:
        st.info("Nenhuma rodovia cadastrada para esta unidade.")
        return TODAS
    return st.selectbox(label, ops, key=f"{chave}_rod")


def filtro_municipio(dados, unidade, rodovia, chave: str, label: str = "Município"):
    ops = [TODAS] + municipios_disponiveis(dados, unidade, rodovia)
    return st.selectbox(label, ops, key=f"{chave}_mun")


def filtro_faixa_km(df: pd.DataFrame, chave: str, colunas=("km_inicial", "km_final")):
    """Slider de faixa de km calculado a partir do proprio recorte de dados."""
    vals = pd.concat([pd.to_numeric(df[c], errors="coerce") for c in colunas if c in df.columns]).dropna()
    if vals.empty:
        return None
    lo, hi = float(vals.min()), float(vals.max())
    if hi - lo < 0.01:
        return (lo, hi)
    return st.slider("Faixa de km", min_value=round(lo, 1), max_value=round(hi, 1),
                     value=(round(lo, 1), round(hi, 1)), step=0.5, key=f"{chave}_km")


def aplicar(df: pd.DataFrame, unidade=None, rodovia=None, municipio=None,
            categoria=None, faixa_km=None, coluna_km="km") -> pd.DataFrame:
    """Aplica os filtros selecionados a qualquer dataset padronizado."""
    out = df.copy()
    if unidade and unidade != TODAS and "unidade" in out.columns:
        out = out[out["unidade"] == unidade]
    if rodovia and rodovia != TODAS and "rodovia" in out.columns:
        out = out[out["rodovia"] == normalizar_rodovia(rodovia)]
    if municipio and municipio != TODAS and "municipio" in out.columns:
        out = out[out["municipio"].str.casefold() == str(municipio).casefold()]
    if categoria and categoria != TODAS and "categoria" in out.columns:
        out = out[out["categoria"] == categoria]
    if faixa_km:
        lo, hi = faixa_km
        if coluna_km in out.columns:
            k = pd.to_numeric(out[coluna_km], errors="coerce")
            out = out[(k.isna()) | ((k >= lo) & (k <= hi))]
        elif {"km_inicial", "km_final"} <= set(out.columns):
            a = pd.to_numeric(out["km_inicial"], errors="coerce")
            b = pd.to_numeric(out["km_final"], errors="coerce").fillna(a)
            out = out[(b >= lo) & (a <= hi)]
    return out.reset_index(drop=True)


def busca_texto(df: pd.DataFrame, termo: str, colunas) -> pd.DataFrame:
    if not termo:
        return df
    termo = termo.strip().casefold()
    mask = pd.Series(False, index=df.index)
    for c in colunas:
        if c in df.columns:
            mask = mask | df[c].astype(str).str.casefold().str.contains(termo, na=False, regex=False)
    return df[mask].reset_index(drop=True)
