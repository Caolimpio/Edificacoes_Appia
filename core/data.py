"""Camada de dados: leitura, normalizacao e cache dos datasets CSV.

Trocar CSV por banco SQL no futuro exige alterar apenas `_ler_fonte`.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

from core.config import DATA_DIR
from core.km import extensao, km_para_float

TABELAS = {
    "unidades": ["unidade", "lote", "concessionaria", "uf", "status_dados", "observacao"],
    "rodovias": ["unidade", "rodovia", "nome_rodovia", "tipo", "trecho", "sentido",
                 "km_inicial", "km_final", "extensao", "codigo", "observacao"],
    "municipios": ["unidade", "rodovia", "municipio", "tipo", "km_inicial", "km_final", "extensao", "descricao"],
    "estruturas": ["unidade", "categoria", "tipo", "nome", "rodovia", "km", "sentido",
                   "municipio", "latitude", "longitude", "qtd_viaturas", "viaturas", "observacao"],
    "pedagios": ["unidade", "nome", "rodovia", "km", "sentido", "municipio",
                 "latitude", "longitude", "observacao"],
}


def normalizar_rodovia(valor) -> str:
    """Padroniza sigla de rodovia: 'sp 075' / 'SP-075' -> 'SP075'."""
    s = str(valor or "").upper().strip()
    return s.replace(" ", "").replace("-", "").replace("_", "")


def _ler_fonte(nome: str) -> pd.DataFrame:
    caminho = DATA_DIR / f"{nome}.csv"
    if not caminho.exists():
        return pd.DataFrame(columns=TABELAS[nome])
    return pd.read_csv(caminho, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def _tratar(nome: str, df: pd.DataFrame) -> pd.DataFrame:
    for col in TABELAS[nome]:
        if col not in df.columns:
            df[col] = ""
    df = df[TABELAS[nome]].copy()
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip().replace({"nan": "", "None": ""})

    if "rodovia" in df.columns:
        df["rodovia"] = df["rodovia"].map(normalizar_rodovia)
    for col in ("km", "km_inicial", "km_final", "latitude", "longitude", "qtd_viaturas"):
        if col in df.columns:
            df[col] = df[col].map(km_para_float) if col.startswith("km") else pd.to_numeric(df[col], errors="coerce")
    if {"km_inicial", "km_final"} <= set(df.columns):
        calc = [extensao(a, b) for a, b in zip(df["km_inicial"], df["km_final"])]
        atual = pd.to_numeric(df.get("extensao"), errors="coerce") if "extensao" in df.columns else None
        df["extensao"] = [c if c is not None else (a if atual is not None else None)
                          for c, a in zip(calc, atual if atual is not None else calc)]
    return df.reset_index(drop=True)


@st.cache_data(show_spinner="Carregando bases da Via Appia...")
def carregar_dados() -> dict[str, pd.DataFrame]:
    """Retorna todos os datasets tratados. Cacheado; use `limpar_cache()` apos atualizar CSVs."""
    dados = {nome: _tratar(nome, _ler_fonte(nome)) for nome in TABELAS}

    # Pedagios: consolidados a partir das estruturas quando o CSV proprio estiver vazio
    est = dados["estruturas"]
    if dados["pedagios"].empty and not est.empty:
        ped = est[est["categoria"].str.lower() == "pedágio"].copy()
        dados["pedagios"] = _tratar("pedagios", ped.rename(columns={"nome": "nome"}))
    return dados


def limpar_cache() -> None:
    carregar_dados.clear()


def indicadores(dados: dict[str, pd.DataFrame]) -> dict[str, int | float]:
    est, rod, mun = dados["estruturas"], dados["rodovias"], dados["municipios"]
    bases = est[est["categoria"] == "Base"]
    ped = est[est["categoria"] == "Pedágio"]
    ext = pd.to_numeric(rod[rod["tipo"] == "Principal"]["extensao"], errors="coerce").sum()
    return {
        "unidades": dados["unidades"]["unidade"].nunique(),
        "rodovias": rod["rodovia"].nunique(),
        "trechos": len(rod),
        "municipios": mun["municipio"].nunique(),
        "bases": len(bases),
        "pedagios": len(ped),
        "estruturas": len(est),
        "extensao_principal": round(float(ext), 1),
    }


def rodovias_da_unidade(dados, unidade: str | None = None) -> list[str]:
    rod, mun = dados["rodovias"], dados["municipios"]
    itens = set(rod["rodovia"]) | set(mun["rodovia"]) | set(dados["estruturas"]["rodovia"])
    if unidade and unidade != "Todas":
        itens = (set(rod.loc[rod["unidade"] == unidade, "rodovia"])
                 | set(mun.loc[mun["unidade"] == unidade, "rodovia"])
                 | set(dados["estruturas"].loc[dados["estruturas"]["unidade"] == unidade, "rodovia"]))
    return sorted(x for x in itens if x)


def municipios_disponiveis(dados, unidade=None, rodovia=None) -> list[str]:
    df = dados["municipios"]
    if unidade and unidade != "Todas":
        df = df[df["unidade"] == unidade]
    if rodovia and rodovia != "Todas":
        df = df[df["rodovia"] == normalizar_rodovia(rodovia)]
    extra = dados["estruturas"]
    if unidade and unidade != "Todas":
        extra = extra[extra["unidade"] == unidade]
    if rodovia and rodovia != "Todas":
        extra = extra[extra["rodovia"] == normalizar_rodovia(rodovia)]
    return sorted({m for m in list(df["municipio"]) + list(extra["municipio"]) if m})


def unidades_disponiveis(dados) -> list[str]:
    return sorted(u for u in dados["unidades"]["unidade"] if u)
