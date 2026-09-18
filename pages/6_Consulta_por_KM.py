"""Consulta por quilometro: contexto completo de um km em uma rodovia."""
import streamlit as st

from core.config import configurar_pagina
from core.consulta import consultar_km
from core.data import carregar_dados, rodovias_da_unidade
from core.km import float_para_km, km_para_float
from core.ui import botao_exportar, cabecalho, cards, painel_dados, rodape, tabela

configurar_pagina("Consulta por Km", "🔎")
dados = carregar_dados()
cabecalho("Consulta por Quilômetro",
          "Informe rodovia e km para obter município, trecho, base, pedágio e demais estruturas.", "Consulta")

c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
unidade = c1.selectbox("Unidade", ["Todas"] + sorted(dados["unidades"]["unidade"]), key="ckm_uni")
rodovia = c2.selectbox("Rodovia", rodovias_da_unidade(dados, unidade) or ["—"], key="ckm_rod")
km_txt = c3.text_input("Km de referência", value="45+500", key="ckm_km",
                       help="Formatos aceitos: 45+500, 045+500, 45.5")
raio = c4.slider("Raio de busca (km)", 1.0, 50.0, 10.0, 1.0, key="ckm_raio")

if km_para_float(km_txt) is None:
    st.error("Km inválido. Utilize o formato rodoviário `45+500` ou decimal `45.5`.")
    st.stop()

res = consultar_km(dados, rodovia, km_txt, unidade, raio_estruturas=raio)
mun = res["municipios"]
linha = mun.iloc[0] if not mun.empty else None
base = res["base_mais_proxima"] or {}
ped = res["pedagio_mais_proximo"] or {}

st.markdown(f"### {res['rodovia']} · km {float_para_km(res['km'])}")
cards([("Unidade", res["unidade"] or "—", "responsável"),
       ("Município", linha["municipio"] if linha is not None else "—", "no km consultado"),
       ("Base mais próxima", base.get("nome", "—"), f"{base.get('distancia','—')} km de distância"),
       ("Pedágio mais próximo", ped.get("nome", "—"), f"{ped.get('distancia','—')} km de distância"),
       ("Estruturas no raio", len(res["estruturas"]), f"até {raio:g} km")], destaque_indices=(3,))

if res["fora_de_trecho"]:
    st.warning("O km informado está fora dos intervalos cadastrados para esta rodovia/unidade.")

esq, dir_ = st.columns([1, 1], gap="large")
with esq:
    painel_dados([
        ("Rodovia", res["rodovia"]),
        ("Km consultado", float_para_km(res["km"])),
        ("Unidade", res["unidade"] or "—"),
        ("Município", linha["municipio"] if linha is not None else "não localizado"),
        ("Trecho municipal", f"km {float_para_km(linha['km_inicial'])} a km {float_para_km(linha['km_final'])}"
            if linha is not None else "—"),
        ("Extensão do trecho municipal", f"{linha['extensao']} km" if linha is not None else "—"),
        ("Tipo de via", linha["tipo"] if linha is not None else "—"),
    ], titulo="Localização")
with dir_:
    painel_dados([
        ("Base", f"{base.get('nome','—')} ({base.get('tipo','')})" if base else "—"),
        ("Base · km", float_para_km(base.get("km")) if base else "—"),
        ("Base · município", base.get("municipio", "—") if base else "—"),
        ("Pedágio", ped.get("nome", "—") if ped else "—"),
        ("Pedágio · km", float_para_km(ped.get("km")) if ped else "—"),
        ("Trechos de rodovia no km", len(res["trechos"])),
    ], titulo="Estruturas de referência")

st.divider()
t1, t2, t3 = st.tabs(["Estruturas próximas", "Trechos da rodovia no km", "Municípios no km"])
with t1:
    tabela(res["estruturas"], ["distancia", "categoria", "tipo", "nome", "km", "sentido", "municipio", "unidade"],
           vazio="Nenhuma estrutura cadastrada dentro do raio selecionado.")
    botao_exportar(res["estruturas"], f"estruturas_{res['rodovia']}_km.xlsx")
with t2:
    tabela(res["trechos"], ["unidade", "tipo", "trecho", "nome_rodovia", "km_inicial", "km_final", "extensao"])
with t3:
    tabela(mun, ["municipio", "tipo", "km_inicial", "km_final", "extensao", "unidade"])

rodape()
