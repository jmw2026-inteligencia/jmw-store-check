import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JMW Store Check", layout="centered")

# --- CSS AZUL CORPORATIVO ---
st.markdown("""
    <style>
    .stApp { background-color: #367c87 !important; color: #ffffff !important; }
    .bcv-box { background: #2a616a; color: white; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; border: 1px solid #ffffff; }
    .price-value { font-size: 24px; font-weight: 800; color: #ff8c00; background: #ffffff; text-align: center; padding: 15px; border-radius: 10px; }
    div.stButton > button { background-color: #ff8c00 !important; color: white !important; font-weight: bold; border: none; height: 3.5rem; width: 100%; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE ESTADO ---
if 'serial' not in st.session_state: st.session_state.serial = ""
if 'precio' not in st.session_state: st.session_state.precio = 0.0
if 'prod' not in st.session_state: st.session_state.prod = "-- Seleccione --"

st.markdown("<h1>📊 JMW Store Check</h1>", unsafe_allow_html=True)

# --- CARGA RÁPIDA DE DATOS ---
@st.cache_data(ttl=600)
def cargar_maestro():
    df = pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")
    df.columns = [str(c).lower().strip().replace(" ", "_") for c in df.columns]
    df['nombre'] = df['nombre'].astype(str).str.strip()
    return df

df_maestro = cargar_maestro()

# --- TASA BCV ---
def get_tasa():
    try:
        res = requests.get("https://www.bcv.org.ve/", timeout=5, verify=False)
        return float(BeautifulSoup(res.text, 'html.parser').find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 530.50

tasa_bcv = get_tasa()
st.markdown(f"<div class='bcv-box'>🇻🇪 Tasa BCV: {tasa_bcv:.2f} Bs/$</div>", unsafe_allow_html=True)

# --- INTERFAZ ---
vendedor = st.selectbox("Auditor", ["Jad", "Alexander", "Maria", "Juana"], key="vendedor_sel")
competencia = st.selectbox("Establecimiento", ["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"], key="competencia_sel")

foto = st.file_uploader("Evidencia (Imagen)", type=['jpg', 'png'])
serial_manual = st.text_input("Serial (Código de barras)", key="serial")

producto = st.selectbox("Seleccionar Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist(), key="prod")

es_usd = st.toggle("¿Precio en DÓLARES?", True)
precio = st.number_input("Precio Marcado", min_value=0.0, step=0.01, key="precio")

valor_usd = precio if es_usd else (precio / tasa_bcv)
st.markdown(f"<div class='price-value'>VALOR: {valor_usd:.2f} $</div>", unsafe_allow_html=True)

# --- TRANSMISIÓN ---
if st.button("🚀 TRANSMITIR REGISTRO"):
    if producto == "-- Seleccione --":
        st.error("⚠️ ¡Debes seleccionar un producto!")
    else:
        fila = df_maestro[df_maestro["nombre"] == producto].iloc[0]
        payload = {
            "fecha_captura": str(datetime.date.today()),
            "vendedor": vendedor,
            "competencia": competencia,
            "serial_escaneado": serial_manual if serial_manual else str(fila.get("serial", "N/A")),
            "nombre_producto": producto,
            "segmento": str(fila.get("segmento", "N/A")),
            "proveedor": str(fila.get("proveedor", "N/A")),
            "rubro": str(fila.get("rubro", "N/A")),
            "sub_categoria": str(fila.get("sub_categoria", "N/A")),
            "moneda_origen": "USD" if es_usd else "VES",
            "precio_bruto_origen": float(precio),
            "tasa_bcv_momento": float(tasa_bcv),
            "precio_competencia_usd": float(valor_usd),
            "foto_url": "FOTO_ADJUNTA" if foto else "SIN FOTO"
        }
        
        headers = {"apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Content-Type": "application/json"}
        res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
        
        if res.status_code in [200, 201, 204]:
            st.success("✅ ¡Registro enviado!")
            st.session_state.serial = ""
            st.session_state.precio = 0.0
            st.session_state.prod = "-- Seleccione --"
            st.rerun()
        else:
            st.error(f"❌ Error: {res.text}")
