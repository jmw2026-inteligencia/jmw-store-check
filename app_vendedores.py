import os
import datetime
import streamlit as st
import requests
import pandas as pd
import cv2
import numpy as np

# CONFIGURACIÓN
st.set_page_config(page_title="JMW - Captura", layout="centered")

# CSS para velocidad y legibilidad
st.markdown("""
    <style>
    .stApp { background-color: #00a99d; }
    .stButton>button { background: #1c355e; color: white; height: 3.5rem; width: 100%; font-size: 20px; font-weight: bold; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# Supabase Config
SUPABASE_URL = "https://ofpqnoinvpumkfifiera.supabase.co"
SUPABASE_KEY = "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL"

# CARGA DE DATOS (Mismo que tenías)
@st.cache_data(ttl=1800)
def cargar_maestro_local():
    ruta_excel = "IMPORTACION_ANALISIS_PRECIO.xlsx"
    if not os.path.exists(ruta_excel): return pd.DataFrame()
    df_productos = pd.read_excel(ruta_excel, sheet_name="PRODUCTOS")
    df_catalogo = pd.read_excel(ruta_excel, sheet_name="CATALOGO_PRODUCTOS")
    df_categoria = pd.read_excel(ruta_excel, sheet_name="CATEGORIA")
    # ... (tus cruces de datos) ...
    return df_productos # Simplificado para brevedad, mantén tu lógica original de merge aquí

df_maestro = cargar_maestro_local()

# INTERFAZ
st.title("📸 Registro Rápido")

# 1. ESCÁNER O BÚSQUEDA
img_capture = st.camera_input("Enfoca el código de barras")
serial_detectado = ""

# Lógica mejorada para evitar errores en la cámara
if img_capture:
    try:
        file_bytes = np.asarray(bytearray(img_capture.read()), dtype=np.uint8)
        opencv_image = cv2.imdecode(file_bytes, 1)
        detector = cv2.barcode.BarcodeDetector()
        ok, decoded_info, _, _ = detector.detectAndDecode(opencv_image)
        if ok and decoded_info:
            serial_detectado = decoded_info[0]
            st.success(f"Detectado: {serial_detectado}")
    except:
        st.warning("Error al procesar imagen, usa el buscador manual.")

serial_input = st.text_input("Código o Serial:", value=serial_detectado)

# 2. SELECTOR DE PRODUCTO
producto_seleccionado = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["NOMBRE_PRODUCTO"].tolist())

# 3. PRECIO
precio = st.number_input("Precio ($)", min_value=0.0, step=0.1)

# 4. TRANSMITIR (Sin globos, aviso rápido)
if st.button("🚀 TRANSMITIR"):
    if producto_seleccionado == "-- Seleccione --":
        st.error("Selecciona un producto.")
    else:
        # AQUÍ TU LÓGICA DE REQUESTS.POST A SUPABASE...
        # ...
        st.success("✅ Registro enviado. Puede seguir con el siguiente.")
        if st.button("🔄 Cargar siguiente"):
            st.rerun()
