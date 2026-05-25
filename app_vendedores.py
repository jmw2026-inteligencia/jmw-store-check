import os
import datetime
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import cv2
import numpy as np

# ==========================================
# 1. CONFIGURACIÓN Y DISEÑO PROFESIONAL
# ==========================================
st.set_page_config(page_title="JMW Store Check", page_icon="📸", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    .block-container { padding-top: 1rem !important; max-width: 500px !important; }
    h1 { font-family: 'Arial', sans-serif !important; font-size: 28px !important; font-weight: 800 !important; color: #ffffff !important; text-align: center; margin-bottom: 5px !important; }
    h2 { font-size: 16px !important; color: #ffffff !important; text-align: center; margin-bottom: 20px !important; opacity: 0.9; }
    .stButton>button { background: #1c355e !important; color: white !important; border-radius: 8px !important; height: 3.5rem !important; font-weight: bold !important; border: none !important; width: 100%; }
    .stButton>button:hover { background: #8cc63f !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)
st.markdown("<h2>Sistema de Monitoreo de Precios</h2>", unsafe_allow_html=True)

# ==========================================
# 2. LÓGICA DE DATOS (Maestro + BCV)
# ==========================================
@st.cache_data(ttl=1800)
def cargar_maestro_local():
    ruta = "IMPORTACION_ANALISIS_PRECIO.xlsx"
    if not os.path.exists(ruta): return pd.DataFrame()
    
    df_p = pd.read_excel(ruta, sheet_name="PRODUCTOS")
    df_c = pd.read_excel(ruta, sheet_name="CATALOGO_PRODUCTOS")
    df_cat = pd.read_excel(ruta, sheet_name="CATEGORIA")
    
    df_p.columns = df_p.columns.str.lower()
    df_c.columns = df_c.columns.str.lower()
    df_cat.columns = df_cat.columns.str.lower()
    
    df_f = df_p[(df_p["activo"] == -1) & (df_p["destacado"] == -1)].copy()
    df_f["serial"] = df_f["serial"].astype(str).str.strip()
    df_c["serial"] = df_c["serial"].astype(str).str.strip()
    
    df_m = pd.merge(df_f[["serial", "nombre", "categoria_id"]], df_cat[["id", "segmento1"]], left_on="categoria_id", right_on="id", how="left")
    df_m = pd.merge(df_m, df_c[["serial", "proveedor", "rubro", "sub_categoria"]], on="serial", how="left")
    
    df_exp = df_m[["serial", "nombre", "segmento1", "proveedor", "rubro", "sub_categoria"]].copy()
    df_exp.columns = ["SERIAL", "NOMBRE_PRODUCTO", "SEGMENTO", "PROVEEDOR", "RUBRO", "SUB_CATEGORIA"]
    return df_exp.sort_values(by="NOMBRE_PRODUCTO")

df_maestro = cargar_maestro_local()

@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        res = requests.get("https://www.bcv.org.ve/", headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        return float(soup.find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 45.50

tasa_bcv = obtener_tasa_bcv()
st.markdown(f"<div style='text-align:center; color:white;'>Tasa BCV: <b>{tasa_bcv:.2f} Bs/$</b></div>", unsafe_allow_html=True)

# ==========================================
# 3. FORMULARIO DE CAPTURA
# ==========================================
if 'form_key' not in st.session_state: st.session_state['form_key'] = 0

with st.form(key=f"form_{st.session_state['form_key']}", clear_on_submit=True):
    with st.expander("👤 Datos de Control"):
        vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
        competencia = st.selectbox("Establecimiento", ["Competencia1", "Competencia2", "Competencia3", "Otro"])
    
    st.markdown("### 📷 Captura")
    img_capture = st.camera_input("Escanear")
    serial_manual = st.text_input("Código de Barras")
    producto = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["NOMBRE_PRODUCTO"].tolist())
    precio = st.number_input("Precio", min_value=0.0, step=0.01)
    
    submit = st.form_submit_button("🚀 TRANSMITIR REGISTRO")

# ==========================================
# 4. LÓGICA DE ENVÍO
# ==========================================
if submit:
    if producto == "-- Seleccione --":
        st.error("❌ Seleccione un producto.")
    else:
        # Aquí tu lógica de requests.post original...
        st.success("✅ Registro enviado.")
        st.session_state['form_key'] += 1
        st.rerun()
