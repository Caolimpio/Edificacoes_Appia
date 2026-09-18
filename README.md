# Via Appia · Painel Geo-Operacional

Aplicação **Python + Streamlit** para centralizar, consultar e explorar as informações
geográficas e operacionais das unidades da Via Appia (rodovias, municípios, bases,
praças de pedágio e demais estruturas).

## 1. Instalação

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

A aplicação abre em `http://localhost:8501`.

## 2. Estrutura do projeto

```text
via_appia/
├── app.py                       # Página inicial (indicadores + consulta rápida por km)
├── pages/
│   ├── 1_Unidades.py            # Resumo por unidade (Colinas, Tietê, Nascentes, Serra…)
│   ├── 2_Rodovias.py            # Trechos, km inicial/final, municípios, estruturas
│   ├── 3_Municipios.py          # Rodovia → km → município e o caminho inverso
│   ├── 4_Bases_e_Estruturas.py  # Busca e detalhe de bases/estruturas
│   ├── 5_Pedagios.py            # Praças de pedágio
│   ├── 6_Consulta_por_KM.py     # Consulta completa por quilômetro
│   ├── 7_Mapa.py                # Mapa interativo (Folium)
│   └── 8_Importar_Dados.py      # Upload/modelos dos CSVs
├── core/
│   ├── config.py                # Paleta, CSS corporativo, caminhos
│   ├── km.py                    # Tratamento de quilometragem (45+500 ↔ 45.5)
│   ├── data.py                  # Carga, normalização e cache dos dados
│   ├── filtros.py               # Filtros dependentes e reutilizáveis
│   ├── consulta.py              # Regras de negócio das consultas
│   ├── mapas.py                 # Mapa Folium + gráfico de trechos municipais
│   └── ui.py                    # Componentes visuais (cards, tabelas, exportação)
├── data/                        # Base de dados (CSV) — única fonte de verdade
├── etl/importar_planilhas.py    # Conversão das planilhas originais → CSV
├── .streamlit/config.toml       # Tema
└── requirements.txt
```

Separação de responsabilidades: **dados** (`data/`), **regras de negócio** (`core/consulta.py`),
**tratamento** (`core/km.py`, `core/data.py`), **interface** (`app.py`, `pages/`) e
**visualizações** (`core/mapas.py`, `core/ui.py`). Nenhum dado está codificado nas páginas.

## 3. Modelo de dados

### `data/unidades.csv`
| coluna | descrição |
|---|---|
| unidade | Nome da unidade (Colinas, Tietê, Nascentes, Serra…) |
| lote | Lote da concessão (ex.: Lote 13) |
| concessionaria | Razão/identificação da concessionária |
| uf | Estado |
| status_dados | `Completo` ou `Parcial` |
| observacao | Nota sobre a cobertura dos dados |

### `data/rodovias.csv`
`unidade, rodovia, nome_rodovia, tipo, trecho, sentido, km_inicial, km_final, extensao, codigo, observacao`
`tipo` = `Principal` | `Acesso` | `Vicinal`. Uma rodovia pode ter vários trechos (linhas).

### `data/municipios.csv`
`unidade, rodovia, municipio, tipo, km_inicial, km_final, extensao`
Um registro por combinação **rodovia + município + trecho**.

### `data/estruturas.csv`
`unidade, categoria, tipo, nome, rodovia, km, sentido, municipio, latitude, longitude, qtd_viaturas, viaturas, observacao`
`categoria` = `Base` | `Pedágio` | `Fiscalização` | `Conservação` | `Outros`.
`tipo` = SAU, CCO, BSO, PGF, Praça de Pedágio, etc.

### `data/pedagios.csv`
Visão derivada das praças de pedágio (mantida para integrações externas).

### `data/coordenadas_municipios.csv`
`municipio, uf, latitude, longitude, fonte` — centroides usados como **fallback** no mapa
enquanto as coordenadas exatas das estruturas não estiverem cadastradas.

## 4. Tratamento de quilômetros

`core/km.py` centraliza a conversão:

| entrada | valor interno | apresentação |
|---|---|---|
| `45+500` | 45.5 | `45+500` |
| `102+200` | 102.2 | `102+200` |
| `1+350` | 1.35 | `1+350` |
| `045+000` | 45.0 | `45+000` |

Funções: `km_para_float`, `float_para_km`, `km_no_intervalo`, `extensao`, `distancia_km`.
Toda comparação (município, trecho, estrutura) usa essas funções — nunca comparação textual.

## 5. Dados carregados nesta versão

Extraídos das planilhas fornecidas:

* **Colinas (Lote 13)** — municípios das SP-075, SP-127, SP-280 e SP-300; trechos das rodovias
  principais (mapa oficial); bases, PGFs, pedágios e conservação.
* **Tietê (Lote 21)** — municípios e acessos (SP-300, SP-101, SP-113, SP-209, SP-308);
  rodovias principais, acessos e vicinais; bases, pedágios, PGF e conservação.
* **Nascentes** e **Serra** — apenas as estruturas do mapa geral (status `Parcial`).

## 6. Atualização dos dados

**Opção A — pela interface:** página *Importar Dados* → baixar modelo → preencher → enviar → recarregar.

**Opção B — via ETL:**

```bash
python etl/importar_planilhas.py \
  --colinas "Municípios Colinas.xlsx" \
  --tiete "Municípios Tietê.xls" \
  --lote21 "LISTA DE RODOVIAS, ACESSOS E VICINAIS- LOTE 21.xls" \
  --edificacoes "Edificações_Appia.xlsx"
```

Para uma **nova unidade**, basta acrescentar linhas em `unidades.csv` e nos demais CSVs —
nenhuma alteração de código é necessária.

## 7. Identidade visual

| Uso | Cor |
|---|---|
| Estrutural / principal | `#1b5d5d` |
| Destaques e alertas | `#ff5400` |
| Secundária | `#3ca4a6` |
| Cinza de apoio | `#bfbfbf` |

## 8. Evolução prevista

Camada de dados isolada em `core/data.py` (`_ler_fonte`): trocar CSV por PostgreSQL/Oracle
exige alterar apenas essa função. Já preparado para: cadastro/edição de estruturas,
histórico de alterações, georreferenciamento de eixos (GeoJSON/KML), indicadores
operacionais e exportação/integração (Excel nativo, Power BI via CSV/SQL).
