import os
import datetime
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import cv2
import numpy as np

# --- CONFIGURACIÓN E IDENTIDAD (Estilos JMW) ---
st.set_page_config(page_title="JMW Store Check", page_icon="📸", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    h1 { color: #ffffff !important; font-size: 26px !important; font-weight: 700 !important; text-align: center; }
    h2 { color: #ffffff !important; font-size: 20px !important; text-align: center; margin-bottom: 20px !important; }
    .help-text { color: #e0e0e0 !important; font-size: 13px !important; font-style: italic !important; margin-bottom: 15px !important; display: block; }
    .stButton>button { background: #1c355e !important; color: white !important; font-weight: bold; border-radius: 8px !important; height: 3.5rem !important; width: 100%; border: none !important; }
    .info-box { background-color: #1c355e !important; color: #ffffff !important; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)
st.markdown("<h2>Sistema de Monitoreo de Precios</h2>", unsafe_allow_html=True)

# --- CARGA DE DATOS (Manteniendo tu estructura) ---
@st.cache_data(ttl=1800)
def cargar_maestro_local():
    # Asegúrate que la ruta sea correcta según tu sistema
    ruta_excel = "IMPORTACION_ANALISIS_PRECIO.xlsx"
    if not os.path.exists(ruta_excel): return pd.DataFrame()
    
    df_p = pd.read_excel(ruta_excel, sheet_name="PRODUCTOS")
    df_c = pd.read_excel(ruta_excel, sheet_name="CATALOGO_PRODUCTOS")
    df_cat = pd.read_excel(ruta_excel, sheet_name="CATEGORIA")
    
    df_p.columns = df_p.columns.str.lower()
    df_c.columns = df_c.columns.str.lower()
    df_cat.columns = df_cat.columns.str.lower()
    
    df_f = df_p[(df_p["activo"] == -1) & (df_p["destacado"] == -1)].copy()
    df_f["serial"] = df_f["serial"].astype(str).str.strip()
    
    df_m = pd.merge(df_f[["serial", "nombre", "categoria_id"]], df_cat[["id", "segmento1"]], left_on="categoria_id", right_on="id", how="left")
    df_m = pd.merge(df_m, df_c[["serial", "proveedor", "rubro", "sub_categoria"]], on="serial", how="left")
    
    df_exp = df_m[["serial", "nombre", "segmento1", "proveedor", "rubro", "sub_categoria"]].copy()
    df_exp.columns = ["SERIAL", "NOMBRE_PRODUCTO", "SEGMENTO", "PROVEEDOR", "RUBRO", "SUB_CATEGORIA"]
    return df_exp.sort_values(by="NOMBRE_PRODUCTO").reset_index(drop=True)

df_maestro = cargar_maestro_local()

# --- TASA BCV ---
@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        res = requests.get("https://www.bcv.org.ve/", headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=5)
        return float(BeautifulSoup(res.text, 'html.parser').find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 45.50

tasa_bcv = obtener_tasa_bcv()
st.markdown(f"<div class='info-box'>Tasa BCV de Referencia: {tasa_bcv:.2f} Bs/$</div>", unsafe_allow_html=True)

# --- FORMULARIO CON SESSION STATE ---
if 'submitted' not in st.session_state: st.session_state['submitted'] = False

if not st.session_state['submitted']:
    with st.expander("👤 Persona y Datos de Control", expanded=True):
        vendedor = st.selectbox("Selecciona Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
        st.markdown("<span class='help-text'>Identifícate para registrar la autoría.</span>", unsafe_allow_html=True)
        competencia = st.selectbox("Establecimiento Competidor", ["Competencia1", "Competencia2", "Competencia3", "Otro"])
        st.markdown("<span class='help-text'>Cadena o farmacia auditada.</span>", unsafe_allow_html=True)

    with st.expander("📷 Escáner de Código"):
        img = st.camera_input("Enfoca el producto")
        serial = st.text_input("Código de Barras (Manual/Escaneado)")
        st.markdown("<span class='help-text'>Si no detecta, escribe el serial aquí.</span>", unsafe_allow_html=True)

    producto = st.selectbox("Seleccione Producto", ["-- Seleccione --"] + df_maestro["NOMBRE_PRODUCTO"].tolist())
    
    moneda = st.radio("¿Moneda en anaquel?", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
    precio = st.number_input("Precio Marcado", min_value=0.0, step=0.01)
    
    if moneda == "Bolívares (Bs)" and precio > 0:
        st.markdown(f"<div style='background:#ffffff; color:#1c355e; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>PRECIO EN BOLÍVARES: {precio:.2f} Bs | EQUIVALENTE: {(precio/tasa_bcv):.2f} $</div>", unsafe_allow_html=True)
    elif moneda == "Dólares ($)" and precio > 0:
        st.markdown(f"<div style='background:#ffffff; color:#1c355e; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>PRECIO MARCADO: {precio:.2f} $</div>", unsafe_allow_html=True)

    foto_file = st.file_uploader("🖼️ Foto para entrenamiento (IA)", type=["jpg", "png"])
    
    if st.button("🚀 TRANSMITIR REGISTRO"):
        if producto == "-- Seleccione --":
            st.error("❌ Error: Debes seleccionar un producto.")
        else:
            # Aquí va tu lógica de POST a Supabase...
            st.session_state['submitted'] = True
            st.rerun()

else:
    st.success("✅ ¡REGISTRO EXITOSO!")
    if st.button("🔄 Siguiente Registro"):
        st.session_state['submitted'] = False
        st.rerun()
