"""Componentes visuais reutilizaveis (cabecalho, cards, tabelas, exportacao)."""
from __future__ import annotations
import io
import pandas as pd
import streamlit as st

from core.km import float_para_km

ROTULOS = {
    "unidade": "Unidade", "rodovia": "Rodovia", "nome_rodovia": "Nome da rodovia",
    "tipo": "Tipo", "trecho": "Trecho", "sentido": "Sentido", "codigo": "Código",
    "km": "Km", "km_inicial": "Km inicial", "km_final": "Km final",
    "extensao": "Extensão (km)", "municipio": "Município", "categoria": "Categoria",
    "nome": "Nome", "latitude": "Latitude", "longitude": "Longitude",
    "qtd_viaturas": "Viaturas (qtd)", "viaturas": "Viaturas", "observacao": "Observação",
    "distancia": "Distância (km)", "status_dados": "Status dos dados",
    "concessionaria": "Concessionária", "lote": "Lote", "uf": "UF", "descricao": "Descrição",
}


def cabecalho(titulo: str, subtitulo: str = "", tag: str = "Via Appia") -> None:
    st.markdown(
        f"""<div class="va-header"><span class="va-tag">{tag}</span>
        <h1>{titulo}</h1><p>{subtitulo}</p></div>""",
        unsafe_allow_html=True,
    )


def cards(itens: list[tuple[str, object, str]], destaque_indices=()) -> None:
    """itens = [(rotulo, valor, subtitulo)]"""
    html = ['<div class="va-cards">']
    for i, (rot, val, sub) in enumerate(itens):
        cls = "va-card destaque" if i in destaque_indices else "va-card"
        html.append(f'<div class="{cls}"><div class="rot">{rot}</div>'
                    f'<div class="val">{val}</div><div class="sub">{sub}</div></div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def pills(itens, laranja=False) -> None:
    cls = "va-pill laranja" if laranja else "va-pill"
    st.markdown("".join(f'<span class="{cls}">{i}</span>' for i in itens), unsafe_allow_html=True)


def painel_dados(pares: list[tuple[str, object]], titulo: str = "") -> None:
    if titulo:
        st.markdown(f"**{titulo}**")
    linhas = "".join(f'<div class="lin"><span>{k}</span><b>{v}</b></div>' for k, v in pares)
    st.markdown(f'<div class="va-box">{linhas}</div>', unsafe_allow_html=True)


def formatar_tabela(df: pd.DataFrame, colunas_km=("km", "km_inicial", "km_final")) -> pd.DataFrame:
    """Converte colunas de km para o formato rodoviario e renomeia cabecalhos."""
    out = df.copy()
    for c in colunas_km:
        if c in out.columns:
            out[c] = out[c].map(lambda v: float_para_km(v))
    for c in ("extensao", "distancia"):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").round(3)
    out = out.rename(columns={c: ROTULOS.get(c, c.replace("_", " ").title()) for c in out.columns})
    return out.fillna("")


def tabela(df: pd.DataFrame, colunas=None, altura: int | None = None, vazio: str = "Nenhum registro encontrado.") -> None:
    """Exibe o DataFrame formatado. `altura` em pixels; None deixa o Streamlit dimensionar."""
    if df is None or df.empty:
        st.info(vazio)
        return
    dados = df[[c for c in colunas if c in df.columns]] if colunas else df
    extras = {"height": int(altura)} if altura else {}   # Streamlit >= 1.49 rejeita height=None
    st.dataframe(formatar_tabela(dados), use_container_width=True, hide_index=True, **extras)


def botao_exportar(df: pd.DataFrame, nome_arquivo: str, rotulo: str = "⬇️ Exportar para Excel") -> None:
    if df is None or df.empty:
        return
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        formatar_tabela(df).to_excel(writer, index=False, sheet_name="Dados")
    st.download_button(rotulo, buffer.getvalue(), file_name=nome_arquivo,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def rodape() -> None:
    st.markdown(
        '<div class="va-rodape">Via Appia · Painel Geo-Operacional — dados carregados de <code>data/*.csv</code></div>',
        unsafe_allow_html=True,
    )


def aviso_dados_parciais(unidade: str, status: str) -> None:
    if status and status.lower().startswith("parcial"):
        st.warning(f"A unidade **{unidade}** possui dados parciais: apenas as estruturas do mapa geral "
                   "estão cadastradas. Rodovias e municípios serão complementados nas próximas cargas.")
