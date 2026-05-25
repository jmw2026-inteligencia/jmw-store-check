import os
import datetime
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import cv2
import numpy as np

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="JMW - Captura Store Check", page_icon="📸", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    .block-container { padding-top: 1.5rem !important; max-width: 500px !important; }
    h1, h2, h3, p, span, .stMarkdown { color: #ffffff !important; font-family: 'Segoe UI', sans-serif; }
    h1 { font-size: 26px !important; font-weight: 700 !important; text-align: center; margin-bottom: 0px !important; }
    h2 { font-size: 20px !important; text-align: center; margin-top: 0px !important; margin-bottom: 5px !important; }
    .stButton>button { background: linear-gradient(90deg, #1c355e, #8cc63f) !important; color: white !important;
        border-radius: 10px !important; height: 3.8rem !important; font-size: 18px !important;
        font-weight: bold !important; border: none !important; box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important; margin-top: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CREDENCIALES
# ==========================================
SUPABASE_URL = "https://ofpqnoinvpumkfifiera.supabase.co"
SUPABASE_KEY = "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL"

# ==========================================
# 3. DATA MAESTRA
# ==========================================
@st.cache_data(ttl=1800)
def cargar_maestro_local():
    ruta_excel = "IMPORTACION_ANALISIS_PRECIO.xlsx"
    if not os.path.exists(ruta_excel): return pd.DataFrame()
    df_productos = pd.read_excel(ruta_excel, sheet_name="PRODUCTOS")
    df_catalogo = pd.read_excel(ruta_excel, sheet_name="CATALOGO_PRODUCTOS")
    df_categoria = pd.read_excel(ruta_excel, sheet_name="CATEGORIA")
    df_productos.columns = df_productos.columns.str.lower()
    df_catalogo.columns = df_catalogo.columns.str.lower()
    df_categoria.columns = df_categoria.columns.str.lower()
    df_prod_filtrado = df_productos[(df_productos["activo"] == -1) & (df_productos["destacado"] == -1)].copy()
    df_prod_filtrado["serial"] = df_prod_filtrado["serial"].astype(str).str.strip()
    df_catalogo["serial"] = df_catalogo["serial"].astype(str).str.strip()
    df_combinado_1 = pd.merge(df_prod_filtrado[["serial", "nombre", "categoria_id"]], df_categoria[["id", "segmento1"]], left_on="categoria_id", right_on="id", how="left")
    df_maestro_final = pd.merge(df_combinado_1, df_catalogo[["serial", "proveedor", "rubro", "sub_categoria"]], on="serial", how="left")
    df_exportar = df_maestro_final[["serial", "nombre", "segmento1", "proveedor", "rubro", "sub_categoria"]].copy()
    df_exportar = df_exportar.fillna("SIN DATA")
    df_exportar.columns = ["SERIAL", "NOMBRE_PRODUCTO", "SEGMENTO", "PROVEEDOR", "RUBRO", "SUB_CATEGORIA"]
    df_exportar["NOMBRE_PRODUCTO"] = df_exportar["NOMBRE_PRODUCTO"].astype(str).str.strip()
    return df_exportar.sort_values(by="NOMBRE_PRODUCTO").reset_index(drop=True)

df_maestro = cargar_maestro_local()

# ==========================================
# 4. TASA BCV
# ==========================================
@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        response = requests.get("https://www.bcv.org.ve/", headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        tasa_element = soup.find(id="dolar")
        return float(tasa_element.find('strong').text.strip().replace(',', '.'))
    except: return 45.50

tasa_bcv = obtener_tasa_bcv()

st.markdown("<h1>JMW CASA DE REPRESENTACIONES</h1>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align: center;'>Tasa Oficial: <b>{tasa_bcv:.2f} Bs/$</b></div>", unsafe_allow_html=True)

# ==========================================
# 5. CAMPOS Y ESCÁNER
# ==========================================
vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
competencia = st.selectbox("Establecimiento", ["Competencia1", "Competencia2", "Competencia3", "Otro"])

st.markdown("### 📷 Captura")
img_capture = st.camera_input("Enfoca el código")
serial_detectado = ""

if img_capture:
    try:
        file_bytes = np.asarray(bytearray(img_capture.read()), dtype=np.uint8)
        opencv_image = cv2.imdecode(file_bytes, 1)
        detector = cv2.barcode.BarcodeDetector()
        ok, decoded_info, _, _ = detector.detectAndDecode(opencv_image)
        if ok and decoded_info:
            serial_detectado = decoded_info[0]
            st.success(f"✅ Identificado: {serial_detectado}")
    except: st.warning("Error en cámara, usa el campo manual.")

serial_final = st.text_input("Código de Barras", value=serial_detectado)
producto_seleccionado = st.selectbox("Seleccione Producto", ["-- Seleccione --"] + df_maestro["NOMBRE_PRODUCTO"].tolist())
moneda = st.radio("Moneda", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)

precio_bruto = st.number_input("Precio Marcado", min_value=0.0, step=0.01)
precio_calculado_usd = precio_bruto if moneda == "Dólares ($)" else (precio_bruto / tasa_bcv)

# ==========================================
# 6. TRANSMITIR
# ==========================================
if st.button("🚀 TRANSMITIR REGISTRO"):
    if producto_seleccionado == "-- Seleccione --":
        st.error("¡Seleccione un producto!")
    else:
        info_prod = df_maestro[df_maestro["NOMBRE_PRODUCTO"] == producto_seleccionado].iloc[0]
        payload = {
            "fecha_captura": str(datetime.date.today()),
            "vendedor": vendedor,
            "competencia": competencia,
            "serial_escaneado": str(info_prod["SERIAL"]),
            "nombre_producto": str(info_prod["NOMBRE_PRODUCTO"]),
            "precio_competencia_usd": float(round(precio_calculado_usd, 2))
        }
        res = requests.post(f"{SUPABASE_URL}/rest/v1/store_check", headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/json"}, json=payload)
        
        if res.status_code in [200, 201, 204]:
            st.success("✅ ¡Registro Exitoso!")
            if st.button("🔄 Cargar Siguiente"): st.rerun()
        else:
            st.error(f"❌ Error: {res.text}")
