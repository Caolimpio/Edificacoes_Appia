"""Pagina de rodovias: intervalos de km, municipios, bases e pedagios por rodovia."""
import streamlit as st

from core.config import configurar_pagina
from core.consulta import perfil_rodovia
from core.data import carregar_dados, rodovias_da_unidade
from core.filtros import busca_texto, filtro_unidade
from core.km import float_para_km
from core.mapas import barra_trechos_municipais
from core.ui import botao_exportar, cabecalho, cards, pills, rodape, tabela

configurar_pagina("Rodovias", "🛣️")
dados = carregar_dados()
cabecalho("Rodovias", "Consulte trechos, quilometragem, municípios e estruturas de cada rodovia.", "Rodovias")

c1, c2, c3 = st.columns([1, 1, 1.2])
with c1:
    unidade = filtro_unidade(dados, "rod")
with c2:
    lista = rodovias_da_unidade(dados, unidade)
    rodovia = st.selectbox("Rodovia", lista or ["—"], key="rod_sel")
with c3:
    termo = st.text_input("Pesquisar rodovia (sigla, nome ou trecho)", key="rod_busca",
                          placeholder="ex.: castello branco, SP300, vicinal")

if termo:
    st.markdown("#### Resultados da pesquisa")
    res = busca_texto(dados["rodovias"], termo, ["rodovia", "nome_rodovia", "trecho", "codigo", "tipo"])
    tabela(res, ["unidade", "rodovia", "nome_rodovia", "tipo", "trecho", "km_inicial", "km_final", "extensao"])
    st.divider()

if rodovia and rodovia != "—":
    p = perfil_rodovia(dados, rodovia, unidade)
    st.markdown(f"### {p['rodovia']}" + (f" — {p['nome']}" if p["nome"] else ""))
    pills(p["unidades"] or ["unidade não informada"])
    cards([("Km inicial", float_para_km(p["km_inicial"]), "menor km cadastrado"),
           ("Km final", float_para_km(p["km_final"]), "maior km cadastrado"),
           ("Extensão", f"{p['extensao']} km", f"{len(p['trechos'])} trecho(s)"),
           ("Municípios", p["municipios"]["municipio"].nunique(), "atravessados"),
           ("Bases", int((p["estruturas"]["categoria"] == "Base").sum()), "na rodovia"),
           ("Pedágios", int((p["estruturas"]["categoria"] == "Pedágio").sum()), "na rodovia")],
          destaque_indices=(5,))

    t1, t2, t3, t4 = st.tabs(["Trechos", "Municípios (km inicial/final)", "Bases e estruturas", "Perfil visual"])
    with t1:
        tabela(p["trechos"], ["unidade", "tipo", "trecho", "nome_rodovia", "km_inicial", "km_final", "extensao", "codigo", "observacao"])
        botao_exportar(p["trechos"], f"trechos_{p['rodovia']}.xlsx")
    with t2:
        tabela(p["municipios"], ["municipio", "tipo", "km_inicial", "km_final", "extensao", "unidade"])
        botao_exportar(p["municipios"], f"municipios_{p['rodovia']}.xlsx")
    with t3:
        tabela(p["estruturas"], ["categoria", "tipo", "nome", "km", "sentido", "municipio", "unidade", "viaturas"])
        botao_exportar(p["estruturas"], f"estruturas_{p['rodovia']}.xlsx")
    with t4:
        barra_trechos_municipais(p["municipios"][p["municipios"]["tipo"] != "Acesso"])
        estr = p["estruturas"].dropna(subset=["km"])
        if not estr.empty:
            st.markdown("**Estruturas ao longo da rodovia**")
            tabela(estr.sort_values("km"), ["km", "categoria", "nome", "municipio", "sentido"])
else:
    st.info("Selecione uma unidade com rodovias cadastradas.")

rodape()
