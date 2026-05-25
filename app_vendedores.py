import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="JMW Store Check", layout="centered")

# --- CSS MEJORADO (Sin negros) ---
st.markdown("""
    <style>
    .stApp { background-color: #367c87 !important; }
    h1, .stMarkdown, label { color: #ffffff !important; }
    /* Selectores en naranja claro */
    div[data-baseweb="select"], div[data-baseweb="input"], .stNumberInput input { 
        background-color: #fff2e6 !important; color: #333 !important; 
    }
    .bcv-box { background: #2a616a; color: white; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; border: 1px solid #ffffff; margin-bottom: 20px; }
    .price-value { font-size: 24px; font-weight: 800; color: #ff8c00; background: #ffffff; text-align: center; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    div.stButton > button { background-color: #ff8c00 !important; color: white !important; font-weight: bold; border: none; height: 3.5rem; width: 100%; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if 'vendedor' not in st.session_state: st.session_state.vendedor = "Jad"
if 'competencia' not in st.session_state: st.session_state.competencia = "Forum"

# --- CARGA ---
@st.cache_data(ttl=3600)
def cargar_maestro():
    df = pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")
    df.columns = [str(c).lower().strip().replace(" ", "_") for c in df.columns]
    return df

df_maestro = cargar_maestro()

st.markdown("<h1>📊 JMW Store Check</h1>", unsafe_allow_html=True)

# Tasa BCV
try:
    res = requests.get("https://www.bcv.org.ve/", timeout=5, verify=False)
    tasa = float(BeautifulSoup(res.text, 'html.parser').find(id="dolar").find('strong').text.strip().replace(',', '.'))
except: tasa = 530.50
st.markdown(f"<div class='bcv-box'>🇻🇪 Tasa BCV: {tasa:.2f} Bs/$</div>", unsafe_allow_html=True)

# 1. Auditor (Persistente)
with st.expander("👤 1. Auditor y Establecimiento", expanded=True):
    st.session_state.vendedor = st.selectbox("Auditor", ["Jad", "Alexander", "Maria", "Juana"], index=["Jad", "Alexander", "Maria", "Juana"].index(st.session_state.vendedor))
    st.session_state.competencia = st.selectbox("Establecimiento", ["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"], index=["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"].index(st.session_state.competencia))

# 2. Evidencia
with st.expander("📷 2. Escáner y Evidencia", expanded=True):
    tipo_foto = st.radio("Método", ["Cámara", "Archivo"], horizontal=True)
    foto = st.camera_input("Capturar") if tipo_foto == "Cámara" else st.file_uploader("Subir imagen", type=['jpg', 'png'])
    serial_manual = st.text_input("Serial (Código de barras)", key="serial_input")

# 3. Producto
with st.expander("📦 3. Producto y Precio", expanded=True):
    busqueda = st.text_input("Buscar Producto (Nombre o SKU):", key="busqueda")
    df_filtrado = df_maestro[df_maestro['nombre'].str.contains(busqueda, case=False, na=False)] if busqueda else df_maestro
    prod_sel = st.selectbox("Seleccionar", df_filtrado['nombre'].tolist(), index=None, key="prod_sel")
    es_usd = st.toggle("¿Precio en DÓLARES?", True)
    precio = st.number_input("Precio Marcado", min_value=0.0, step=0.01, key="precio_input")
    val_usd = precio if es_usd else (precio / tasa)
    st.markdown(f"<div class='price-value'>VALOR: {val_usd:.2f} $</div>", unsafe_allow_html=True)

# 4. Transmisión
if st.button("🚀 TRANSMITIR REGISTRO"):
    if not prod_sel:
        st.error("⚠️ ¡Debes seleccionar un producto!")
    else:
        fila = df_maestro[df_maestro["nombre"] == prod_sel].iloc[0]
        payload = {
            "fecha_captura": str(datetime.date.today()),
            "vendedor": st.session_state.vendedor,
            "competencia": st.session_state.competencia,
            "serial_escaneado": serial_manual if serial_manual else str(fila.get("serial", "N/A")),
            "nombre_producto": str(prod_sel),
            "segmento": str(fila.get("segmento", "N/A")),
            "proveedor": str(fila.get("proveedor", "N/A")),
            "rubro": str(fila.get("rubro", "N/A")),
            "sub_categoria": str(fila.get("sub_categoria", "N/A")),
            "moneda_origen": "USD" if es_usd else "VES",
            "precio_bruto_origen": float(precio),
            "tasa_bcv_momento": float(tasa),
            "precio_competencia_usd": float(val_usd),
            "foto_url": "FOTO_ADJUNTA" if foto else "SIN FOTO"
        }
        
        headers = {"apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Content-Type": "application/json"}
        res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
        
        if res.status_code in [200, 201, 204]:
            st.success("✅ ¡Registro enviado exitosamente!")
            st.toast("Esperando nuevo producto...")
            time.sleep(2) # Pausa para que el usuario lea el éxito
            # Limpiar solo producto y precio
            st.rerun()
        else:
            st.error(f"❌ Error: {res.text}")
