from __future__ import annotations
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

from api_client import deliveries_list, companies_from_deliveries
from utils.helpers import df_to_excel_download, multi_select_all, map_regime

st.title("📦 Entregas")

token = st.session_state.get("ACESSORIAS_TOKEN", "")
if not token:
    st.stop()

with st.sidebar:
    hoje = date.today()
    dt_ini = st.date_input("Período inicial", hoje.replace(day=1))
    dt_fim = st.date_input("Período final", hoje)
    st.caption("Use 'ListAll' para analisar todas as empresas do portfólio.")

# Carrega catálogo básico de empresas para filtros (fallback via entregas)
cat_empresas = companies_from_deliveries(token, dt_ini, dt_fim)
emp_options = [f'{c.get("Razao","") or "Sem Razão"} | {c.get("Identificador")}' for c in cat_empresas]
emp_sel, _ = multi_select_all("Empresas", emp_options)

status_options = ["Entregue", "Pendente", "Atrasada!"]
status_sel, _ = multi_select_all("Status", status_options)

dpto_filter = st.text_input("Filtrar por Departamento (ex.: Fiscal, DP, Contábil)", "")

run = st.button("🔎 Consultar")

if not run:
    st.stop()

# Busca entregas (todas as empresas) no período
raw = deliveries_list(token, "ListAll", dt_ini, dt_fim)

# Normalização
rows = []
for emp in raw:
    ident = emp.get("Identificador")
    razao = emp.get("Razao")
    for ent in emp.get("Entregas", []):
        rows.append({
            "CNPJ_CPF": ident,
            "Razao": razao,
            "Entrega": ent.get("Nome"),
            "Status": ent.get("Status"),
            "DtPrazo": ent.get("EntDtPrazo") or ent.get("EntCompetencia"),
            "DtAtraso": ent.get("EntDtAtraso"),
            "DtEntrega": ent.get("EntDtEntrega"),
            "Multa": ent.get("EntMulta"),
            "Depto": (ent.get("Config") or {}).get("DptoNome"),
        })
df = pd.DataFrame(rows)

if df.empty:
    st.info("Nenhuma entrega encontrada para o período e filtros.")
    st.stop()

# Filtros locais
if emp_sel:
    idents_selecionados = [opt.split("|")[-1].strip() for opt in emp_sel]
    df = df[df["CNPJ_CPF"].isin(idents_selecionados)]

if status_sel:
    df = df[df["Status"].isin(status_sel)]

if dpto_filter:
    df = df[df["Depto"].fillna("").str.contains(dpto_filter, case=False, na=False)]

st.subheader("Linhas de Entregas")
st.dataframe(df, use_container_width=True, height=420)
df_to_excel_download(df, "entregas_filtradas.xlsx", sheet_name="entregas")

# KPIs
col = st.columns(4)
col[0].metric("Empresas", df["CNPJ_CPF"].nunique())
col[1].metric("Atrasadas", int((df["Status"] == "Atrasada!").sum()))
col[2].metric("Pendentes", int((df["Status"] == "Pendente").sum()))
col[3].metric("Entregues", int((df["Status"] == "Entregue").sum()))

st.divider()

# Ranking de empresas com mais atrasos
st.subheader("🏆 Ranking – Empresas com mais atrasos")
rank = (df[df["Status"] == "Atrasada!"]
        .groupby(["Razao", "CNPJ_CPF"])
        .size()
        .reset_index(name="QtdeAtrasos")
        .sort_values("QtdeAtrasos", ascending=False))
if rank.empty:
    st.info("Nenhuma empresa com atrasos no período.")
else:
    fig = px.bar(rank.head(20), x="Razao", y="QtdeAtrasos", title="Top 20 empresas com mais atrasos")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(rank, use_container_width=True)
    df_to_excel_download(rank, "ranking_atrasos.xlsx", sheet_name="ranking")

st.divider()

# Entregas por Departamento e Status
st.subheader("Entregas por Departamento x Status")
grp = df.groupby(["Depto", "Status"], dropna=False).size().reset_index(name="Qtde")
fig2 = px.bar(grp, x="Depto", y="Qtde", color="Status", barmode="group")
st.plotly_chart(fig2, use_container_width=True)

# Entregas por Empresa (todas)
st.subheader("Entregas por Empresa e Status")
grp2 = df.groupby(["Razao", "Status"]).size().reset_index(name="Qtde")
fig3 = px.bar(grp2, x="Razao", y="Qtde", color="Status")
st.plotly_chart(fig3, use_container_width=True)
