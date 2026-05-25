import os
import datetime
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import cv2
import numpy as np

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO (TODO EN AZUL Y BLANCO)
# ==========================================
st.set_page_config(page_title="JMW Store Check", page_icon="📸", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    .block-container { max-width: 500px !important; }
    h1 { color: #ffffff !important; text-align: center; font-weight: 800; }
    h2 { color: #ffffff !important; text-align: center; font-size: 16px; margin-bottom: 20px; }
    label { color: #ffffff !important; font-weight: 600 !important; }
    .stSelectbox>div>div, .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #1c355e !important; color: #ffffff !important; border: 1px solid #ffffff !important;
    }
    .help-text { color: #e0e0e0 !important; font-size: 12px !important; font-style: italic !important; margin-bottom: 10px !important; }
    .stButton>button { background: #1c355e !important; color: white !important; font-weight: bold; border-radius: 8px; width: 100%; height: 3.5rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)
st.markdown("<h2>Sistema Profesional de Monitoreo de Precios</h2>", unsafe_allow_html=True)

# (MANTÉN TUS FUNCIONES cargar_maestro_local() y obtener_tasa_bcv() AQUÍ)
tasa_bcv = obtener_tasa_bcv()
st.markdown(f"<div style='text-align:center; color:white; background:rgba(0,0,0,0.1); padding:10px; border-radius:8px;'>Tasa BCV Referencia: <b>{tasa_bcv:.2f} Bs/$</b></div>", unsafe_allow_html=True)

# ==========================================
# 2. FORMULARIO CON LÓGICA COMPLETA
# ==========================================
if 'form_key' not in st.session_state: st.session_state['form_key'] = 0

with st.form(key=f"form_{st.session_state['form_key']}", clear_on_submit=True):
    with st.expander("👤 Persona y Datos de Control", expanded=True):
        vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
        st.markdown("<span class='help-text'>Identifícate para registrar la autoría de la captura.</span>", unsafe_allow_html=True)
        competencia = st.selectbox("Establecimiento Competidor", ["Competencia1", "Competencia2", "Competencia3", "Otro"])
        st.markdown("<span class='help-text'>Selecciona el local que estás auditando.</span>", unsafe_allow_html=True)

    with st.expander("📷 Escáner de Código (Opcional)"):
        img_capture = st.camera_input("Enfoca las barras")
        serial_manual = st.text_input("Código de Barras")
        st.markdown("<span class='help-text'>Si el escáner falla, ingresa el serial manualmente.</span>", unsafe_allow_html=True)

    producto = st.selectbox("Seleccione Producto", ["-- Seleccione --"] + df_maestro["NOMBRE_PRODUCTO"].tolist())
    
    moneda = st.radio("Moneda visible en anaquel:", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
    precio_valor = st.number_input("Precio Marcado", min_value=0.0, step=0.01)
    
    if moneda == "Bolívares (Bs)" and precio_valor > 0:
        st.info(f"📊 Conversión profesional: {(precio_valor/tasa_bcv):.2f} $ al cambio BCV.")
    
    foto_file = st.file_uploader("🖼️ Evidencia fotográfica (Entrenamiento IA)", type=["jpg", "jpeg", "png"])
    st.markdown("<span class='help-text'>Toma una foto clara del producto y su precio.</span>", unsafe_allow_html=True)
    
    submit = st.form_submit_button("🚀 TRANSMITIR REGISTRO")

# ==========================================
# 3. LÓGICA DE PROCESAMIENTO
# ==========================================
if submit:
    if producto == "-- Seleccione --":
        st.error("❌ Error: Debe seleccionar un producto.")
    else:
        # Lógica de envío igual a la tuya...
        st.success("✅ Registro enviado con éxito.")
        st.session_state['form_key'] += 1
        st.rerun()
