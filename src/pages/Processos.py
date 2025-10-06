from __future__ import annotations
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st
from api_client import processes_list
from utils.helpers import df_to_excel_download

st.title("🧭 Processos")

token = st.session_state.get("ACESSORIAS_TOKEN", "")
if not token:
    st.stop()

with st.sidebar:
    nome = st.text_input("Nome contém", "")
    status_sel = st.selectbox("Status", ["", "A=Ativos", "C=Concluídos", "X=Excluídos"], index=0)
    ini = st.date_input("Início (de)", value=None)
    fim = st.date_input("Início (até)", value=None)
    run = st.button("🔎 Consultar")

if not run:
    st.stop()

status_letter = status_sel.split("=")[0] if status_sel else None
raw = processes_list(token, proc_id_like="*", nome=nome or None,
                     inicio_ini=ini or None, inicio_fim=fim or None,
                     status_letra=status_letter or None)

df = pd.DataFrame(raw)
if df.empty:
    st.info("Nenhum processo encontrado.")
    st.stop()

st.subheader("Linhas de Processos")
st.dataframe(df, use_container_width=True, height=420)
df_to_excel_download(df, "processos_filtrados.xlsx", sheet_name="processos")

if {"ProcDepartamento", "ProcStatus"}.issubset(df.columns):
    grp = df.groupby(["ProcDepartamento", "ProcStatus"]).size().reset_index(name="Qtde")
    fig = px.bar(grp, x="ProcDepartamento", y="Qtde", color="ProcStatus", title="Processos por Departamento e Status")
    st.plotly_chart(fig, use_container_width=True)
