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
    .stApp { background-color: #f0f7f6 !important; font-family: 'Outfit', sans-serif !important; }
    h1 { color: #008080 !important; text-align: center; font-weight: 800 !important; }
    .bcv-box { background: #008080; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .price-box { background: #ffffff; color: #008080; padding: 20px; border-radius: 15px; text-align: center; font-size: 28px; font-weight: 800; border: 3px solid #008080; margin: 15px 0; }
    .stButton>button { background: #008080 !important; color: white !important; font-weight: bold; border-radius: 12px; width: 100%; height: 3.5rem; border: none; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)

# --- 1. CONEXIÓN BCV ---
@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        res = requests.get("https://www.bcv.org.ve/", headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        return float(soup.find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 530.50

tasa_bcv = obtener_tasa_bcv()
st.markdown(f"<div class='bcv-box'>🇻🇪 Tasa BCV Actual: {tasa_bcv:.2f} Bs/$</div>", unsafe_allow_html=True)

# --- 2. CARGA DATOS ---
@st.cache_data(ttl=1800)
def cargar_maestro():
    try:
        df = pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")
        df.columns = [str(c).lower().strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

df_maestro = cargar_maestro()

# --- 3. FORMULARIO ---
with st.expander("👤 1. Auditor y Establecimiento", expanded=True):
    vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
    competencia = st.selectbox("Establecimiento", ["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"])

with st.expander("📷 2. Escáner de Producto (Opcional)", expanded=True):
    foto = st.camera_input("Tomar foto")
    serial = st.text_input("Código de Barras Manual")

with st.expander("📦 3. Seleccionar Producto", expanded=True):
    producto_sel = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist())

with st.expander("💰 4. Registro de Precio", expanded=True):
    es_dolar = st.toggle("¿Precio en DÓLARES ($)?", value=True)
    moneda_txt = "DÓLARES ($)" if es_dolar else "BOLÍVARES (Bs)"
    precio = st.number_input(f"Precio Marcado en {moneda_txt}", min_value=0.0, step=0.01)
    
    valor_final = precio if es_dolar else (precio / tasa_bcv)
    label_valor = "VALOR EN DÓLARES ($):" if es_dolar else "VALOR CALCULADO EN DÓLARES ($):"
    st.markdown(f"<div class='price-box'>{label_valor}<br>{valor_final:.2f} $</div>", unsafe_allow_html=True)

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
            "precio_competencia_usd": float(round(valor_final, 2)),
            "foto_url": "SIN FOTO"
        }
        
        headers = {"apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", "Content-Type": "application/json"}
        res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
        
        if res.status_code in [200, 201, 204]:
            st.success("✅ ¡Registro enviado exitosamente!")
        else:
            st.error(f"Error: {res.text}")
