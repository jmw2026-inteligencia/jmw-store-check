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
    h1 { color: #ffffff !important; text-align: center; font-weight: 800; font-size: 26px !important; }
    h2 { color: #ffffff !important; text-align: center; font-size: 18px !important; margin-bottom: 20px !important; }
    .help-text { color: #e0e0e0 !important; font-size: 13px !important; font-style: italic !important; margin-bottom: 10px !important; display: block; }
    .stButton>button { background: #1c355e !important; color: white !important; font-weight: bold; border-radius: 8px; width: 100%; height: 3.5rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)
st.markdown("<h2>Sistema de Monitoreo de Precios</h2>", unsafe_allow_html=True)

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
    # Limpieza para que no falle el selectbox
    df_exp["NOMBRE_PRODUCTO"] = df_exp["NOMBRE_PRODUCTO"].astype(str)
    return df_exp.sort_values(by="NOMBRE_PRODUCTO")

df_maestro = cargar_maestro_local()

# --- TASA BCV ---
tasa_bcv = 45.50 # Ajusta si necesitas scraping en tiempo real

# --- FORMULARIO ---
if 'submitted' not in st.session_state: st.session_state['submitted'] = False

if not st.session_state['submitted']:
    with st.form("form_completo", clear_on_submit=False):
        
        # 1. EXPANDER DE DATOS BÁSICOS (RECUPERADO)
        with st.expander("👤 Persona y Datos de Control", expanded=True):
            vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
            st.markdown("<span class='help-text'>Selecciona quién realiza la auditoría.</span>", unsafe_allow_html=True)
            competencia = st.selectbox("Establecimiento", ["Competencia1", "Competencia2", "Competencia3", "Otro"])
            st.markdown("<span class='help-text'>Selecciona el local visitado.</span>", unsafe_allow_html=True)

        # 2. ESCÁNER
        with st.expander("📷 Escáner de Código"):
            st.camera_input("Enfocar")
            serial_manual = st.text_input("Código de Barras (Manual)")

        # 3. PRODUCTO CON DESCRIPCIÓN LARGA (FIX: Searchable Selectbox)
        producto = st.selectbox("Producto (Escribe para buscar descripción larga)", 
                                ["-- Seleccione --"] + df_maestro["NOMBRE_PRODUCTO"].tolist(),
                                help="Si el nombre es largo, usa este buscador.")
        
        # 4. PRECIOS
        moneda = st.radio("Moneda:", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
        precio = st.number_input("Precio Marcado", min_value=0.0, step=0.01)
        
        if moneda == "Bolívares (Bs)" and precio > 0:
            st.info(f"PRECIO PROFESIONAL: {precio:.2f} Bs | EQUIVALENTE: {(precio/tasa_bcv):.2f} $")

        # 5. SUBMIT
        if st.form_submit_button("🚀 TRANSMITIR REGISTRO"):
            if producto == "-- Seleccione --":
                st.error("❌ Debe seleccionar un producto.")
            else:
                payload = {
                    "fecha_captura": str(datetime.date.today()),
                    "vendedor": vendedor,
                    "competencia": competencia,
                    "nombre_producto": producto,
                    "precio_competencia_usd": float(round(precio if moneda == "Dólares ($)" else precio/tasa_bcv, 2))
                }
                # Tu clave de Supabase
                headers = {"apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Content-Type": "application/json"}
                res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
                
                if res.status_code in [200, 201, 204]:
                    st.session_state['submitted'] = True
                    st.rerun()
                else:
                    st.error(f"Error Supabase: {res.text}")
else:
    st.success("✅ ¡Registro enviado exitosamente!")
    if st.button("🔄 Siguiente Registro"):
        st.session_state['submitted'] = False
        st.rerun()
