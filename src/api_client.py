from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from datetime import date, datetime
import requests
import streamlit as st

API_BASE = "https://api.acessorias.com"

def _get_token() -> str:
    token = ""
    try:
        token = st.secrets.get("ACESSORIAS_TOKEN", "")
    except Exception:
        pass
    if not token:
        token = os.getenv("ACESSORIAS_TOKEN", "")
    return token

def _headers(token: Optional[str] = None) -> Dict[str, str]:
    token = token or _get_token()
    return {"Authorization": f"Bearer {token}"} if token else {}

def _paged_get(url: str, headers: Dict[str, str], params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    aggregated: List[Dict[str, Any]] = []
    page = 1
    while True:
        q = dict(params or {})
        q["Pagina"] = page
        r = requests.get(url, headers=headers, params=q, timeout=60)
        if r.status_code == 204:
            break
        r.raise_for_status()
        payload = r.json()
        if isinstance(payload, dict):
            aggregated.append(payload)
            break
        if not payload:
            break
        aggregated.extend(payload)
        page += 1
    return aggregated

@st.cache_data(show_spinner=False)
def deliveries_list(token: str, identificador: str, dt_ini: date, dt_fim: date,
                    dt_lastdh: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Retorna a estrutura:
    [
      { "ID": ..., "Identificador": "...", "Razao": "...", "Entregas": [ {...}, ... ] },
      ...
    ]
    Use identificador="ListAll" para todas as empresas.
    """
    params: Dict[str, Any] = {
        "DtInitial": dt_ini.strftime("%Y-%m-%d"),
        "DtFinal": dt_fim.strftime("%Y-%m-%d"),
    }
    if dt_lastdh:
        params["DtLastDH"] = dt_lastdh.strftime("%Y-%m-%d %H:%M:%S")
    url = f"{API_BASE}/deliveries/{identificador}"
    return _paged_get(url, _headers(token), params)

@st.cache_data(show_spinner=False)
def processes_list(token: str, proc_id_like: str = "*", nome: Optional[str] = None,
                   inicio_ini: Optional[date] = None, inicio_fim: Optional[date] = None,
                   concl_ini: Optional[date] = None, concl_fim: Optional[date] = None,
                   status_letra: Optional[str] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if nome: params["ProcNome"] = nome
    if inicio_ini: params["ProcInicioIni"] = inicio_ini.strftime("%Y-%m-%d")
    if inicio_fim: params["ProcInicioFim"] = inicio_fim.strftime("%Y-%m-%d")
    if concl_ini: params["ProcConclusaoIni"] = concl_ini.strftime("%Y-%m-%d")
    if concl_fim: params["ProcConclusaoFim"] = concl_fim.strftime("%Y-%m-%d")
    if status_letra: params["Status"] = status_letra
    url = f"{API_BASE}/processes/{proc_id_like}"
    return _paged_get(url, _headers(token), params)

@st.cache_data(show_spinner=False)
def company_detail(token: str, identificador: str, incluir_obrigacoes: bool = False) -> Optional[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if incluir_obrigacoes:
        params["obligations"] = ""
    url = f"{API_BASE}/companies/{identificador}"
    r = requests.get(url, headers=_headers(token), params=params, timeout=60)
    if r.status_code == 204:
        return None
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner=False)
def companies_from_deliveries(token: str, dt_ini: date, dt_fim: date) -> List[Dict[str, Any]]:
    """
    Fallback para compor catálogo de empresas a partir das entregas (quando a API
    não expõe um endpoint de listagem geral de companies).
    """
    data = deliveries_list(token, "ListAll", dt_ini, dt_fim)
    rows: Dict[str, Dict[str, Any]] = {}
    for emp in data:
        key = emp.get("Identificador")
        if key not in rows:
            rows[key] = {
                "Identificador": key,
                "Razao": emp.get("Razao"),
                "ID": emp.get("ID"),
            }
    return list(rows.values())
