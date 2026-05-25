import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="JMW Store Check", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    h1 { color: #ffffff !important; text-align: center; font-weight: 800; font-size: 26px !important; }
    h2 { color: #ffffff !important; text-align: center; font-size: 18px !important; margin-bottom: 20px !important; }
    .help-text { color: #e0e0e0 !important; font-size: 13px !important; font-style: italic !important; margin-bottom: 10px !important; }
    .stButton>button { background: #1c355e !important; color: white !important; font-weight: bold; border-radius: 8px; width: 100%; height: 3.5rem; }
    .info-msg { background: #1c355e; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)

# --- CONEXIÓN BCV ---
@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        res = requests.get("https://www.bcv.org.ve/", headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        return float(soup.find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 530.50

tasa_bcv = obtener_tasa_bcv()
st.markdown(f"<div class='info-msg'>Tasa BCV: {tasa_bcv:.2f} Bs/$</div>", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=1800)
def cargar_maestro_local():
    return pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")

df_maestro = cargar_maestro_local()

# --- FORMULARIO ---
if 'submitted' not in st.session_state: st.session_state['submitted'] = False

if not st.session_state['submitted']:
    with st.form("form_final"):
        with st.expander("👤 Persona y Datos de Control", expanded=True):
            vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
            competencia = st.selectbox("Establecimiento", ["Competencia1", "Competencia2", "Competencia3", "Otro"])
        
        with st.expander("📷 Escáner"):
            st.camera_input("Enfocar")
            serial = st.text_input("Código de Barras")

        producto_sel = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist())
        moneda = st.radio("Moneda:", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
        precio = st.number_input("Precio Marcado", min_value=0.0, step=0.01)

        if st.form_submit_button("🚀 TRANSMITIR REGISTRO"):
            if producto_sel == "-- Seleccione --":
                st.error("Seleccione un producto.")
            else:
                info = df_maestro[df_maestro["nombre"] == producto_sel].iloc[0]
                # ESTE PAYLOAD TIENE LAS COLUMNAS EXACTAS DE TU BASE DE DATOS ORIGINAL
                payload = {
                    "fecha_captura": str(datetime.date.today()),
                    "vendedor": str(vendedor),
                    "competencia": str(competencia),
                    "serial_escaneado": str(serial) if serial else str(info.get("serial", "N/A")),
                    "nombre_producto": str(producto_sel),
                    "segmento": str(info.get("segmento1", "N/A")),
                    "proveedor": str(info.get("proveedor", "N/A")),
                    "rubro": str(info.get("rubro", "N/A")),
                    "sub_categoria": str(info.get("sub_categoria", "N/A")),
                    "moneda_origen": "VES" if moneda == "Bolívares (Bs)" else "USD",
                    "precio_bruto_origen": float(precio),
                    "tasa_bcv_momento": float(tasa_bcv),
                    "precio_competencia_usd": float(round(precio if moneda == "Dólares ($)" else precio/tasa_bcv, 2)),
                    "foto_url": "SIN FOTO"
                }
                
                headers = {"apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Content-Type": "application/json"}
                res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
                
                if res.status_code in [200, 201, 204]:
                    st.session_state['submitted'] = True
                    st.rerun()
                else:
                    st.error(f"Error {res.status_code}: {res.text}")
else:
    st.success("✅ ¡Registro enviado exitosamente!")
    if st.button("🔄 Siguiente"):
        st.session_state['submitted'] = False
        st.rerun()
