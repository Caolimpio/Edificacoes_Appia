"""Pagina de bases e estruturas operacionais."""
import streamlit as st

from core.config import configurar_pagina
from core.data import carregar_dados, rodovias_da_unidade
from core.filtros import aplicar, busca_texto, filtro_faixa_km, filtro_municipio, filtro_unidade
from core.km import float_para_km
from core.ui import botao_exportar, cabecalho, cards, painel_dados, rodape, tabela

configurar_pagina("Bases e Estruturas", "🏗️")
dados = carregar_dados()
est = dados["estruturas"]
cabecalho("Bases e Estruturas", "Localize bases, postos de fiscalização, conservação e demais estruturas.", "Estruturas")

with st.sidebar:
    st.markdown("### Filtros")
    unidade = filtro_unidade(dados, "est")
    rodovia = st.selectbox("Rodovia", ["Todas"] + rodovias_da_unidade(dados, unidade), key="est_rod")
    categorias = ["Todas"] + sorted({c for c in est["categoria"] if c})
    categoria = st.selectbox("Categoria", categorias, key="est_cat")
    municipio = filtro_municipio(dados, unidade, rodovia, "est")

parcial = aplicar(est, unidade=unidade, rodovia=rodovia, municipio=municipio, categoria=categoria)
termo = st.text_input("🔎 Pesquisar por nome da base / estrutura", key="est_busca",
                      placeholder="ex.: SAU 03, base operacional, CCO")
parcial = busca_texto(parcial, termo, ["nome", "tipo", "municipio", "rodovia", "viaturas"])
faixa = filtro_faixa_km(parcial.rename(columns={"km": "km_inicial"}).assign(km_final=None), "est") if not parcial.empty else None
df = aplicar(parcial, faixa_km=faixa, coluna_km="km").sort_values(["categoria", "rodovia", "km"])

cards([("Estruturas", len(df), "no recorte"),
       ("Bases", int((df["categoria"] == "Base").sum()), "SAU/CCO/BSO"),
       ("Pedágios", int((df["categoria"] == "Pedágio").sum()), "praças"),
       ("Viaturas", int(df["qtd_viaturas"].fillna(0).sum()), "somadas")], destaque_indices=(2,))

st.divider()
lista, detalhe = st.columns([1.5, 1], gap="large")
with lista:
    st.markdown("#### Estruturas")
    tabela(df, ["categoria", "tipo", "nome", "unidade", "rodovia", "km", "sentido", "municipio", "qtd_viaturas"], altura=430)
    botao_exportar(df, "estruturas_via_appia.xlsx")
with detalhe:
    st.markdown("#### Detalhe da estrutura")
    if df.empty:
        st.info("Ajuste os filtros para visualizar detalhes.")
    else:
        rotulos = [f"{r['nome']} · {r['rodovia']} km {float_para_km(r['km'])}" for _, r in df.iterrows()]
        idx = rotulos.index(st.selectbox("Selecione", rotulos, key="est_det"))
        r = df.iloc[idx]
        painel_dados([("Nome", r["nome"]), ("Categoria / Tipo", f"{r['categoria']} · {r['tipo']}"),
                      ("Unidade", r["unidade"]), ("Rodovia", r["rodovia"]),
                      ("Km", float_para_km(r["km"])), ("Município", r["municipio"] or "—"),
                      ("Sentido", r["sentido"] or "—"),
                      ("Coordenadas", f"{r['latitude']}, {r['longitude']}" if r["latitude"] == r["latitude"] else "não cadastradas"),
                      ("Viaturas", r["viaturas"] or "—")])
        st.page_link("pages/6_Consulta_por_KM.py", label="Consultar o contexto deste km →", icon="🔎")
        st.page_link("pages/7_Mapa.py", label="Ver no mapa →", icon="🗺️")

rodape()
