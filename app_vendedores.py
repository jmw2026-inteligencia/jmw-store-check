import streamlit as st
import requests
import datetime
import pandas as pd
import uuid

# --- CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="JMW Store Check", layout="centered")

# --- CARGA DE DATOS ---
@st.cache_data(ttl=1800)
def cargar_maestro_local():
    return pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")

df_maestro = cargar_maestro_local()
tasa_bcv = 530.50 # Actualizado según tu ejemplo

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

        # Filtro de producto
        producto_seleccionado = st.selectbox("Producto", ["-- Seleccione --"] + df_maestro["nombre"].tolist())
        
        moneda = st.radio("Moneda:", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
        precio = st.number_input("Precio Marcado", min_value=0.0, step=0.01)

        submit = st.form_submit_button("🚀 TRANSMITIR REGISTRO")

        if submit:
            if producto_seleccionado == "-- Seleccione --":
                st.error("Seleccione un producto.")
            else:
                # Buscamos datos adicionales del maestro para completar las columnas obligatorias
                info = df_maestro[df_maestro["nombre"] == producto_seleccionado].iloc[0]
                
                # PAYLOAD COMPLETO SEGÚN TU TABLA
                payload = {
                    "id": str(uuid.uuid4()),
                    "fecha_captura": str(datetime.date.today()),
                    "vendedor": vendedor,
                    "competencia": competencia,
                    "serial_escaneado": str(serial) if serial else str(info.get("serial", "N/A")),
                    "nombre_producto": str(producto_seleccionado),
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
                
                headers = {
                    "apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", 
                    "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL", 
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                }
                
                res = requests.post("https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", headers=headers, json=payload)
                
                if res.status_code in [200, 201]:
                    st.session_state['submitted'] = True
                    st.rerun()
                else:
                    st.error(f"Error {res.status_code}: {res.text}")
else:
    st.success("✅ ¡Registro enviado exitosamente!")
    if st.button("🔄 Siguiente Registro"):
        st.session_state['submitted'] = False
        st.rerun()
