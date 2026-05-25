import os
import datetime
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import cv2
import numpy as np

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO PROFESIONAL
# ==========================================
st.set_page_config(page_title="JMW Store Check", page_icon="📸", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    .block-container { padding-top: 1rem !important; max-width: 500px !important; }
    h1 { font-family: 'Segoe UI', sans-serif !important; font-size: 28px !important; font-weight: 700 !important; color: #ffffff !important; text-align: center; }
    h2 { font-size: 16px !important; color: #ffffff !important; text-align: center; margin-bottom: 20px !important; }
    .stButton>button { background: linear-gradient(90deg, #1c355e, #8cc63f) !important; color: white !important;
        border-radius: 10px !important; height: 3.5rem !important; font-weight: bold !important; width: 100%; border: none !important; }
    .help-text { color: #e0e0e0 !important; font-size: 12px !important; font-style: italic !important; margin-bottom: 10px !important; display: block; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)
st.markdown("<h2>Sistema de Monitoreo de Precios</h2>", unsafe_allow_html=True)

SUPABASE_URL = "https://ofpqnoinvpumkfifiera.supabase.co"
SUPABASE_KEY = "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL"

# ==========================================
# 2. CARGA DE DATOS Y BCV
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
    return df_exp.sort_values(by="NOMBRE_PRODUCTO").reset_index(drop=True)

df_maestro = cargar_maestro_local()

@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        res = requests.get("https://www.bcv.org.ve/", headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=5)
        return float(BeautifulSoup(res.text, 'html.parser').find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 45.50

tasa_bcv = obtener_tasa_bcv()
st.markdown(f"<div style='text-align:center; color:white;'>Tasa BCV: <b>{tasa_bcv:.2f} Bs/$</b></div>", unsafe_allow_html=True)

# ==========================================
# 3. FORMULARIO COMPLETO
# ==========================================
if 'form_key' not in st.session_state: st.session_state['form_key'] = 0

with st.form(key=f"form_{st.session_state['form_key']}", clear_on_submit=True):
    with st.expander("👤 Persona y Datos de Control"):
        vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
        competencia = st.selectbox("Establecimiento", ["Competencia1", "Competencia2", "Competencia3", "Otro"])

    with st.expander("📷 Escáner de Código (Opcional)"):
        img_capture = st.camera_input("Enfocar")
        serial_manual = st.text_input("Código de Barras (Manual)", value="")
        st.markdown("<span class='help-text'>Si usas la cámara, el código aparecerá aquí arriba.</span>", unsafe_allow_html=True)

    producto = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["NOMBRE_PRODUCTO"].tolist())
    moneda = st.radio("Moneda", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
    precio_valor = st.number_input("Precio Marcado", min_value=0.0, step=0.01)
    foto_file = st.file_uploader("🖼️ Foto para entrenamiento", type=["jpg", "jpeg", "png"])
    
    submit = st.form_submit_button("🚀 TRANSMITIR REGISTRO")

# ==========================================
# 4. LÓGICA DE PROCESAMIENTO Y ENVÍO
# ==========================================
if submit:
    if producto == "-- Seleccione --":
        st.error("❌ Seleccione un producto.")
    else:
        # Lógica de conversión
        precio_final_usd = precio_valor if moneda == "Dólares ($)" else (precio_valor / tasa_bcv)
        
        # Payload completo
        info_prod = df_maestro[df_maestro["NOMBRE_PRODUCTO"] == producto].iloc[0]
        payload = {
            "fecha_captura": str(datetime.date.today()),
            "vendedor": vendedor,
            "competencia": competencia,
            "serial_escaneado": serial_manual if serial_manual else str(info_prod["SERIAL"]),
            "nombre_producto": producto,
            "precio_competencia_usd": float(round(precio_final_usd, 2))
        }
        
        # Envío a Supabase
        headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/json"}
        res = requests.post(f"{SUPABASE_URL}/rest/v1/store_check", headers=headers, json=payload)
        
        if res.status_code in [200, 201, 204]:
            st.success("✅ ¡Registro enviado!")
            st.session_state['form_key'] += 1
            st.rerun()
        else:
            st.error(f"❌ Error en base de datos: {res.text}")
