import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JMW Store Check", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;600&display=swap');
    .stApp { background-color: #f8fbfb !important; font-family: 'Outfit', sans-serif !important; }
    h1 { color: #008080 !important; text-align: center; font-weight: 800 !important; }
    .bcv-box { background: #008080; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px; }
    .price-box { background: #e0f2f1; color: #00695c; padding: 15px; border-radius: 10px; text-align: center; font-size: 20px; font-weight: bold; border: 2px solid #008080; }
    .stButton>button { background: #008080 !important; color: white !important; border-radius: 8px; width: 100%; height: 3rem; font-weight: bold; }
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
        res = requests.get("https://www.bcv.org.ve/", headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        return float(soup.find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 530.50

tasa_bcv = get_tasa()
st.markdown(f"<div class='bcv-box'>🇻🇪 Tasa BCV: {tasa_bcv:.2f} Bs/$</div>", unsafe_allow_html=True)

# --- 3. INTERFAZ ---
with st.expander("👤 Auditor y Punto de Venta", expanded=True):
    vendedor = st.selectbox("Auditor", ["Jad", "Alexander", "Maria", "Juana"])
    competencia = st.selectbox("Establecimiento", ["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"])

with st.expander("📷 Evidencia Fotográfica y Serial", expanded=True):
    foto = st.camera_input("Capturar evidencia")
    serial_manual = st.text_input("Serial (Código de barras)")

with st.expander("📦 Producto y Segmentación", expanded=True):
    producto = st.selectbox("Seleccionar Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist())
    
    es_usd = st.toggle("¿El precio marcado es en DÓLARES?", True)
    label_precio = "Precio Marcado en DÓLARES ($)" if es_usd else "Precio Marcado en BOLÍVARES (Bs)"
    precio = st.number_input(label_precio, min_value=0.0, step=0.01)
    
    valor_usd = precio if es_usd else (precio / tasa_bcv)
    st.markdown(f"<div class='price-box'>VALOR EN USD CALCULADO: {valor_usd:.2f} $</div>", unsafe_allow_html=True)

# --- 4. TRANSMISIÓN ---
if st.button("🚀 TRANSMITIR REGISTRO"):
    if producto == "-- Seleccione --":
        st.error("Por favor, selecciona un producto.")
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
        
        headers = {
            "apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL",
            "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL",
            "Content-Type": "application/json"
        }
        
        res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
        
        if res.status_code in [200, 201, 204]:
            st.success("✅ ¡Registro enviado exitosamente!")
        else:
            st.error(f"Error técnico: {res.text}")
