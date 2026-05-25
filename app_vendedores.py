import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JMW Store Check", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f8fbfb !important; }
    h1 { color: #008080 !important; text-align: center; font-weight: 800 !important; }
    .bcv-box { background: #008080; color: white; padding: 12px; border-radius: 12px; text-align: center; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>📊 JMW Store Check</h1>", unsafe_allow_html=True)

# --- 1. CARGA SEGURA DE DATOS ---
@st.cache_data(ttl=600)
def get_maestro():
    archivo = "IMPORTACION_ANALISIS_PRECIO.xlsx"
    if not os.path.exists(archivo):
        return None # Devuelve None si no existe el archivo
    df = pd.read_excel(archivo, sheet_name="PRODUCTOS")
    df.columns = [str(c).lower().strip().replace(" ", "_") for c in df.columns]
    df['nombre'] = df['nombre'].astype(str).str.strip()
    return df

df_maestro = get_maestro()

if df_maestro is None:
    st.error("⚠️ ERROR: No se encuentra el archivo 'IMPORTACION_ANALISIS_PRECIO.xlsx'. Por favor, súbelo a la carpeta del proyecto.")
    st.stop() # Detiene la ejecución aquí para que no de error

# --- 2. TASA BCV ---
def get_tasa():
    try:
        res = requests.get("https://www.bcv.org.ve/", headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        return float(soup.find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 530.50

tasa_bcv = get_tasa()
st.markdown(f"<div class='bcv-box'>🇻🇪 Tasa BCV: {tasa_bcv:.2f} Bs/$</div>", unsafe_allow_html=True)

# --- 3. INTERFAZ ---
vendedor = st.selectbox("Auditor", ["Jad", "Alexander", "Maria", "Juana"], key="vendedor")
competencia = st.selectbox("Establecimiento", ["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"], key="competencia")

# Foto y Serial
tipo_foto = st.radio("Evidencia", ["Cámara", "Archivo"], horizontal=True)
foto = st.camera_input("Capturar") if tipo_foto == "Cámara" else st.file_uploader("Subir", type=['jpg'])
serial_manual = st.text_input("Serial", key="serial")

# Producto
producto = st.selectbox("Seleccionar Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist(), key="prod")

es_usd = st.toggle("¿Precio en DÓLARES?", True)
precio = st.number_input("Precio Marcado", min_value=0.0, step=0.01, key="precio")
valor_usd = precio if es_usd else (precio / tasa_bcv)
st.write(f"### Valor en USD: {valor_usd:.2f} $")

# --- 4. TRANSMISIÓN ---
if st.button("🚀 TRANSMITIR"):
    if producto == "-- Seleccione --":
        st.error("Selecciona un producto.")
    else:
        fila = df_maestro[df_maestro["nombre"] == producto].iloc[0]
        payload = {
            "fecha_captura": str(datetime.date.today()),
            "vendedor": str(vendedor),
            "competencia": str(competencia),
            "serial_escaneado": str(serial_manual) if serial_manual else str(fila.get("serial", "N/A")),
            "nombre_producto": str(producto),
            "segmento": str(fila.get("segmento", "N/A")),
            "proveedor": str(fila.get("proveedor", "N/A")),
            "rubro": str(fila.get("rubro", "N/A")),
            "sub_categoria": str(fila.get("sub_categoria", "N/A")),
            "moneda_origen": "USD" if es_usd else "VES",
            "precio_bruto_origen": float(precio),
            "tasa_bcv_momento": float(tasa_bcv),
            "precio_competencia_usd": float(valor_usd),
            "foto_url": "FOTO_TOMADA" if foto else "SIN FOTO"
        }
        
        headers = {"apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Content-Type": "application/json"}
        res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
        
        if res.status_code in [200, 201, 204]:
            st.success("✅ ¡Enviado!")
            st.session_state.serial = ""
            st.session_state.precio = 0.0
            st.session_state.prod = "-- Seleccione --"
            st.rerun()
        else:
            st.error(f"Error: {res.text}")
