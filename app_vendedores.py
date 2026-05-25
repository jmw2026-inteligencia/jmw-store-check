import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JMW Store Check", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    h1 { color: white !important; text-align: center; font-weight: 800; }
    .price-box { background: #1c355e; color: #00ffcc; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; border: 2px solid white; margin: 15px 0; }
    .stButton>button { background: #1c355e !important; color: white !important; font-weight: bold; width: 100%; height: 3.5rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)

# --- CONEXIÓN BCV ---
@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        res = requests.get("https://www.bcv.org.ve/", headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        return float(soup.find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 530.50

tasa_bcv = obtener_tasa_bcv()
st.sidebar.metric("Tasa BCV", f"{tasa_bcv} Bs/$")

# --- CARGA DATOS ---
@st.cache_data(ttl=1800)
def cargar_maestro():
    df = pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")
    df.columns = [str(c).lower().strip() for c in df.columns]
    return df

df_maestro = cargar_maestro()

# --- INTERFAZ ---
vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
competencia = st.selectbox("Establecimiento", ["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"])
producto_sel = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist())

# Lógica de Moneda Instantánea
col_t, col_p = st.columns([1, 2])
with col_t:
    es_dolar = st.toggle("¿Precio en $?", value=True)
with col_p:
    moneda_txt = "DÓLARES ($)" if es_dolar else "BOLÍVARES (Bs)"
    st.markdown(f"### Moneda: {moneda_txt}")

precio = st.number_input(f"Precio Marcado", min_value=0.0, step=0.01)

# Cálculo visual inmediato
precio_usd = precio if es_dolar else (precio / tasa_bcv)
st.markdown(f"<div class='price-box'>VALOR USD: {precio_usd:.2f} $</div>", unsafe_allow_html=True)

serial = st.text_input("Código de Barras")

# Transmisión
if st.button("🚀 TRANSMITIR REGISTRO"):
    if producto_sel == "-- Seleccione --":
        st.error("Selecciona un producto.")
    else:
        info = df_maestro[df_maestro["nombre"] == producto_sel].iloc[0]
        payload = {
            "fecha_captura": str(datetime.date.today()),
            "vendedor": str(vendedor),
            "competencia": str(competencia),
            "serial_escaneado": str(serial) if serial else str(info.get("serial", "N/A")),
            "nombre_producto": str(producto_sel),
            "segmento": str(info.get("segmento", "N/A")),
            "proveedor": str(info.get("proveedor", "N/A")),
            "rubro": str(info.get("rubro", "N/A")),
            "sub_categoria": str(info.get("sub_categoria", "N/A")),
            "moneda_origen": "USD" if es_dolar else "VES",
            "precio_bruto_origen": float(precio),
            "tasa_bcv_momento": float(tasa_bcv),
            "precio_competencia_usd": float(round(precio_usd, 2)),
            "foto_url": "SIN FOTO"
        }
        
        headers = {"apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Content-Type": "application/json"}
        res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
        
        if res.status_code in [200, 201, 204]:
            st.success("✅ Registro Exitoso")
        else:
            st.error(f"Error: {res.text}")
