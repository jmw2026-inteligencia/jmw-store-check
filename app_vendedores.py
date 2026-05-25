import os
import datetime
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# --- CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="JMW Store Check", page_icon="📸", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    h1 { color: #ffffff !important; text-align: center; font-weight: 800; font-size: 28px !important; }
    h2 { color: #ffffff !important; text-align: center; font-size: 18px !important; margin-bottom: 20px !important; }
    .help-text { color: #e0e0e0 !important; font-size: 13px !important; font-style: italic !important; margin-bottom: 10px !important; }
    .stButton>button { background: #1c355e !important; color: white !important; font-weight: bold; border-radius: 8px; width: 100%; height: 3.5rem; }
    .info-msg { background: #1c355e; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)
st.markdown("<h2>Sistema de Monitoreo de Precios</h2>", unsafe_allow_html=True)

# --- DATOS ---
@st.cache_data(ttl=1800)
def cargar_maestro_local():
    # Asegúrate que el archivo esté en la misma carpeta
    return pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")

df_maestro = cargar_maestro_local()
tasa_bcv = 45.50 # Ajusta si necesitas scraping en tiempo real

# --- FORMULARIO ---
if 'submitted' not in st.session_state: st.session_state['submitted'] = False

if not st.session_state['submitted']:
    with st.form("form_final", clear_on_submit=False):
        
        # 1. EXPANDER DE CONTROL
        with st.expander("👤 Persona y Datos de Control", expanded=True):
            vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
            st.markdown("<span class='help-text'>Identifícate para registrar la autoría de la captura.</span>", unsafe_allow_html=True)
            competencia = st.selectbox("Establecimiento", ["Competencia1", "Competencia2", "Competencia3", "Otro"])
            st.markdown("<span class='help-text'>Selecciona el local que estás auditando.</span>", unsafe_allow_html=True)

        # 2. EXPANDER DE ESCÁNER
        with st.expander("📷 Escáner de Código"):
            st.camera_input("Enfocar")
            serial = st.text_input("Código de Barras (Manual/Escaneado)")
            st.markdown("<span class='help-text'>Ingresa el serial si la cámara no lo detecta.</span>", unsafe_allow_html=True)

        # 3. PRODUCTO
        producto = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist())
        st.markdown("<span class='help-text'>Usa el buscador integrado para encontrar productos de nombres largos.</span>", unsafe_allow_html=True)

        # 4. PRECIOS Y LÓGICA
        moneda = st.radio("Moneda visible:", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
        precio = st.number_input("Precio Marcado", min_value=0.0, step=0.01)
        
        if moneda == "Bolívares (Bs)" and precio > 0:
            st.markdown(f"<div class='info-msg'>Precio en Bs: {precio:.2f} Bs | Equivalente: {(precio/tasa_bcv):.2f} $ al cambio BCV</div>", unsafe_allow_html=True)
        
        # 5. SUBMIT
        if st.form_submit_button("🚀 TRANSMITIR REGISTRO"):
            if producto == "-- Seleccione --":
                st.error("❌ Debes seleccionar un producto.")
            else:
                # Payload que incluye TODOS los campos posibles para evitar el error 23502
                payload = {
                    "fecha_captura": str(datetime.date.today()),
                    "vendedor": vendedor,
                    "competencia": competencia,
                    "nombre_producto": producto,
                    "serial_escaneado": serial if serial else "N/A",
                    "precio_competencia_usd": float(round(precio if moneda == "Dólares ($)" else precio/tasa_bcv, 2))
                }
                
                headers = {
                    "apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", 
                    "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", 
                    "Content-Type": "application/json"
                }
                
                res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
                
                if res.status_code in [200, 201, 204]:
                    st.session_state['submitted'] = True
                    st.rerun()
                else:
                    st.error(f"❌ Error de Base de Datos ({res.status_code}): {res.text}")

else:
    st.success("✅ ¡Registro enviado exitosamente!")
    if st.button("🔄 Siguiente Registro"):
        st.session_state['submitted'] = False
        st.rerun()
