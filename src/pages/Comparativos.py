from __future__ import annotations
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st
from api_client import deliveries_list
from utils.helpers import df_to_excel_download

st.title("📈 Comparativos (Mês a Mês)")

token = st.session_state.get("ACESSORIAS_TOKEN", "")
if not token:
    st.stop()

with st.sidebar:
    ano = st.number_input("Ano", min_value=2000, max_value=date.today().year, value=date.today().year)
    run = st.button("🔎 Gerar comparativos")

if not run:
    st.stop()

# monta período anual
dt_ini = date(ano, 1, 1)
dt_fim = date(ano, 12, 31)

raw = deliveries_list(token, "ListAll", dt_ini, dt_fim)

rows = []
for emp in raw:
    ident = emp.get("Identificador")
    razao = emp.get("Razao")
    for ent in emp.get("Entregas", []):
        rows.append({
            "CNPJ_CPF": ident,
            "Razao": razao,
            "Status": ent.get("Status"),
            "DtPrazo": ent.get("EntDtPrazo") or ent.get("EntCompetencia"),
            "Depto": (ent.get("Config") or {}).get("DptoNome"),
        })
df = pd.DataFrame(rows)
if df.empty:
    st.info("Sem dados para o ano selecionado.")
    st.stop()

df["Mes"] = pd.to_datetime(df["DtPrazo"], errors="coerce").dt.to_period("M").astype(str)

# Volume total por mês
vol = df.groupby("Mes").size().reset_index(name="Qtde")
fig = px.line(vol, x="Mes", y="Qtde", title="Volume de Entregas por Mês")
st.plotly_chart(fig, use_container_width=True)

# % atrasadas por mês
atr = (df.assign(Atrasada=(df["Status"] == "Atrasada!").astype(int))
         .groupby("Mes")["Atrasada"].mean()
         .reset_index(name="%Atrasadas"))
atr["%Atrasadas"] = (atr["%Atrasadas"] * 100).round(2)
fig2 = px.line(atr, x="Mes", y="%Atrasadas", title="% de Entregas Atrasadas por Mês")
st.plotly_chart(fig2, use_container_width=True)

# por departamento
dep = df.groupby(["Mes", "Depto"]).size().reset_index(name="Qtde")
fig3 = px.bar(dep, x="Mes", y="Qtde", color="Depto", barmode="group", title="Entregas por Mês e Departamento")
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Bases comparativas")
st.dataframe(df, use_container_width=True, height=420)
df_to_excel_download(df, "comparativo_base.xlsx", sheet_name="base")
