"""Configuracoes globais: paleta, identidade visual e CSS da aplicacao."""
from pathlib import Path
import streamlit as st

APP_NAME = "Via Appia | Painel Geo-Operacional"
APP_ICON = "🛣️"

# Paleta corporativa obrigatoria
PRIMARIA = "#1b5d5d"
DESTAQUE = "#ff5400"
SECUNDARIA = "#3ca4a6"
CINZA = "#bfbfbf"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CORES_CATEGORIA = {
    "Base": PRIMARIA,
    "Pedágio": DESTAQUE,
    "Fiscalização": SECUNDARIA,
    "Conservação": "#7a8c8c",
    "Outros": CINZA,
}

_CSS = """
<style>
:root {
  --primaria:#1b5d5d; --destaque:#ff5400; --secundaria:#3ca4a6; --cinza:#bfbfbf;
}
.block-container {padding-top:1.6rem; padding-bottom:2.5rem; max-width:1400px;}
h1,h2,h3,h4 {color:var(--primaria); font-weight:700; letter-spacing:-.2px;}
hr {border-color:#e6ecec;}

/* Cabecalho */
.va-header {background:linear-gradient(100deg,#1b5d5d 0%,#24706f 55%,#3ca4a6 100%);
  border-radius:14px; padding:22px 26px; color:#fff; margin-bottom:18px;}
.va-header h1 {color:#fff; margin:0; font-size:1.55rem; line-height:1.2;}
.va-header p {margin:.35rem 0 0; color:#dfeeee; font-size:.92rem;}
.va-header .va-tag {display:inline-block; background:var(--destaque); color:#fff;
  font-size:.68rem; font-weight:700; letter-spacing:.9px; padding:3px 10px;
  border-radius:20px; text-transform:uppercase; margin-bottom:8px;}

/* Cards de indicadores */
.va-cards {display:flex; flex-wrap:wrap; gap:14px;}
.va-card {flex:1 1 165px; background:#fff; border:1px solid #e6ecec; border-left:5px solid var(--primaria);
  border-radius:12px; padding:14px 16px; box-shadow:0 1px 3px rgba(27,93,93,.07);}
.va-card.destaque {border-left-color:var(--destaque);}
.va-card .rot {font-size:.7rem; text-transform:uppercase; letter-spacing:.8px; color:#6b7c7c; font-weight:700;}
.va-card .val {font-size:1.7rem; font-weight:800; color:var(--primaria); line-height:1.15;}
.va-card .sub {font-size:.75rem; color:#8a9a9a;}

/* Pills / badges */
.va-pill {display:inline-block; padding:3px 10px; border-radius:20px; font-size:.72rem;
  font-weight:700; background:#eaf4f4; color:var(--primaria); margin:0 6px 6px 0;}
.va-pill.laranja {background:#fff0e8; color:var(--destaque);}
.va-pill.cinza {background:#f2f4f4; color:#6b7c7c;}

/* Painel de resultado */
.va-box {background:#f7fafa; border:1px solid #e6ecec; border-radius:12px; padding:16px 18px;}
.va-box .lin {display:flex; justify-content:space-between; gap:12px; padding:6px 0;
  border-bottom:1px dashed #e2e9e9; font-size:.9rem;}
.va-box .lin:last-child {border-bottom:none;}
.va-box .lin b {color:var(--primaria);}

/* Tabelas e widgets */
[data-testid="stDataFrame"] {border:1px solid #e6ecec; border-radius:10px;}
div[data-baseweb="tab-list"] {gap:4px; border-bottom:2px solid #eef2f2;}
button[data-baseweb="tab"] {font-weight:600;}
section[data-testid="stSidebar"] {background:#f4f7f7; border-right:1px solid #e6ecec;}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2 {font-size:1.05rem;}
.stButton>button {border-radius:8px; font-weight:600;}
.va-rodape {color:#8a9a9a; font-size:.75rem; text-align:center; margin-top:26px;}

@media (max-width:820px){
  .block-container {padding-left:.8rem; padding-right:.8rem;}
  .va-card {flex:1 1 44%;}
  .va-header h1 {font-size:1.2rem;}
}
</style>
"""


def configurar_pagina(titulo: str, icone: str = APP_ICON) -> None:
    """Aplica configuracao de pagina + CSS (chamar como primeira instrucao de cada pagina)."""
    st.set_page_config(page_title=f"{titulo} · Via Appia", page_icon=icone, layout="wide")
    st.markdown(_CSS, unsafe_allow_html=True)
