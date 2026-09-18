"""Regras de negocio das consultas (por km, por municipio, por base)."""
from __future__ import annotations
import pandas as pd

from core.data import normalizar_rodovia
from core.km import distancia_km, km_no_intervalo, km_para_float


def _no_km(df: pd.DataFrame, ref, tolerancia: float = 0.0) -> pd.DataFrame:
    """Filtra as linhas cujo intervalo [km_inicial, km_final] contem `ref`.

    Usa mascara booleana com indice: uma lista vazia em `df[...]` seria interpretada
    pelo pandas como selecao de COLUNAS, descartando o schema do DataFrame.
    """
    if df.empty or not {"km_inicial", "km_final"} <= set(df.columns):
        return df.iloc[0:0].copy()
    mascara = pd.Series(
        [km_no_intervalo(ref, a, b, tolerancia) for a, b in zip(df["km_inicial"], df["km_final"])],
        index=df.index, dtype=bool)
    return df[mascara].copy()


def consultar_km(dados: dict[str, pd.DataFrame], rodovia: str, km, unidade: str | None = None,
                 raio_estruturas: float = 10.0) -> dict:
    """Retorna o contexto completo de um km de referencia em uma rodovia."""
    rod = normalizar_rodovia(rodovia)
    ref = km_para_float(km)
    resultado = {"rodovia": rod, "km": ref, "unidade": unidade, "municipios": pd.DataFrame(),
                 "trechos": pd.DataFrame(), "estruturas": pd.DataFrame(), "pedagios": pd.DataFrame(),
                 "base_mais_proxima": None, "pedagio_mais_proximo": None, "fora_de_trecho": True}
    if ref is None or not rod:
        return resultado

    def recorte(df):
        out = df[df["rodovia"] == rod]
        if unidade and unidade != "Todas":
            out = out[out["unidade"] == unidade]
        return out.copy()

    mun = _no_km(recorte(dados["municipios"]), ref)
    resultado["municipios"] = mun.sort_values("km_inicial").reset_index(drop=True) if not mun.empty else mun

    trechos = _no_km(recorte(dados["rodovias"]), ref)
    resultado["trechos"] = trechos.reset_index(drop=True)
    resultado["fora_de_trecho"] = trechos.empty and mun.empty

    est = recorte(dados["estruturas"])
    if not est.empty:
        est["distancia"] = [distancia_km(ref, k) for k in est["km"]]
        est = _ordenar(est.dropna(subset=["distancia"]), ["distancia"])
        resultado["estruturas"] = est[est["distancia"] <= raio_estruturas].reset_index(drop=True)
        bases = est[est["categoria"] == "Base"]
        if not bases.empty:
            resultado["base_mais_proxima"] = bases.iloc[0].to_dict()
        peds = est[est["categoria"] == "Pedágio"]
        resultado["pedagios"] = peds[peds["distancia"] <= raio_estruturas].reset_index(drop=True)
        if not peds.empty:
            resultado["pedagio_mais_proximo"] = peds.iloc[0].to_dict()
    if unidade in (None, "Todas") and not mun.empty:
        resultado["unidade"] = mun.iloc[0]["unidade"]
    return resultado


def resumo_unidade(dados: dict[str, pd.DataFrame], unidade: str) -> dict:
    rod = dados["rodovias"].query("unidade == @unidade")
    mun = dados["municipios"].query("unidade == @unidade")
    est = dados["estruturas"].query("unidade == @unidade")
    principais = rod[rod["tipo"] == "Principal"]
    return {
        "rodovias": rod["rodovia"].nunique(),
        "trechos": len(rod),
        "municipios": mun["municipio"].nunique(),
        "bases": int((est["categoria"] == "Base").sum()),
        "pedagios": int((est["categoria"] == "Pedágio").sum()),
        "estruturas": len(est),
        "extensao": round(float(pd.to_numeric(principais["extensao"], errors="coerce").sum()), 1),
        "df_rodovias": _ordenar(rod, ["tipo", "rodovia", "km_inicial"]),
        "df_municipios": _ordenar(mun, ["rodovia", "km_inicial"]),
        "df_estruturas": _ordenar(est, ["categoria", "rodovia", "km"]),
    }


def perfil_rodovia(dados: dict[str, pd.DataFrame], rodovia: str, unidade: str | None = None) -> dict:
    rod = normalizar_rodovia(rodovia)

    def recorte(df):
        out = df[df["rodovia"] == rod]
        if unidade and unidade != "Todas":
            out = out[out["unidade"] == unidade]
        return out.copy()

    trechos = _ordenar(recorte(dados["rodovias"]), ["km_inicial"])
    mun = _ordenar(recorte(dados["municipios"]), ["km_inicial"])
    est = _ordenar(recorte(dados["estruturas"]), ["categoria", "km"])
    kms = pd.to_numeric(pd.concat([trechos["km_inicial"], trechos["km_final"],
                                   mun["km_inicial"], mun["km_final"]]), errors="coerce").dropna()
    return {
        "rodovia": rod,
        "nome": next((n for n in trechos["nome_rodovia"] if n), ""),
        "unidades": sorted({u for u in list(trechos["unidade"]) + list(mun["unidade"]) if u}),
        "km_inicial": float(kms.min()) if not kms.empty else None,
        "km_final": float(kms.max()) if not kms.empty else None,
        "extensao": round(float(pd.to_numeric(trechos["extensao"], errors="coerce").sum()), 3),
        "trechos": trechos.reset_index(drop=True),
        "municipios": mun.reset_index(drop=True),
        "estruturas": est.reset_index(drop=True),
    }


def perfil_municipio(dados: dict[str, pd.DataFrame], municipio: str) -> dict:
    alvo = str(municipio).casefold()
    mun = dados["municipios"]
    mun = _ordenar(mun[mun["municipio"].str.casefold().str.startswith(alvo)], ["rodovia", "km_inicial"])
    est = dados["estruturas"]
    est = _ordenar(est[est["municipio"].str.casefold().str.startswith(alvo)], ["categoria", "km"])
    return {"trechos": mun.reset_index(drop=True), "estruturas": est.reset_index(drop=True),
            "unidades": sorted({u for u in list(mun["unidade"]) + list(est["unidade"]) if u}),
            "rodovias": sorted({r for r in list(mun["rodovia"]) + list(est["rodovia"]) if r}),
            "extensao": round(float(pd.to_numeric(mun["extensao"], errors="coerce").sum()), 3)}


def _ordenar(df: pd.DataFrame, colunas) -> pd.DataFrame:
    """Ordena apenas pelas colunas existentes; devolve o DataFrame intacto se estiver vazio."""
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    validas = [c for c in colunas if c in df.columns]
    return df.sort_values(validas) if validas else df
