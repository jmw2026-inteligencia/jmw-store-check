import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup

# --- 1. CONFIGURACIÓN VISUAL Y ESTÉTICA (JMW CORPORATIVO) ---
st.set_page_config(page_title="JMW Store Check", page_icon="📊", layout="centered")

st.markdown("""
    <style>
    /* Fondo Teal Corporativo */
    .stApp { background-color: #00a99d !important; }
    
    /* Encabezados */
    h1 { color: #ffffff !important; text-align: center; font-weight: 800; font-size: 30px !important; margin-bottom: 0px !important; }
    h3 { color: #fdfdfd !important; text-align: center; font-size: 16px !important; font-weight: 400; margin-bottom: 25px !important; }
    
    /* Textos de Ayuda / Explicación */
    .help-text { color: #e0f2f1 !important; font-size: 14px !important; font-style: italic !important; display: block; margin-bottom: 12px; margin-top: -10px; }
    
    /* Sección de Precios Dinámica */
    .price-header { color: #1c355e !important; background-color: #ffffff; padding: 10px; border-radius: 8px 8px 0 0; font-weight: bold; text-align: center; border: 1px solid #1c355e; margin-bottom: 0px; }
    
    /* Botones y Mensajes */
    .stButton>button { background: #1c355e !important; color: white !important; font-weight: bold; border-radius: 8px; width: 100%; height: 3.5rem; border: none; font-size: 18px; }
    .stButton>button:hover { background: #2c4a7c !important; color: #ffffff !important; }
    .info-msg { background: #1c355e; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; margin-top: 15px; border: 1px solid #00a99d; }
    
    /* Estilo de Expanders */
    .streamlit-expanderHeader { background-color: rgba(255,255,255,0.1) !important; color: white !important; border-radius: 8px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>JMW Store Check</h1>", unsafe_allow_html=True)
st.markdown("<h3>Monitoreo de Competencia y Análisis de Precios</h3>", unsafe_allow_html=True)

# --- 2. CONEXIÓN BCV ---
@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get("https://www.bcv.org.ve/", headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        tasa_str = soup.find(id="dolar").find('strong').text.strip().replace(',', '.')
        return float(tasa_str)
    except:
        return 45.50 # Valor de respaldo

tasa_bcv = obtener_tasa_bcv()
st.sidebar.metric("Tasa BCV", f"{tasa_bcv} Bs/$")

# --- 3. CARGA DEL MAESTRO DE PRODUCTOS ---
@st.cache_data(ttl=1800)
def cargar_maestro():
    try:
        df = pd.read_excel("IMPORTACION_ANALISIS_PRECIO.xlsx", sheet_name="PRODUCTOS")
        # Normalizamos nombres de columnas a minúsculas para evitar errores
        df.columns = [str(c).lower().strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al cargar el Excel: {e}")
        return pd.DataFrame()

df_maestro = cargar_maestro()

# --- 4. INTERFAZ DE FORMULARIO ---
if 'submitted' not in st.session_state: st.session_state['submitted'] = False

if not st.session_state['submitted']:
    with st.form("form_captura"):
        
        # --- SECCIÓN 1: CONTROL ---
        with st.expander("👤 DATOS DEL AUDITOR Y LOCAL", expanded=True):
            vendedor = st.selectbox("Seleccione su nombre:", ["Jad", "Alexander", "Maria", "Juana"])
            st.markdown("<span class='help-text'>Obligatorio para el reporte de gestión diaria.</span>", unsafe_allow_html=True)
            
            competencia = st.selectbox("Local de la Competencia:", ["Forum", "Gama", "Plaza", "Central Madeirense", "Otros"])
            st.markdown("<span class='help-text'>Seleccione el establecimiento donde se encuentra.</span>", unsafe_allow_html=True)

        # --- SECCIÓN 2: ESCÁNER ---
        with st.expander("📷 IDENTIFICACIÓN DEL PRODUCTO"):
            st.camera_input("Enfocar Código de Barras")
            serial_manual = st.text_input("Código de Barras (Si el escaneo falla):")
            st.markdown("<span class='help-text'>Escriba el serial que aparece debajo de las barras.</span>", unsafe_allow_html=True)

        # --- SECCIÓN 3: PRODUCTO Y PRECIO ---
        st.markdown("<br>", unsafe_allow_html=True)
        producto_nombre = st.selectbox("Seleccione el Producto Maestro:", ["-- Seleccione --"] + df_maestro["nombre"].tolist())
        st.markdown("<span class='help-text'>Use el buscador escribiendo el nombre o marca.</span>", unsafe_allow_html=True)

        # Selección de Moneda
        moneda_opcion = st.radio("¿En qué moneda está el precio en el estante?", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
        
        # Título Dinámico de la Sección de Precio
        label_dinamico = f"INGRESE PRECIO EN {moneda_opcion.upper()}"
        st.markdown(f"<div class='price-header'>{label_dinamico}</div>", unsafe_allow_html=True)
        
        precio_input = st.number_input("", min_value=0.0, step=0.01, format="%.2f")
        st.markdown("<span class='help-text'>Escriba el monto exacto que marca la etiqueta.</span>", unsafe_allow_html=True)

        # Cálculo en tiempo real
        if precio_input > 0:
            es_bs = moneda_opcion == "Bolívares (Bs)"
            usd_calc = precio_input / tasa_bcv if es_bs else precio_input
            bs_calc = precio_input if es_bs else precio_input * tasa_bcv
            
            st.markdown(f"""
                <div class='info-msg'>
                    EQUIVALENCIA DE CAPTURA:<br>
                    <b>{bs_calc:.2f} Bs</b>  |  <b>{usd_calc:.2f} $</b><br>
                    <small>Calculado a tasa BCV: {tasa_bcv}</small>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        btn_transmitir = st.form_submit_button("🚀 TRANSMITIR A CENTRAL")

        if btn_transmitir:
            if producto_nombre == "-- Seleccione --":
                st.error("❌ ERROR: Debe seleccionar un producto del listado.")
            elif precio_input <= 0:
                st.error("❌ ERROR: El precio debe ser mayor a cero.")
            else:
                # Extraer información del Excel
                info_prod = df_maestro[df_maestro["nombre"] == producto_nombre].iloc[0]
                
                # Preparar el envío (PAYLOAD COMPLETO)
                payload = {
                    "fecha_captura": str(datetime.date.today()),
                    "vendedor": str(vendedor),
                    "competencia": str(competencia),
                    "serial_escaneado": str(serial_manual) if serial_manual else str(info_prod.get("serial", "N/A")),
                    "nombre_producto": str(producto_nombre),
                    "segmento": str(info_prod.get("segmento", "N/A")),
                    "proveedor": str(info_prod.get("proveedor", "N/A")),
                    "rubro": str(info_prod.get("rubro", "N/A")),
                    "sub_categoria": str(info_prod.get("sub_categoria", "N/A")),
                    "moneda_origen": "VES" if moneda_opcion == "Bolívares (Bs)" else "USD",
                    "precio_bruto_origen": float(precio_input),
                    "tasa_bcv_momento": float(tasa_bcv),
                    "precio_competencia_usd": float(round(precio_input if moneda_opcion == "Dólares ($)" else precio_input/tasa_bcv, 2)),
                    "foto_url": "SIN FOTO"
                }

                headers = {
                    "apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL",
                    "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                }

                try:
                    res = requests.post(
                        "https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check", 
                        headers=headers, 
                        json=payload
                    )
                    
                    if res.status_code in [200, 201, 204]:
                        st.session_state['submitted'] = True
                        st.rerun()
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
                except Exception as e:
                    st.error(f"Fallo de conexión: {e}")

else:
    # --- PANTALLA DE ÉXITO ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.success("✅ REGISTRO TRANSMITIDO EXITOSAMENTE")
    st.balloons()
    
    if st.button("➕ REGISTRAR OTRO PRODUCTO"):
        st.session_state['submitted'] = False
        st.rerun()
