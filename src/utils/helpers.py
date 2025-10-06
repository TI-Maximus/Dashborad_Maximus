from __future__ import annotations
from typing import Dict, Iterable, Tuple
from io import BytesIO
import pandas as pd
import streamlit as st

# Regimes conhecidos (ajuste conforme sua realidade na API)
REGIME_MAP: Dict[int, str] = {
    0: "Indefinido",
    1: "SN c/ IE",
    2: "SN s/ IE",
    3: "LP c/ IE (ind/comb)",
    4: "LP s/ IE (serv.)",
    5: "Lucro Real",
    6: "MEI",
    7: "eSocial/Empregador",
    8: "Produtor Rural",
    9: "Pessoa Física",
    10: "Imune/Isenta",
}

SITUACAO_OPCOES = ["Ativa", "Inativa", "Baixada", "Suspensa"]

def map_regime(v):
    try:
        return REGIME_MAP.get(int(v), str(v))
    except Exception:
        return v

def df_to_excel_download(df: pd.DataFrame, filename: str, sheet_name: str = "dados"):
    if df is None or df.empty:
        st.warning("Nada para exportar.")
        return
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    st.download_button(
        "⬇️ Exportar Excel",
        data=buffer.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def multi_select_all(label: str, options: Iterable[str], default_all: bool = True) -> Tuple[Iterable[str], bool]:
    options = list(options)
    select_all = st.checkbox(f"Selecionar todos ({label})", value=default_all)
    sel = st.multiselect(label, options, default=options if select_all else [])
    return sel, select_all
