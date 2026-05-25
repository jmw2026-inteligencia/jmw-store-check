import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup
import urllib3

# --- CONFIGURACIÓN ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="JMW Store Check", layout="centered")

# --- CSS OSCURO CORPORATIVO ---
st.markdown("""
    <style>
    /* Fondo oscuro global */
    .stApp { background-color: #121212 !important; color: #e0e0e0 !important; font-family: 'Outfit', sans-serif !important; }
    
    /* Encabezados y texto */
    h1 { color: #008080 !important; text-align: center; font-weight: 800 !important; margin-bottom: 20px; }
    
    /* Box BCV y Precios */
    .bcv-box { background: #1e1e1e; border: 1px solid #008080; color: #008080; padding: 15px; border-radius: 12px; text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px; }
    .price-value { font-size: 28px; font-weight: 800; color: #ff8c00; text-align: center; padding: 15px; border: 2px dashed #ff8c00; border-radius: 12px; margin-bottom: 20px; background: #2a2a2a; }
    
    /* Expanders y Inputs */
    .stExpander { background-color: #1e1e1e !important; border-color: #333 !important; }
    
    /* Botón Transmitir */
    div.stButton > button { background-color: #008080 !important; color: white !important; font-weight: bold; border: none; height: 3.5rem; width: 100%; border-radius: 8px; }
    div.stButton > button:hover { background-color: #006666 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>📊 JMW Store Check</h1>", unsafe_allow_html=True)

# --- 1. CARGA DE DATOS ---
@st.cache_data(ttl=600)
def cargar_maestro():
    df = pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")
    df.columns = [str(c).lower().strip().replace(" ", "_") for c in df.columns]
    df['nombre'] = df['nombre'].astype(str).str.strip()
    return df

df_maestro = cargar_maestro()

# --- 2. TASA BCV ---
def get_tasa():
    try:
        res = requests.get("https://www.bcv.org.ve/", headers={"User-Agent": "Mozilla/5.0"}, timeout=8, verify=False)
        if res.status_code == 200:
            return float(BeautifulSoup(res.text, 'html.parser').find(id="dolar").find('strong').text.strip().replace(',', '.'))
        return 530.50
    except: return 530.50

tasa_bcv = get_tasa()
st.markdown(f"<div class='bcv-box'>🇻🇪 Tasa BCV: {tasa_bcv:.2f} Bs/$</div>", unsafe_allow_html=True)

# --- 3. INTERFAZ ---
with st.expander("👤 1. Auditor y Punto de Venta", expanded=True):
    vendedor = st.selectbox("Auditor", ["Jad", "Alexander", "Maria", "Juana"], key="vendedor")
    competencia = st.selectbox("Establecimiento", ["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"], key="competencia")

with st.expander("📷 2. Escáner y Evidencia", expanded=True):
    foto = st.camera_input("Capturar evidencia")
    serial_manual = st.text_input("Serial (Código de barras)", key="serial")

with st.expander("📦 3. Producto y Precio", expanded=True):
    producto = st.selectbox("Seleccionar Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist(), key="prod")
    es_usd = st.toggle("¿Precio en DÓLARES?", True)
    label_precio = "Precio Marcado ($)" if es_usd else "Precio Marcado (Bs)"
    precio = st.number_input(label_precio, min_value=0.0, step=0.01, key="precio")
    valor_usd = precio if es_usd else (precio / tasa_bcv)
    st.markdown(f"<div class='price-value'>VALOR: {valor_usd:.2f} $</div>", unsafe_allow_html=True)

# --- 4. TRANSMISIÓN ---
if st.button("🚀 TRANSMITIR REGISTRO"):
    if producto == "-- Seleccione --":
        st.error("⚠️ ¡Debes seleccionar un producto!")
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
            st.success("✅ ¡Registro enviado exitosamente!")
            st.session_state.serial = ""
            st.session_state.precio = 0.0
            st.session_state.prod = "-- Seleccione --"
            st.rerun()
        else:
            st.error(f"❌ Error al transmitir: {res.text}")
