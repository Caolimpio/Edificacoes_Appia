"""Visualizacao cartografica (Folium) com fallback por centroide municipal."""
from __future__ import annotations
import pandas as pd
import streamlit as st

from core.config import CORES_CATEGORIA, DATA_DIR, PRIMARIA
from core.km import float_para_km

_ICONES = {"Base": "home", "Pedágio": "usd", "Fiscalização": "check", "Conservação": "wrench"}


@st.cache_data
def centroides_municipais() -> pd.DataFrame:
    """Coordenadas aproximadas de referencia (substituir por dados oficiais quando disponiveis)."""
    caminho = DATA_DIR / "coordenadas_municipios.csv"
    if not caminho.exists():
        return pd.DataFrame(columns=["municipio", "uf", "latitude", "longitude"])
    df = pd.read_csv(caminho, encoding="utf-8-sig")
    df["chave"] = df["municipio"].astype(str).str.casefold().str.strip()
    return df


def resolver_coordenadas(df: pd.DataFrame) -> pd.DataFrame:
    """Preenche latitude/longitude ausentes com o centroide do municipio (marcado como aproximado)."""
    out = df.copy()
    for c in ("latitude", "longitude"):
        out[c] = pd.to_numeric(out.get(c), errors="coerce")
    cent = centroides_municipais()
    if cent.empty:
        out["coord_aproximada"] = False
        return out
    mapa_lat = dict(zip(cent["chave"], cent["latitude"]))
    mapa_lon = dict(zip(cent["chave"], cent["longitude"]))
    chave = out["municipio"].astype(str).str.casefold().str.strip()
    faltando = out["latitude"].isna() | out["longitude"].isna()
    out["coord_aproximada"] = faltando & chave.isin(mapa_lat)
    out.loc[faltando, "latitude"] = chave[faltando].map(mapa_lat)
    out.loc[faltando, "longitude"] = chave[faltando].map(mapa_lon)
    return out


def _popup(linha: pd.Series) -> str:
    itens = [("Unidade", linha.get("unidade")), ("Tipo", linha.get("tipo")),
             ("Rodovia", linha.get("rodovia")), ("Km", float_para_km(linha.get("km"))),
             ("Município", linha.get("municipio")), ("Sentido", linha.get("sentido")),
             ("Viaturas", linha.get("viaturas"))]
    corpo = "".join(f"<tr><td style='color:#6b7c7c;padding-right:8px'>{k}</td>"
                    f"<td><b>{v}</b></td></tr>" for k, v in itens if v not in (None, "", "—"))
    aviso = ("<div style='color:#ff5400;font-size:11px;margin-top:6px'>Coordenada aproximada "
             "(centroide municipal)</div>" if linha.get("coord_aproximada") else "")
    return (f"<div style='font-family:sans-serif;font-size:12.5px;min-width:210px'>"
            f"<div style='color:{PRIMARIA};font-weight:700;margin-bottom:5px'>{linha.get('nome','')}</div>"
            f"<table>{corpo}</table>{aviso}</div>")


def mapa_estruturas(df: pd.DataFrame, altura: int = 560, agrupar: bool = True):
    """Renderiza mapa interativo das estruturas; retorna o objeto de interacao do streamlit-folium."""
    import folium
    from folium.plugins import MarkerCluster
    from streamlit_folium import st_folium

    dados = resolver_coordenadas(df).dropna(subset=["latitude", "longitude"])
    if dados.empty:
        st.info("Nenhuma estrutura com coordenadas disponíveis para os filtros selecionados. "
                "Preencha latitude/longitude em `data/estruturas.csv` ou o centroide em "
                "`data/coordenadas_municipios.csv`.")
        return None

    centro = [dados["latitude"].mean(), dados["longitude"].mean()]
    mapa = folium.Map(location=centro, zoom_start=8, tiles="cartodbpositron", control_scale=True)
    camadas = {}
    for categoria, grupo in dados.groupby("categoria"):
        cor = CORES_CATEGORIA.get(categoria, CORES_CATEGORIA["Outros"])
        camada = folium.FeatureGroup(name=f"{categoria} ({len(grupo)})", show=True)
        alvo = MarkerCluster().add_to(camada) if (agrupar and len(grupo) > 25) else camada
        for _, linha in grupo.iterrows():
            folium.Marker(
                [linha["latitude"], linha["longitude"]],
                tooltip=f"{linha.get('nome','')} · {linha.get('rodovia','')} km {float_para_km(linha.get('km'))}",
                popup=folium.Popup(_popup(linha), max_width=320),
                icon=folium.Icon(color="white", icon_color=cor,
                                 icon=_ICONES.get(categoria, "info-sign"), prefix="glyphicon"),
            ).add_to(alvo)
        camada.add_to(mapa)
        camadas[categoria] = len(grupo)
    folium.LayerControl(collapsed=False).add_to(mapa)
    if len(dados) > 1:
        mapa.fit_bounds([[dados["latitude"].min(), dados["longitude"].min()],
                         [dados["latitude"].max(), dados["longitude"].max()]], padding=(25, 25))
    return st_folium(mapa, use_container_width=True, height=altura, returned_objects=["last_object_clicked_tooltip"])


def barra_trechos_municipais(df_municipios: pd.DataFrame, altura: int = 320):
    """Grafico horizontal (km inicial -> km final) dos municipios de uma rodovia."""
    if df_municipios.empty:
        st.info("Sem trechos municipais cadastrados.")
        return
    dados = df_municipios.dropna(subset=["km_inicial"]).copy()
    dados["km_final"] = pd.to_numeric(dados["km_final"], errors="coerce").fillna(dados["km_inicial"])
    dados = dados.sort_values("km_inicial")
    grafico = pd.DataFrame({"Município": dados["municipio"] + " (" + dados["tipo"].fillna("") + ")",
                            "Início do trecho": dados["km_inicial"],
                            "Extensão": (dados["km_final"] - dados["km_inicial"]).clip(lower=0.05)}
                           ).set_index("Município")
    st.bar_chart(grafico, horizontal=True, height=altura, color=["#e6ecec", PRIMARIA],
                 stack=True, use_container_width=True)
    st.caption("Barra clara = km de início do trecho · barra escura = extensão do município na rodovia.")
