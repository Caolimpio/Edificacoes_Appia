"""Pagina de municipios: rodovia -> km -> municipio e caminho inverso."""
import streamlit as st

from core.config import configurar_pagina
from core.consulta import perfil_municipio
from core.data import carregar_dados, municipios_disponiveis, rodovias_da_unidade
from core.filtros import aplicar, filtro_faixa_km, filtro_unidade
from core.mapas import barra_trechos_municipais
from core.ui import botao_exportar, cabecalho, cards, pills, rodape, tabela

configurar_pagina("Municípios", "📍")
dados = carregar_dados()
cabecalho("Municípios", "Relação município ↔ rodovia ↔ quilometragem.", "Municípios")

aba_rod, aba_mun = st.tabs(["Por rodovia", "Por município"])

with aba_rod:
    c1, c2 = st.columns(2)
    with c1:
        unidade = filtro_unidade(dados, "mun_rod")
    with c2:
        rodovia = st.selectbox("Rodovia", ["Todas"] + rodovias_da_unidade(dados, unidade), key="mun_rod_sel")
    base = aplicar(dados["municipios"], unidade=unidade, rodovia=rodovia)
    faixa = filtro_faixa_km(base, "mun_rod") if not base.empty else None
    df = aplicar(base, faixa_km=faixa, coluna_km="km_inicial").sort_values(["rodovia", "km_inicial"])
    cards([("Trechos municipais", len(df), "registros"),
           ("Municípios", df["municipio"].nunique(), "distintos"),
           ("Extensão somada", f"{round(df['extensao'].fillna(0).sum(), 1)} km", "no recorte")])
    tabela(df, ["municipio", "rodovia", "tipo", "km_inicial", "km_final", "extensao", "unidade"])
    botao_exportar(df, "municipios_por_rodovia.xlsx")
    if rodovia != "Todas":
        st.markdown("#### Distribuição dos municípios na rodovia")
        barra_trechos_municipais(df[df["tipo"] != "Acesso"])

with aba_mun:
    c1, c2 = st.columns([1, 1])
    with c1:
        unidade2 = filtro_unidade(dados, "mun_inv")
    with c2:
        opcoes = municipios_disponiveis(dados, unidade2)
        municipio = st.selectbox("Município", opcoes or ["—"], key="mun_inv_sel")
    if municipio and municipio != "—":
        p = perfil_municipio(dados, municipio)
        st.markdown(f"### {municipio}")
        pills(p["unidades"] or ["unidade não informada"])
        pills(p["rodovias"], laranja=True)
        cards([("Rodovias", len(p["rodovias"]), "atendem o município"),
               ("Trechos", len(p["trechos"]), "cadastrados"),
               ("Extensão", f"{p['extensao']} km", "somada"),
               ("Estruturas", len(p["estruturas"]), "no município")])
        st.markdown("#### Trechos rodoviários no município")
        tabela(p["trechos"], ["rodovia", "tipo", "km_inicial", "km_final", "extensao", "unidade"])
        st.markdown("#### Estruturas no município")
        tabela(p["estruturas"], ["categoria", "tipo", "nome", "rodovia", "km", "sentido", "unidade"])
        botao_exportar(p["trechos"], f"trechos_{municipio}.xlsx")

rodape()
