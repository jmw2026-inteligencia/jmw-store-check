import os
import datetime
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import cv2
import numpy as np

# 1. Configuración de página
st.set_page_config(page_title="JMW Store Check", page_icon="📸", layout="centered")

# CSS Profesional: Fondo JMW, etiquetas blancas, inputs azules
st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    h1 { color: #ffffff !important; text-align: center; font-weight: 800; }
    h2 { color: #ffffff !important; text-align: center; font-size: 16px; margin-bottom: 20px; }
    label { color: #ffffff !important; font-weight: 600 !important; }
    .stSelectbox>div>div, .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #1c355e !important; color: #ffffff !important; border: 1px solid #ffffff !important;
    }
    .help-text { color: #e0e0e0 !important; font-size: 12px !important; font-style: italic !important; margin-bottom: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# 2. Funciones Lógica (Data y BCV)
@st.cache_data(ttl=1800)
def cargar_maestro_local():
    ruta = "IMPORTACION_ANALISIS_PRECIO.xlsx"
    if not os.path.exists(ruta): return pd.DataFrame()
    df_p = pd.read_excel(ruta, sheet_name="PRODUCTOS")
    df_c = pd.read_excel(ruta, sheet_name="CATALOGO_PRODUCTOS")
    df_cat = pd.read_excel(ruta, sheet_name="CATEGORIA")
    # Limpieza básica
    df_p.columns = df_p.columns.str.lower()
    df_c.columns = df_c.columns.str.lower()
    df_cat.columns = df_cat.columns.str.lower()
    # Tu cruce lógico
    df_f = df_p[(df_p["activo"] == -1) & (df_p["destacado"] == -1)].copy()
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
        return float(BeautifulSoup(res.text, 'html.parser').find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 45.50

tasa_bcv = obtener_tasa_bcv()

# 3. Interfaz
st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)
st.markdown(f"<h2>Tasa BCV Referencia: {tasa_bcv:.2f} Bs/$</h2>", unsafe_allow_html=True)

if 'form_key' not in st.session_state: st.session_state['form_key'] = 0

with st.form(key=f"form_{st.session_state['form_key']}", clear_on_submit=True):
    with st.expander("👤 Datos de Control"):
        vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
        competencia = st.selectbox("Establecimiento", ["Competencia1", "Competencia2", "Competencia3", "Otro"])
    
    with st.expander("📷 Escáner (Opcional)"):
        img = st.camera_input("Enfocar")
        serial = st.text_input("Código")
    
    producto = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["NOMBRE_PRODUCTO"].tolist())
    moneda = st.radio("Moneda:", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
    precio = st.number_input("Precio", min_value=0.0, step=0.01)
    
    if moneda == "Bolívares (Bs)" and precio > 0:
        st.info(f"Conversión: {(precio/tasa_bcv):.2f} $")
        
    foto = st.file_uploader("Foto Entrenamiento", type=["jpg", "png"])
    submit = st.form_submit_button("🚀 TRANSMITIR REGISTRO")

# 4. Lógica de Envío
if submit:
    if producto == "-- Seleccione --":
        st.error("Seleccione un producto.")
    else:
        # Aquí va tu lógica de Supabase (requests.post)
        st.success("✅ Registro enviado.")
        st.session_state['form_key'] += 1
        st.rerun()
