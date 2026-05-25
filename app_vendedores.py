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
    h1 { font-family: 'Arial', sans-serif !important; font-size: 28px !important; font-weight: 800 !important; color: #ffffff !important; text-align: center; margin-bottom: 20px !important; }
    h2 { font-size: 18px !important; color: #ffffff !important; text-align: center; margin-bottom: 20px !important; opacity: 0.9; }
    .stButton>button { background: #1c355e !important; color: white !important; border-radius: 8px !important; height: 3.5rem !important; font-weight: bold !important; border: none !important; width: 100%; }
    .stButton>button:hover { background: #8cc63f !important; }
    </style>
""", unsafe_allow_html=True)

# TÍTULO PROFESIONAL
st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)
st.markdown("<h2>Sistema de Monitoreo de Precios</h2>", unsafe_allow_html=True)

# ==========================================
# 2. LÓGICA DE DATOS
# ==========================================
# (Mantén aquí tu función cargar_maestro_local y obtener_tasa_bcv intactas)
# ...

# ==========================================
# 3. ESTADO DE LA APLICACIÓN (PARA EL RESET)
# ==========================================
if 'form_key' not in st.session_state:
    st.session_state['form_key'] = 0

def reset_form():
    st.session_state['form_key'] += 1

# ==========================================
# 4. FORMULARIO CON KEY DINÁMICA
# ==========================================
with st.form(key=f"my_form_{st.session_state['form_key']}"):
    
    with st.expander("👤 Persona y Datos de Control"):
        vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
        competencia = st.selectbox("Establecimiento", ["Competencia1", "Competencia2", "Competencia3", "Otro"])

    st.markdown("### 📷 Captura de Código")
    img_capture = st.camera_input("Enfoca el código")
    
    # Lógica de escaneo...
    serial_input = st.text_input("Código de Barras")
    producto_sel = st.selectbox("Seleccione Producto", ["-- Seleccione --"] + df_maestro["NOMBRE_PRODUCTO"].tolist())
    precio = st.number_input("Precio", min_value=0.0, step=0.01)
    
    submit_button = st.form_submit_button(label="🚀 TRANSMITIR REGISTRO")

# ==========================================
# 5. ACCIÓN DE ENVÍO
# ==========================================
if submit_button:
    if producto_sel == "-- Seleccione --":
        st.error("❌ Debes seleccionar un producto")
    else:
        # AQUÍ TU LÓGICA DE REQUESTS.POST...
        
        # MENSAJE DE ÉXITO
        st.success("✅ Registro enviado correctamente.")
        
        # RESET AUTOMÁTICO
        reset_form()
        st.rerun()
