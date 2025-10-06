from __future__ import annotations
import os
import streamlit as st

st.set_page_config(page_title="Acessórias – Análise Contábil", layout="wide", page_icon="📊")

st.title("📊 Plataforma de Análise Contábil – Acessórias API")

token = ""
try:
    token = st.secrets.get("ACESSORIAS_TOKEN", "")
except Exception:
    pass
if not token:
    token = os.getenv("ACESSORIAS_TOKEN", "")

st.session_state["ACESSORIAS_TOKEN"] = token

if not token:
    st.warning("Informe seu token (Bearer) para usar a API.")
    typed = st.text_input("Token da API", type="password", help="Cole aqui se não estiver em secrets.toml nem variável de ambiente.")
    if typed:
        st.session_state["ACESSORIAS_TOKEN"] = typed
        st.success("Token carregado na sessão. Abra uma página no menu lateral.")
else:
    st.info("Token carregado. Use as páginas no menu lateral para navegar.")
