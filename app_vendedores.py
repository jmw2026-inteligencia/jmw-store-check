import os
import datetime
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA E IDENTIDAD
# ==========================================
st.set_page_config(
    page_title="JMW - Captura Store Check", 
    page_icon="📸", 
    layout="centered"
)

# Estilo Premium: Fondo Azul-Verde JMW, Fuente Blanca, Inputs legibles
st.markdown("""
    <style>
    .stApp { background-color: #00a99d !important; }
    .block-container { padding-top: 1.5rem !important; max-width: 500px !important; }
    h1, h2, h3, p, span, .stMarkdown { color: #ffffff !important; font-family: 'Segoe UI', sans-serif; }
    h1 { font-size: 26px !important; font-weight: 700 !important; text-align: center; margin-bottom: 0px !important; }
    h2 { font-size: 20px !important; text-align: center; margin-top: 0px !important; margin-bottom: 5px !important; }
    label p { font-weight: 600 !important; color: #ffffff !important; font-size: 15px !important; }
    
    /* Input general styling */
    .stSelectbox>div>div, .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 8px !important; border: 1px solid #1c355e !important;
        background-color: #ffffff !important; color: #1c355e !important; font-weight: 500 !important;
    }
    
    /* Microinstrucciones estéticas */
    .help-text {
        color: #e0e0e0 !important;
        font-size: 12px !important;
        font-style: italic !important;
        margin-top: -10px !important;
        margin-bottom: 15px !important;
        display: block;
    }
    
    .stDetails { border: 1px solid #1c355e !important; background-color: rgba(255, 255, 255, 0.05) !important; border-radius: 8px !important; }
    h3 { font-size: 18px !important; color: #ffffff !important; border-bottom: 2px solid #1c355e; padding-bottom: 5px; margin-bottom: 15px; }
    [data-testid="stFileUploader"] { background-color: #1c355e !important; border: 2px dashed #ffffff !important; border-radius: 10px !important; padding: 10px !important; }
    [data-testid="stFileUploader"] section { color: #ffffff !important; }
    [data-testid="stFileUploader"] button { background-color: #ffffff !important; color: #1c355e !important; border-radius: 6px !important; }
    [data-testid="stFileUploaderFileName"] { color: #ffffff !important; font-weight: bold !important; }
    
    .stButton>button {
        background: linear-gradient(90deg, #1c355e, #8cc63f) !important; color: white !important;
        border-radius: 10px !important; height: 3.8rem !important; font-size: 18px !important;
        font-weight: bold !important; border: none !important; box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important; margin-top: 1.5rem;
    }
    .stButton>button:hover { background: linear-gradient(90deg, #8cc63f, #1c355e) !important; color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CREDENCIALES DE SUPABASE (API REST)
# ==========================================
SUPABASE_URL = "https://ofpqnoinvpumkfifiera.supabase.co"  
SUPABASE_KEY = "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL"        

# ==========================================
# 3. EXTRAER DATA MAESTRA DESDE EXCEL LOCAL
# ==========================================
@st.cache_data(ttl=1800)
def cargar_maestro_local():
    if os.path.exists("IMPORTACION_ANALISIS_PRECIO.xlsx"):
        ruta_excel = "IMPORTACION_ANALISIS_PRECIO.xlsx"  
    else:
        ruta_excel = r"C:\Users\ainteligencia\Desktop\Analisis_Precios\IMPORTACION_ANALISIS_PRECIO.xlsx"  
    
    if not os.path.exists(ruta_excel):
        st.error(f"⚠️ Archivo Excel no encontrado en la ruta: {ruta_excel}")
        return pd.DataFrame()
        
    df_productos = pd.read_excel(ruta_excel, sheet_name="PRODUCTOS")
    df_catalogo = pd.read_excel(ruta_excel, sheet_name="CATALOGO_PRODUCTOS")
    df_categoria = pd.read_excel(ruta_excel, sheet_name="CATEGORIA")

    df_productos.columns = df_productos.columns.str.lower()
    df_catalogo.columns = df_catalogo.columns.str.lower()
    df_categoria.columns = df_categoria.columns.str.lower()

    # Filtro: Activos (-1) y Destacados (-1)
    df_prod_filtrado = df_productos[
        (df_productos["activo"] == -1) & (df_productos["destacado"] == -1)
    ].copy()

    df_prod_filtrado["serial"] = df_prod_filtrado["serial"].astype(str).str.strip()
    df_catalogo["serial"] = df_catalogo["serial"].astype(str).str.strip()

    # Cruce 1: Productos con Categorías
    df_combinado_1 = pd.merge(
        df_prod_filtrado[["serial", "nombre", "categoria_id"]],
        df_categoria[["id", "segmento1"]],
        left_on="categoria_id",
        right_on="id",
        how="left"
    )

    # Cruce 2: Agregar Catálogo
    df_maestro_final = pd.merge(
        df_combinado_1,
        df_catalogo[["serial", "proveedor", "rubro", "sub_categoria"]],
        on="serial",
        how="left"
    )

    df_exportar = df_maestro_final[["serial", "nombre", "segmento1", "proveedor", "rubro", "sub_categoria"]].copy()
    df_exportar = df_exportar.fillna("SIN DATA")
    df_exportar.columns = ["SERIAL", "NOMBRE_PRODUCTO", "SEGMENTO", "PROVEEDOR", "RUBRO", "SUB_CATEGORIA"]
    
    # Limpieza de nombres y ordenación alfabética estricta para optimizar el buscador nativo
    df_exportar["NOMBRE_PRODUCTO"] = df_exportar["NOMBRE_PRODUCTO"].astype(str).str.strip()
    df_exportar = df_exportar.sort_values(by="NOMBRE_PRODUCTO").reset_index(drop=True)
    return df_exportar

df_maestro = cargar_maestro_local()

# ==========================================
# 4. FUNCIÓN: SCRAPING DE TASA BCV
# ==========================================
@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        url = "https://www.bcv.org.ve/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, verify=False, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tasa_element = soup.find(id="dolar")
        if tasa_element:
            tasa_texto = tasa_element.find('strong').text.strip()
            tasa_flotante = float(tasa_texto.replace(',', '.'))
            return tasa_flotante
    except Exception:
        pass
    return 45.50

tasa_bcv = obtener_tasa_bcv()

st.markdown("<h1>JMW CASA DE REPRESENTACIONES</h1>", unsafe_allow_html=True)
st.markdown("<h2>Sistema Inteligente de Monitoreo de Precios</h2>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown(f"""
    <div style='background-color: rgba(255, 255, 255, 0.15); border-left: 4px solid #1c355e; padding: 10px; border-radius: 4px; text-align: center; margin-bottom: 20px;'>
        <span style='font-size: 14px; font-weight: bold;'>Tasa Oficial BCV de Referencia: <b>{tasa_bcv:.2f} Bs/$</b></span>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 5. SECCIÓN: DATOS DE CONTROL
# ==========================================
with st.expander("👤 Persona y Datos de Control"):
    fecha_captura = st.date_input("Fecha de Inspección", datetime.date.today())
    st.markdown("<span class='help-text'>Selecciona la fecha en la que visitas el local.</span>", unsafe_allow_html=True)
    
    vendedor = st.selectbox("Selecciona Vendedor", ["Jad", "Alexander", "Maria", "Juana"], key="vendedor_select")
    st.markdown("<span class='help-text'>Identifícate para registrar la autoría de la captura.</span>", unsafe_allow_html=True)
    
    competencia = st.selectbox("Establecimiento Competidor", ["Competencia1", "Competencia2", "Competencia3", "Competencia4", "Competencia5", "Otro"])
    st.markdown("<span class='help-text'>Selecciona el nombre de la cadena o farmacia que estás auditando.</span>", unsafe_allow_html=True)

# ==========================================
# 6. SECCIÓN: ESCÁNER DE CÓDIGO DE BARRAS
# ==========================================
st.markdown("### 📷 Captura de Código")
img_capture = st.camera_input("Enfoca las barras del producto")
st.markdown("<span class='help-text'>💡 Asegúrate de tener buena luz. Si el escáner no lo detecta automáticamente, pasa directamente a la sección de abajo para ingresar el código de barras o buscar el producto manualmente.</span>", unsafe_allow_html=True)

serial_detectado = ""

if img_capture is not None:
    import cv2
    import numpy as np
    
    file_bytes = np.asarray(bytearray(img_capture.read()), dtype=np.uint8)
    opencv_image = cv2.imdecode(file_bytes, 1)
    
    detector = cv2.barcode.BarcodeDetector()
    ok, decoded_info, decoded_type, corners = detector.detectAndDecode(opencv_image)
    
    if ok and decoded_info:
        serial_detectado = decoded_info[0]
        st.success(f"✅ Identificado: {serial_detectado}")

# ==========================================
# 7. SECCIÓN: DETALLES Y BUSCADOR UNIFICADO EN VIVO
# ==========================================
st.markdown("### 📝 Información del Producto")

serial_final = st.text_input("Código de Barras (Manual o Escaneado)", value=serial_detectado, placeholder="Número de barras")
st.markdown("<span class='help-text'>Si usaste el escáner, se llena solo. Si no, escribe el código numérico de la etiqueta.</span>", unsafe_allow_html=True)

# --- UNIFICACIÓN DEL BUSCADOR NATIVO EN UN SOLO PASO ---
if not df_maestro.empty:
    lista_productos = df_maestro["NOMBRE_PRODUCTO"].tolist()
    
    # Un solo Selectbox: Al hacer clic y escribir, Streamlit busca interactivamente en la lista
    producto_seleccionado = st.selectbox(
        "Seleccione el Producto Homólogo Interno", 
        ["-- Seleccione un producto --"] + lista_productos
    )
    st.markdown("<span class='help-text'>💡 ¡Búsqueda en un paso! Haz clic arriba y empieza a escribir el nombre (ej: mantequilla) para que la lista se filtre sola al instante.</span>", unsafe_allow_html=True)
else:
    producto_seleccionado = "-- Seleccione un producto --"

moneda = st.radio("¿Cómo está marcado el precio en anaquel?", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
st.markdown("<span class='help-text'>Selecciona la moneda real visible en la etiqueta del precio.</span>", unsafe_allow_html=True)

precio_bruto_origen = 0.0
precio_calculado_usd = 0.0

if moneda == "Dólares ($)":
    precio_usd = st.number_input("Precio Marcado en Dólares ($)", min_value=0.0, step=0.01, format="%.2f")
    precio_bruto_origen = precio_usd
    precio_calculado_usd = precio_usd
    st.markdown("<span class='help-text'>Digita el monto exacto en dólares reflejado en el anaquel.</span>", unsafe_allow_html=True)
else:
    precio_bs = st.number_input("Precio Marcado en Bolívares (Bs)", min_value=0.0, step=0.01, format="%.2f")
    precio_bruto_origen = precio_bs
    st.markdown("<span class='help-text'>Digita el monto en Bolívares. El sistema calculará los dólares usando la tasa BCV del día.</span>", unsafe_allow_html=True)
    if precio_bs > 0:
        precio_calculado_usd = precio_bs / tasa_bcv
        st.markdown(f"<p style='color: #8cc63f !important; font-weight: bold; font-size: 14px; text-align: center;'>Conversión Automática: {precio_calculado_usd:.2f} $</p>", unsafe_allow_html=True)

# ==========================================
# 8. SECCIÓN: EVIDENCIA FÍSICA (FOTOS)
# ==========================================
st.markdown("### 🖼️ Evidencia Física (Opcional)")
foto_file = st.file_uploader("Captura o sube una foto del producto/anaquel", type=["jpg", "jpeg", "png"])
st.markdown("<span class='help-text'>Toma una foto clara del producto junto a su precio para respaldar la información.</span>", unsafe_allow_html=True)

# ==========================================
# 9. ENVÍO DE DATOS DIRECTO A TRAVÉS DE API REST
# ==========================================
if st.button("🚀 TRANSMITIR REGISTRO", use_container_width=True):
    if producto_seleccionado == "-- Seleccione un producto --":
        st.error("❌ Error: Debe seleccionar obligatoriamente un producto de la lista.")
    elif precio_calculado_usd <= 0:
        st.error("❌ Error: El monto del precio de la competencia debe ser mayor a cero.")
    else:
        with st.spinner("Sincronizando con JMW Cloud..."):
            try:
                info_prod = df_maestro[df_maestro["NOMBRE_PRODUCTO"] == producto_seleccionado].iloc[0]
                foto_url_final = "SIN FOTO"

                if foto_file is not None:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_archivo_storage = f"{timestamp}_{vendedor}_{info_prod['SERIAL']}.jpg".replace(" ", "_")
                    
                    url_storage = f"{SUPABASE_URL}/storage/v1/object/evidencias/{nombre_archivo_storage}"
                    headers_storage = {
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": foto_file.type
                    }
                    
                    res_storage = requests.post(url_storage, headers=headers_storage, data=foto_file.getvalue())
                    if res_storage.status_code == 200 or res_storage.status_code == 201:
                        foto_url_final = f"{SUPABASE_URL}/storage/v1/object/public/evidencias/{nombre_archivo_storage}"

                payload_sql = {
                    "fecha_captura": str(fecha_captura),
                    "vendedor": vendedor,
                    "competencia": competencia,
                    "serial_escaneado": str(info_prod["SERIAL"]),
                    "nombre_producto": str(info_prod["NOMBRE_PRODUCTO"]),
                    "segmento": str(info_prod["SEGMENTO"]),
                    "proveedor": str(info_prod["PROVEEDOR"]),
                    "rubro": str(info_prod["RUBRO"]),
                    "sub_categoria": str(info_prod["SUB_CATEGORIA"]),
                    "moneda_origen": "USD" if moneda == "Dólares ($)" else "VES",
                    "precio_bruto_origen": float(precio_bruto_origen),
                    "tasa_bcv_momento": float(tasa_bcv),
                    "precio_competencia_usd": float(round(precio_calculado_usd, 2)),
                    "foto_url": foto_url_final
                }

                url_tabla = f"{SUPABASE_URL}/rest/v1/store_check"
                headers_tabla = {
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "apikey": SUPABASE_KEY,
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                }

                res_tabla = requests.post(url_tabla, headers=headers_tabla, json=payload_sql)
                
                if res_tabla.status_code in [200, 201, 204]:
                    st.balloons()
                    st.success("¡Registro de precios y foto almacenados con éxito en la base de datos!")
                else:
                    st.error(f"❌ Error en base de datos ({res_tabla.status_code}): {res_tabla.text}")
                
            except Exception as e:
                st.error(f"❌ Error crítico de red: {str(e)}")