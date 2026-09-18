"""Pagina de unidades: resumo operacional e geografico por unidade."""
import streamlit as st

from core.config import configurar_pagina
from core.consulta import resumo_unidade
from core.data import carregar_dados
from core.ui import (aviso_dados_parciais, botao_exportar, cabecalho, cards, pills, rodape, tabela)

configurar_pagina("Unidades", "🏢")
dados = carregar_dados()
cabecalho("Unidades", "Resumo operacional e geográfico de cada unidade da Via Appia.", "Unidades")

unidades = sorted(dados["unidades"]["unidade"])
abas = st.tabs([u.upper() for u in unidades])

for aba, unidade in zip(abas, unidades):
    with aba:
        info = dados["unidades"].query("unidade == @unidade").iloc[0]
        r = resumo_unidade(dados, unidade)
        st.markdown(f"### {unidade.upper()}")
        pills([x for x in (info["concessionaria"], info["lote"], info["uf"]) if x])
        aviso_dados_parciais(unidade, info["status_dados"])
        cards([("Rodovias", r["rodovias"], f"{r['trechos']} trechos"),
               ("Municípios", r["municipios"], "atendidos"),
               ("Bases", r["bases"], "operacionais"),
               ("Pedágios", r["pedagios"], "praças"),
               ("Estruturas", r["estruturas"], "total cadastrado"),
               ("Extensão", f"{r['extensao']} km", "trechos principais")], destaque_indices=(3,))

        st.divider()
        t1, t2, t3 = st.tabs(["Rodovias e intervalos de km", "Municípios", "Estruturas"])
        with t1:
            tipos = sorted({t for t in r["df_rodovias"]["tipo"] if t})
            escolha = st.multiselect("Tipo de via", tipos, default=tipos, key=f"tipo_{unidade}")
            df = r["df_rodovias"][r["df_rodovias"]["tipo"].isin(escolha)] if escolha else r["df_rodovias"]
            tabela(df, ["rodovia", "nome_rodovia", "tipo", "trecho", "km_inicial", "km_final", "extensao", "codigo"],
                   vazio="Rodovias ainda não cadastradas para esta unidade.")
            botao_exportar(df, f"rodovias_{unidade}.xlsx")
        with t2:
            tabela(r["df_municipios"], ["municipio", "rodovia", "tipo", "km_inicial", "km_final", "extensao"],
                   vazio="Municípios ainda não cadastrados para esta unidade.")
            botao_exportar(r["df_municipios"], f"municipios_{unidade}.xlsx")
        with t3:
            tabela(r["df_estruturas"], ["categoria", "tipo", "nome", "rodovia", "km", "sentido", "municipio", "viaturas"])
            botao_exportar(r["df_estruturas"], f"estruturas_{unidade}.xlsx")

rodape()
