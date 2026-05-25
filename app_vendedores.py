import os
import datetime
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# --- CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="JMW Store Check", page_icon="📸", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    h1 { color: #ffffff !important; text-align: center; font-weight: 800; }
    .stSelectbox>div>div { background-color: #1c355e !important; color: white !important; }
    .stTextInput>div>div>input { background-color: #1c355e !important; color: white !important; }
    .stNumberInput>div>div>input { background-color: #1c355e !important; color: white !important; }
    .stButton>button { background: #1c355e !important; color: white !important; font-weight: bold; border-radius: 8px; width: 100%; height: 3.5rem; }
    .info-msg { background: #1c355e; color: white; padding: 10px; border-radius: 5px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=1800)
def cargar_maestro_local():
    ruta_excel = "IMPORTACION_ANALISIS_PRECIO.xlsx"
    if not os.path.exists(ruta_excel): return pd.DataFrame()
    df_p = pd.read_excel(ruta_excel, sheet_name="PRODUCTOS")
    df_c = pd.read_excel(ruta_excel, sheet_name="CATALOGO_PRODUCTOS")
    df_cat = pd.read_excel(ruta_excel, sheet_name="CATEGORIA")
    df_p.columns = df_p.columns.str.lower()
    df_c.columns = df_c.columns.str.lower()
    df_cat.columns = df_cat.columns.str.lower()
    df_f = df_p[(df_p["activo"] == -1) & (df_p["destacado"] == -1)].copy()
    df_m = pd.merge(df_f[["serial", "nombre", "categoria_id"]], df_cat[["id", "segmento1"]], left_on="categoria_id", right_on="id", how="left")
    df_m = pd.merge(df_m, df_c[["serial", "proveedor", "rubro", "sub_categoria"]], on="serial", how="left")
    df_exp = df_m[["serial", "nombre", "segmento1", "proveedor", "rubro", "sub_categoria"]].copy()
    df_exp.columns = ["SERIAL", "NOMBRE_PRODUCTO", "SEGMENTO", "PROVEEDOR", "RUBRO", "SUB_CATEGORIA"]
    return df_exp.sort_values(by="NOMBRE_PRODUCTO")

df_maestro = cargar_maestro_local()

# --- LÓGICA BCV ---
@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        res = requests.get("https://www.bcv.org.ve/", headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=5)
        return float(BeautifulSoup(res.text, 'html.parser').find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 45.50

tasa_bcv = obtener_tasa_bcv()

# --- INTERFAZ ---
st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)

if 'submitted' not in st.session_state: st.session_state['submitted'] = False

if not st.session_state['submitted']:
    with st.form("form_registro", clear_on_submit=False):
        vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
        competencia = st.selectbox("Establecimiento", ["Competencia1", "Competencia2", "Competencia3", "Otro"])
        
        # Filtro con búsqueda (el selectbox de Streamlit permite buscar)
        producto = st.selectbox("Producto (Escribe para buscar)", ["-- Seleccione --"] + df_maestro["NOMBRE_PRODUCTO"].tolist())
        
        moneda = st.radio("Moneda:", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
        precio = st.number_input("Precio Marcado", min_value=0.0, step=0.01)
        
        if moneda == "Bolívares (Bs)" and precio > 0:
            st.markdown(f"<div class='info-msg'>Precio: {precio:.2f} Bs (Eq: {(precio/tasa_bcv):.2f} $)</div>", unsafe_allow_html=True)

        if st.form_submit_button("🚀 TRANSMITIR REGISTRO"):
            if producto == "-- Seleccione --":
                st.error("Seleccione un producto.")
            else:
                # Lógica de envío
                payload = {
                    "fecha_captura": str(datetime.date.today()),
                    "vendedor": vendedor,
                    "competencia": competencia,
                    "nombre_producto": producto,
                    "precio_competencia_usd": float(round(precio if moneda == "Dólares ($)" else precio/tasa_bcv, 2))
                }
                res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", 
                                    headers={"apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Content-Type": "application/json"},
                                    json=payload)
                if res.status_code in [200, 201]:
                    st.session_state['submitted'] = True
                    st.rerun()
                else:
                    st.error(f"Error: {res.text}")
else:
    st.success("✅ ¡Registro Exitoso!")
    if st.button("🔄 Siguiente Registro"):
        st.session_state['submitted'] = False
        st.rerun()
