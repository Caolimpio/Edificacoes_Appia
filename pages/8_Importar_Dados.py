"""Importacao/atualizacao das bases CSV (preparacao para novas planilhas e unidades)."""
import pandas as pd
import streamlit as st

from core.config import DATA_DIR, configurar_pagina
from core.data import TABELAS, carregar_dados, limpar_cache
from core.ui import cabecalho, rodape, tabela

configurar_pagina("Importar Dados", "📥")
dados = carregar_dados()
cabecalho("Importar / Atualizar Dados",
          "Substitua as bases CSV ou baixe os modelos para incorporar novas unidades e planilhas.", "Dados")

st.info("Fluxo recomendado: baixe o modelo → preencha com os dados reais → envie o arquivo → recarregue o cache. "
        "Nenhum dado está codificado nas páginas: tudo vem de `data/*.csv`.")

tabela_escolhida = st.selectbox("Tabela", list(TABELAS.keys()), key="imp_tab")
colunas = TABELAS[tabela_escolhida]
atual = dados[tabela_escolhida]

c1, c2 = st.columns([1, 1])
with c1:
    st.markdown("**Modelo de colunas**")
    st.code(",".join(colunas), language="text")
    st.download_button("⬇️ Baixar modelo vazio (CSV)",
                       pd.DataFrame(columns=colunas).to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"modelo_{tabela_escolhida}.csv", mime="text/csv")
    st.download_button("⬇️ Baixar base atual (CSV)",
                       atual.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"{tabela_escolhida}.csv", mime="text/csv")
with c2:
    st.markdown("**Enviar nova versão**")
    arquivo = st.file_uploader("Arquivo CSV ou Excel", type=["csv", "xlsx", "xls"], key="imp_up")
    if arquivo is not None:
        novo = (pd.read_csv(arquivo, dtype=str, keep_default_na=False)
                if arquivo.name.lower().endswith(".csv") else pd.read_excel(arquivo, dtype=str))
        faltando = [c for c in colunas if c not in novo.columns]
        st.write(f"Linhas lidas: **{len(novo)}**")
        if faltando:
            st.error(f"Colunas ausentes: {', '.join(faltando)}")
        else:
            st.dataframe(novo.head(15), use_container_width=True, hide_index=True)
            if st.button("💾 Substituir base", type="primary", use_container_width=True):
                destino = DATA_DIR / f"{tabela_escolhida}.csv"
                destino.parent.mkdir(parents=True, exist_ok=True)
                novo.to_csv(destino, index=False, encoding="utf-8-sig")
                limpar_cache()
                st.success(f"`{destino.name}` atualizado com {len(novo)} linhas. Recarregue as páginas.")

st.divider()
st.markdown(f"#### Conteúdo atual · `{tabela_escolhida}.csv` ({len(atual)} linhas)")
tabela(atual, altura=380)
rodape()
