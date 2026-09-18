"""Pagina de pracas de pedagio."""
import streamlit as st

from core.config import configurar_pagina
from core.data import carregar_dados, rodovias_da_unidade
from core.filtros import aplicar, busca_texto, filtro_unidade
from core.ui import botao_exportar, cabecalho, cards, rodape, tabela

configurar_pagina("Praças de Pedágio", "💰")
dados = carregar_dados()
cabecalho("Praças de Pedágio", "Localização, rodovia, km e município de cada praça.", "Pedágios")

ped = dados["estruturas"].query("categoria == 'Pedágio'")
if ped.empty:
    ped = dados["pedagios"].assign(categoria="Pedágio")

c1, c2, c3 = st.columns([1, 1, 1.2])
with c1:
    unidade = filtro_unidade(dados, "ped")
with c2:
    rodovia = st.selectbox("Rodovia", ["Todas"] + rodovias_da_unidade(dados, unidade), key="ped_rod")
with c3:
    termo = st.text_input("Pesquisar praça", key="ped_busca", placeholder="ex.: pedágio, Salto, SP300")

df = busca_texto(aplicar(ped, unidade=unidade, rodovia=rodovia), termo,
                 ["nome", "municipio", "rodovia"]).sort_values(["unidade", "rodovia", "km"])

cards([("Praças", len(df), "no recorte"),
       ("Rodovias", df["rodovia"].nunique(), "com pedágio"),
       ("Municípios", df["municipio"].nunique(), "atendidos"),
       ("Unidades", df["unidade"].nunique(), "envolvidas")], destaque_indices=(0,))

tabela(df, ["unidade", "nome", "rodovia", "km", "sentido", "municipio", "latitude", "longitude", "observacao"])
botao_exportar(df, "pedagios_via_appia.xlsx")

st.markdown("#### Praças por unidade e rodovia")
if not df.empty:
    st.dataframe(df.groupby(["unidade", "rodovia"]).size().reset_index(name="Praças"),
                 use_container_width=True, hide_index=True)
rodape()
