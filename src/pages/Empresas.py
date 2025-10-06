from __future__ import annotations
from datetime import date
import pandas as pd
import streamlit as st
from api_client import companies_from_deliveries, company_detail
from utils.helpers import df_to_excel_download, REGIME_MAP, map_regime, SITUACAO_OPCOES

st.title("🏢 Empresas")

token = st.session_state.get("ACESSORIAS_TOKEN", "")
if not token:
    st.stop()

with st.sidebar:
    hoje = date.today()
    dt_ini = st.date_input("Período base (para catálogo via entregas) – de", hoje.replace(day=1))
    dt_fim = st.date_input("Período base – até", hoje)
    run = st.button("🔎 Atualizar catálogo")

if not run:
    st.stop()

# Catálogo básico (a partir das entregas)
base = companies_from_deliveries(token, dt_ini, dt_fim)
df = pd.DataFrame(base)

# Tenta enriquecer com detalhe (regime/situação) – via chamadas por CNPJ/CPF (cautela com rate limit)
enriquecer = st.toggle("Enriquecer com detalhes de cada empresa (pode ser mais lento)", value=False,
                       help="Consulta /companies/{identificador} para cada empresa para trazer regime e situação.")
if enriquecer:
    regimes = []
    situacoes = []
    for ident in df["Identificador"].tolist():
        try:
            det = company_detail(token, ident, incluir_obrigacoes=False) or {}
        except Exception:
            det = {}
        regimes.append(det.get("regime"))
        situacoes.append(det.get("situacao") or det.get("situacaoCadastral"))
    df["Regime"] = [map_regime(x) for x in regimes]
    df["Situacao"] = situacoes

# Filtros
col1, col2 = st.columns(2)
with col1:
    regime_opts = sorted(list({r for r in df.get("Regime", []).dropna().astype(str).tolist()}))
    regime_sel = st.multiselect("Regime Tributário", regime_opts, default=regime_opts)
with col2:
    sit_opts = sorted(list({s for s in df.get("Situacao", []).dropna().astype(str).tolist()} or SITUACAO_OPCOES))
    sit_sel = st.multiselect("Situação", sit_opts, default=sit_opts)

if "Regime" in df and regime_sel:
    df = df[df["Regime"].astype(str).isin(regime_sel)]
if "Situacao" in df and sit_sel:
    df = df[df["Situacao"].astype(str).isin(sit_sel)]

st.subheader("Catálogo de Empresas")
st.dataframe(df, use_container_width=True, height=450)
df_to_excel_download(df, "empresas_catalogo.xlsx", sheet_name="empresas")
