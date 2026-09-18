"""ETL de referencia: converte as planilhas originais nos CSVs de `data/`.

Uso:
    python etl/importar_planilhas.py --colinas "Municípios Colinas.xlsx" \
        --tiete "Municípios Tietê.xls" --lote21 "LISTA DE RODOVIAS...xls" \
        --edificacoes "Edificações_Appia.xlsx"

Cada funcao trata uma planilha; para novas unidades, replique o padrao e acrescente
as linhas nos DataFrames finais. Os CSVs sao sempre reescritos por completo.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import pandas as pd

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.km import extensao, km_para_float  # noqa: E402

import re

def nome_municipio(valor: str) -> tuple[str, str]:
    """Separa o municipio do rotulo de acesso: 'Conchas - 193 / 300' -> ('Conchas', rotulo)."""
    s = LIMPAR(valor)
    m = re.match(r"^(.*?)\s*-\s*\d{2,3}\s*/\s*\d{2,3}$", s)
    return (m.group(1).strip(), s) if m else (s, "")

DATA = Path(__file__).resolve().parent.parent / "data"
LIMPAR = lambda v: "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()
SIGLA = lambda v: LIMPAR(v).upper().replace(" ", "").replace("-", "")

CATEGORIAS = {
    "SAU": ("Base", "SAU"), "CCO": ("Base", "CCO"), "BSO": ("Base", "BSO"),
    "PGFS": ("Fiscalização", "PGF"), "PGF": ("Fiscalização", "PGF"),
    "PEDÁGIOS": ("Pedágio", "Praça de Pedágio"), "PEDAGIOS": ("Pedágio", "Praça de Pedágio"),
    "SOLUCIONA CONSERVAÇÃO": ("Conservação", "Soluciona Conservação"),
}


def municipios_colinas(caminho: Path) -> list[dict]:
    df = pd.read_excel(caminho, sheet_name="SEPARADO POR ,", header=None)
    linhas = []
    for _, r in df.iterrows():
        ki, kf, rod, mun = km_para_float(r[0]), km_para_float(r[1]), SIGLA(r[2]), LIMPAR(r[3]).title()
        if ki is None or not rod.startswith("SP") or not mun:
            continue
        linhas.append(dict(unidade="Colinas", rodovia=rod, municipio=mun, tipo="Rodovia",
                           km_inicial=ki, km_final=kf, extensao=extensao(ki, kf), descricao=""))
    return linhas


def municipios_tiete(caminho: Path) -> list[dict]:
    df = pd.read_excel(caminho, sheet_name="planilha inss", header=None)
    linhas, rodovia = [], ""
    for _, r in df.iterrows():
        mun, rod, tipo = LIMPAR(r[2]), SIGLA(r[3]), LIMPAR(r[4])
        ki, kf = km_para_float(r[5]), km_para_float(r[6])
        if rod.startswith("SP"):
            rodovia = rod
        if not mun or ki is None or tipo not in ("Rodovia", "Acesso"):
            continue
        nome, rotulo = nome_municipio(mun.title())
        linhas.append(dict(unidade="Tietê", rodovia=rodovia, municipio=nome, tipo=tipo,
                           km_inicial=ki, km_final=kf, extensao=extensao(ki, kf), descricao=rotulo))
    return linhas


def rodovias_lote21(caminho: Path) -> list[dict]:
    xl = pd.ExcelFile(caminho)
    def cabecalho(df):
        for i, r in df.iterrows():
            if any(LIMPAR(v).upper().startswith("ROD.") for v in r.tolist()):
                return i
        return 0
    linhas = []
    mapa = {"RODOVIAS PRINCIPAIS": "Principal", "RODOVIAS DE ACESSOS ": "Acesso", "RODOVIAS VICINAIS": "Vicinal"}
    for aba, tipo in mapa.items():
        if aba not in xl.sheet_names:
            continue
        df = xl.parse(aba, header=None)
        for _, r in df.iloc[cabecalho(df) + 1:].iterrows():
            rod = SIGLA(r[0])
            if not rod:
                continue
            if tipo == "Vicinal":
                acesso, ext = km_para_float(r[5]), km_para_float(r[4])
                ki = acesso
                kf = None if acesso is None or ext is None else round(acesso + ext, 3)
                registro = dict(nome_rodovia=LIMPAR(r[3]).title(), trecho=LIMPAR(r[1]).title(),
                                codigo=LIMPAR(r[2]), observacao=LIMPAR(r[6]))
            else:
                ki, kf = km_para_float(r[2]), km_para_float(r[3])
                registro = dict(nome_rodovia=LIMPAR(r[4]).title(),
                                trecho=LIMPAR(r[1]).title() if tipo == "Principal" else "",
                                codigo="" if tipo == "Principal" else LIMPAR(r[1]), observacao="")
            linhas.append(dict(unidade="Tietê", rodovia=rod, tipo=tipo, sentido="",
                               km_inicial=ki, km_final=kf, extensao=extensao(ki, kf), **registro))
    return linhas


def estruturas_edificacoes(caminho: Path, unidades: dict[str, str]) -> list[dict]:
    xl = pd.ExcelFile(caminho)
    linhas = []
    for aba, unidade in unidades.items():
        if aba not in xl.sheet_names:
            continue
        df = xl.parse(aba, header=None)
        idx = next((i for i, r in df.iterrows() if any(LIMPAR(v).upper() == "BASE" for v in r.tolist())), None)
        if idx is None:
            continue
        cols = {LIMPAR(v).upper(): j for j, v in enumerate(df.iloc[idx].tolist()) if LIMPAR(v)}
        get = lambda r, k: LIMPAR(r[cols[k]]) if k in cols else ""
        categoria = tipo = ""
        for _, r in df.iloc[idx + 1:].iterrows():
            nome = get(r, "BASE")
            if "LEGENDA" in nome.upper():
                break
            if not nome:
                continue
            rod, km, mun = get(r, "RODOVIA"), get(r, "KM"), get(r, "MUNICÍPIO")
            if not rod and not km and not mun:  # linha de secao
                categoria, tipo = CATEGORIAS.get(nome.upper().strip(), ("Outros", nome.title()))
                continue
            linhas.append(dict(unidade=unidade, categoria=categoria, tipo=tipo, nome=nome,
                               rodovia=SIGLA(rod), km=km_para_float(km), sentido=get(r, "SENTIDO").title(),
                               municipio=mun.title(), latitude="", longitude="",
                               qtd_viaturas=km_para_float(get(r, "TOTAL")), viaturas=get(r, "VIATURAS"),
                               observacao=""))
    return linhas


def main() -> None:
    p = argparse.ArgumentParser(description="Gera os CSVs de data/ a partir das planilhas originais.")
    p.add_argument("--colinas"); p.add_argument("--tiete")
    p.add_argument("--lote21"); p.add_argument("--edificacoes")
    a = p.parse_args()

    municipios = []
    if a.colinas:
        municipios += municipios_colinas(Path(a.colinas))
    if a.tiete:
        municipios += municipios_tiete(Path(a.tiete))
    if municipios:
        pd.DataFrame(municipios).to_csv(DATA / "municipios.csv", index=False, encoding="utf-8-sig")
        print(f"municipios.csv: {len(municipios)} linhas")

    if a.lote21:
        rod = rodovias_lote21(Path(a.lote21))
        antigo = pd.read_csv(DATA / "rodovias.csv", encoding="utf-8-sig") if (DATA / "rodovias.csv").exists() else pd.DataFrame()
        base = antigo[antigo["unidade"] != "Tietê"] if not antigo.empty else pd.DataFrame()
        pd.concat([base, pd.DataFrame(rod)], ignore_index=True).to_csv(DATA / "rodovias.csv", index=False, encoding="utf-8-sig")
        print(f"rodovias.csv atualizado (+{len(rod)} linhas Tietê)")

    if a.edificacoes:
        est = estruturas_edificacoes(Path(a.edificacoes),
                                     {"COLINAS": "Colinas", "TIETÊ": "Tietê", "NASCENTES": "Nascentes", "SERRA": "Serra"})
        df = pd.DataFrame(est)
        df.to_csv(DATA / "estruturas.csv", index=False, encoding="utf-8-sig")
        df[df["categoria"] == "Pedágio"][["unidade", "nome", "rodovia", "km", "sentido", "municipio",
                                          "latitude", "longitude", "observacao"]].to_csv(
            DATA / "pedagios.csv", index=False, encoding="utf-8-sig")
        print(f"estruturas.csv: {len(df)} linhas")


if __name__ == "__main__":
    main()
