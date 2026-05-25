import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="JMW Store Check", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;600&display=swap');
    .stApp { background-color: #f0f7f6 !important; font-family: 'Outfit', sans-serif !important; }
    h1 { color: #008080 !important; text-align: center; font-weight: 800 !important; }
    .bcv-box { background: #008080; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 20px; }
    .price-box { background: #ffffff; color: #008080; padding: 20px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: 800; border: 3px solid #008080; margin: 15px 0; }
    .stButton>button { background: #008080 !important; color: white !important; font-weight: bold; border-radius: 12px; width: 100%; height: 3.5rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)

# --- 1. CARGA DE DATOS ---
@st.cache_data(ttl=600)
def cargar_maestro():
    df = pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")
    df.columns = [str(c).lower().strip().replace(" ", "_") for c in df.columns]
    df['nombre'] = df['nombre'].astype(str).str.strip()
    return df

df_maestro = cargar_maestro()

# --- 2. TASA BCV ---
@st.cache_data(ttl=3600)
def get_tasa():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get("https://www.bcv.org.ve/", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        return float(soup.find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 530.50

tasa_bcv = get_tasa()
st.markdown(f"<div class='bcv-box'>🇻🇪 Tasa BCV: {tasa_bcv:.2f} Bs/$</div>", unsafe_allow_html=True)

# --- 3. INTERFAZ ---
with st.expander("👤 1. Auditor y Establecimiento", expanded=True):
    vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
    competencia = st.selectbox("Establecimiento", ["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"])

with st.expander("📷 2. Escáner y Serial", expanded=True):
    foto = st.camera_input("Tomar foto")
    serial_manual = st.text_input("Código de Barras Manual")

with st.expander("📦 3. Seleccionar Producto", expanded=True):
    producto = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist())

with st.expander("💰 4. Registro de Precio", expanded=True):
    es_usd = st.toggle("¿Precio en USD?", True)
    precio = st.number_input("Precio Marcado", min_value=0.0)
    valor_final = precio if es_usd else (precio / tasa_bcv)
    st.markdown(f"<div class='price-box'>VALOR USD: {valor_final:.2f} $</div>", unsafe_allow_html=True)

# --- 4. TRANSMISIÓN ---
if st.button("🚀 TRANSMITIR REGISTRO"):
    if producto == "-- Seleccione --":
        st.error("¡Selecciona un producto!")
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
            "precio_competencia_usd": float(valor_final),
            "foto_url": "FOTO_TOMADA" if foto else "SIN FOTO"
        }
        
        headers = {
            "apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL",
            "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL",
            "Content-Type": "application/json"
        }
        
        res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
        
        if res.status_code in [200, 201, 204]:
            st.success("✅ ¡Registro enviado exitosamente!")
            st.balloons()
        else:
            st.error(f"Error: {res.text}")
