"""Via Appia | Painel Geo-Operacional — pagina inicial (visao geral)."""
import pandas as pd
import streamlit as st

from core.config import configurar_pagina
from core.consulta import consultar_km, resumo_unidade
from core.data import carregar_dados, indicadores, limpar_cache, rodovias_da_unidade
from core.km import float_para_km
from core.ui import botao_exportar, cabecalho, cards, painel_dados, pills, rodape, tabela

configurar_pagina("Visão Geral")
dados = carregar_dados()
ind = indicadores(dados)

cabecalho("Painel Geo-Operacional Via Appia",
          "Consulta centralizada de unidades, rodovias, municípios, bases, praças de pedágio e demais estruturas.")

with st.sidebar:
    st.markdown("### Via Appia")
    st.caption("Navegue pelas páginas ao lado para consultas detalhadas.")
    if st.button("🔄 Recarregar dados", use_container_width=True):
        limpar_cache()
        st.rerun()
    st.divider()
    st.caption("Bases carregadas de `data/*.csv`. Para atualizar, substitua os arquivos e recarregue.")

cards([
    ("Unidades", ind["unidades"], "concessões mapeadas"),
    ("Rodovias", ind["rodovias"], f"{ind['trechos']} trechos cadastrados"),
    ("Municípios", ind["municipios"], "atendidos pelas rodovias"),
    ("Bases", ind["bases"], "SAU, CCO, BSO e operacionais"),
    ("Praças de pedágio", ind["pedagios"], "cadastradas"),
    ("Estruturas", ind["estruturas"], "total no mapa geral"),
], destaque_indices=(4,))
st.caption(f"Extensão somada dos trechos principais cadastrados: **{ind['extensao_principal']} km**")

st.divider()
esq, dir_ = st.columns([1.15, 1], gap="large")

with esq:
    st.subheader("Consulta rápida por km")
    st.caption("Informe a rodovia e o km (formato rodoviário `45+500` ou decimal `45.5`).")
    c1, c2, c3 = st.columns([1, 1, 1])
    unidade = c1.selectbox("Unidade", ["Todas"] + sorted(dados["unidades"]["unidade"]), key="home_uni")
    rodovia = c2.selectbox("Rodovia", rodovias_da_unidade(dados, unidade) or ["—"], key="home_rod")
    km_txt = c3.text_input("Km de referência", value="45+500", key="home_km")

    res = consultar_km(dados, rodovia, km_txt, unidade)
    if res["km"] is None:
        st.error("Km inválido. Use `45+500`, `045+500` ou `45.5`.")
    else:
        mun = res["municipios"]
        base = res["base_mais_proxima"] or {}
        ped = res["pedagio_mais_proximo"] or {}
        linha_mun = mun.iloc[0] if not mun.empty else None
        painel_dados([
            ("Rodovia / Km", f"{res['rodovia']} · km {float_para_km(res['km'])}"),
            ("Unidade", res["unidade"] or "—"),
            ("Município", linha_mun["municipio"] if linha_mun is not None else "não localizado"),
            ("Trecho municipal", f"km {float_para_km(linha_mun['km_inicial'])} a "
                                 f"km {float_para_km(linha_mun['km_final'])}" if linha_mun is not None else "—"),
            ("Base mais próxima", f"{base.get('nome','—')}"
                                  + (f" (km {float_para_km(base.get('km'))} · {base.get('distancia')} km)" if base else "")),
            ("Pedágio mais próximo", f"{ped.get('nome','—')}"
                                     + (f" (km {float_para_km(ped.get('km'))} · {ped.get('distancia')} km)" if ped else "")),
        ], titulo="Resultado")
        if res["fora_de_trecho"]:
            st.warning("Km fora dos intervalos cadastrados para esta rodovia/unidade.")
        st.page_link("pages/6_Consulta_por_KM.py", label="Abrir consulta completa por km →", icon="🔎")

with dir_:
    st.subheader("Unidades da Via Appia")
    for _, u in dados["unidades"].iterrows():
        r = resumo_unidade(dados, u["unidade"])
        with st.expander(f"{u['unidade'].upper()}  ·  {u['lote'] or u['uf']}  ·  {u['status_dados']}"):
            cards([("Rodovias", r["rodovias"], f"{r['trechos']} trechos"),
                   ("Municípios", r["municipios"], "atendidos"),
                   ("Bases", r["bases"], "operacionais"),
                   ("Pedágios", r["pedagios"], "praças")])
            if r["extensao"]:
                st.caption(f"Extensão principal: **{r['extensao']} km**")
            if r["rodovias"]:
                pills(sorted(set(r["df_rodovias"]["rodovia"])))
            st.caption(u["observacao"])

st.divider()
tab1, tab2, tab3 = st.tabs(["Rodovias por unidade", "Estruturas por categoria", "Cobertura dos dados"])

with tab1:
    principais = dados["rodovias"][dados["rodovias"]["tipo"] == "Principal"].sort_values(["unidade", "rodovia", "km_inicial"])
    tabela(principais, ["unidade", "rodovia", "nome_rodovia", "trecho", "km_inicial", "km_final", "extensao"])
    botao_exportar(principais, "via_appia_rodovias_principais.xlsx")

with tab2:
    resumo = (dados["estruturas"].groupby(["unidade", "categoria"]).size()
              .reset_index(name="quantidade").pivot(index="unidade", columns="categoria", values="quantidade").fillna(0).astype(int))
    st.dataframe(resumo, use_container_width=True)

with tab3:
    cob = dados["unidades"][["unidade", "lote", "uf", "status_dados", "observacao"]]
    tabela(cob)
    st.caption("Unidades com status *Parcial* possuem apenas as estruturas do mapa geral; "
               "novas planilhas podem ser incorporadas sem alterar a aplicação.")

rodape()
