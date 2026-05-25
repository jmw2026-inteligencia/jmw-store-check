import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup

st.set_page_config(page_title="JMW Auditoría", layout="centered")

# --- 1. CARGA DE DATOS ---
@st.cache_data(ttl=600)
def cargar_maestro():
    df = pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")
    df.columns = [str(c).lower().strip().replace(" ", "_") for c in df.columns]
    df['nombre'] = df['nombre'].astype(str).str.strip()
    return df

df_maestro = cargar_maestro()

# --- 2. TASA BCV REAL ---
@st.cache_data(ttl=3600)
def get_tasa():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get("https://www.bcv.org.ve/", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        return float(soup.find(id="dolar").find('strong').text.strip().replace(',', '.'))
    except: return 530.50

tasa_bcv = get_tasa()

# --- 3. INTERFAZ ---
st.title("JMW Store Check")
st.metric("Tasa BCV Actual", f"{tasa_bcv} Bs/$")

with st.expander("👤 1. Datos Generales", expanded=True):
    vendedor = st.selectbox("Vendedor", ["Jad", "Alexander", "Maria", "Juana"])
    competencia = st.selectbox("Establecimiento", ["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"])

with st.expander("📷 2. Evidencia y Serial", expanded=True):
    foto = st.camera_input("Tomar foto del punto de venta")
    serial_manual = st.text_input("Digitar Serial (si el escáner falla)")

with st.expander("📦 3. Producto y Precio", expanded=True):
    producto = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist())
    precio = st.number_input("Precio Marcado", min_value=0.0)
    es_usd = st.toggle("¿Precio en USD?", True)

if st.button("🚀 TRANSMITIR REGISTRO"):
    if producto == "-- Seleccione --":
        st.error("¡Selecciona un producto!")
    else:
        fila = df_maestro[df_maestro["nombre"] == producto].iloc[0]
        
        # Validar si faltan datos en el Excel
        if pd.isna(fila.get("segmento")):
            st.warning("⚠️ El Excel no tiene datos de Segmento/Proveedor para este producto.")
        
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
            "precio_competencia_usd": float(precio if es_usd else precio/tasa_bcv),
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
            st.error(f"Error al enviar: {res.text}")
