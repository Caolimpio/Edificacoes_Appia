"""Mapa interativo das estruturas da Via Appia."""
import streamlit as st

from core.config import configurar_pagina
from core.data import carregar_dados, rodovias_da_unidade
from core.filtros import aplicar, filtro_municipio, filtro_unidade
from core.mapas import mapa_estruturas, resolver_coordenadas
from core.ui import cabecalho, cards, rodape, tabela

configurar_pagina("Mapa", "🗺️")
dados = carregar_dados()
est = dados["estruturas"]
cabecalho("Mapa Operacional", "Visualização geográfica de bases, pedágios e demais estruturas.", "Mapa")

with st.sidebar:
    st.markdown("### Filtros do mapa")
    unidade = filtro_unidade(dados, "map")
    rodovia = st.selectbox("Rodovia", ["Todas"] + rodovias_da_unidade(dados, unidade), key="map_rod")
    cats = sorted({c for c in est["categoria"] if c})
    escolhidas = st.multiselect("Categorias", cats, default=cats, key="map_cat")
    municipio = filtro_municipio(dados, unidade, rodovia, "map")
    agrupar = st.checkbox("Agrupar marcadores (clusters)", value=True, key="map_cluster")

df = aplicar(est, unidade=unidade, rodovia=rodovia, municipio=municipio)
if escolhidas:
    df = df[df["categoria"].isin(escolhidas)]

coords = resolver_coordenadas(df)
com_coord = coords.dropna(subset=["latitude", "longitude"])
cards([("Estruturas filtradas", len(df), "no recorte"),
       ("Com coordenada", len(com_coord), "plotáveis no mapa"),
       ("Aproximadas", int(com_coord["coord_aproximada"].sum()), "centroide municipal"),
       ("Sem coordenada", len(df) - len(com_coord), "aguardando cadastro")], destaque_indices=(3,))

clique = mapa_estruturas(df, agrupar=agrupar)
if clique and clique.get("last_object_clicked_tooltip"):
    st.success(f"Selecionado: {clique['last_object_clicked_tooltip']}")

st.caption("Coordenadas aproximadas usam o centroide do município (`data/coordenadas_municipios.csv`) "
           "quando latitude/longitude da estrutura não estão cadastradas. Substitua por coordenadas oficiais "
           "em `data/estruturas.csv` para precisão de campo.")

with st.expander("Estruturas sem coordenadas cadastradas"):
    tabela(coords[coords["latitude"].isna()], ["unidade", "categoria", "nome", "rodovia", "km", "municipio"],
           vazio="Todas as estruturas filtradas possuem coordenadas.")
rodape()
