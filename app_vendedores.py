# -*- coding: utf-8 -*-
import streamlit as st
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup
import urllib3
import time
import os
import re
import base64
from io import BytesIO

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="JMW Store Check", layout="centered")

# ==========================================
# 1. CSS COMPLETO
# ==========================================

st.markdown("""
    <style>
    .stApp { background-color: #367c87 !important; }
    h1, .stMarkdown, label, .stCaption, .stTextInput label, .stNumberInput label { color: #ffffff !important; }
    div[data-baseweb="select"], div[data-baseweb="input"], .stNumberInput input, .stTextInput input {
        background-color: #f5f5f5 !important; color: #1a1a1a !important;
        border-radius: 8px !important; border: 1px solid #2a616a !important;
    }
    div[data-baseweb="select"] ul { background-color: #f5f5f5 !important; color: #1a1a1a !important; }
    .st-emotion-cache-16idsys p { font-weight: bold !important; font-size: 16px !important; color: #ffffff !important; }
    .bcv-box { background: #2a616a; color: white; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; border: 1px solid #ffffff; margin-bottom: 20px; }
    .price-value { font-size: 28px; font-weight: 800; color: #2a616a; background: #ffffff; text-align: center; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
    div.stButton > button { background: #2a616a; color: white !important; font-weight: bold; font-size: 18px; border: none; height: 4rem; width: 100%; border-radius: 12px; }
    div.stButton > button:hover { background: #1e4a55; transform: translateY(-2px); cursor: pointer; }
    .producto-card { background-color: #2a616a; padding: 15px; border-radius: 12px; margin: 10px 0; border-left: 5px solid #ffffff; }
    .producto-serial { font-size: 12px; color: #e0e0e0; }
    .producto-nombre { font-size: 16px; font-weight: bold; color: #ffffff; }
    .producto-detalle { font-size: 13px; color: #e0e0e0; margin-top: 8px; }
    .info-badge { display: inline-block; background-color: #ffffff; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; margin-right: 6px; color: #2a616a; }
    .stAlert[data-baseweb="alert"] { background-color: #1e5a3a !important; border-left: 5px solid #00ff88 !important; }
    .stAlert[data-baseweb="alert"] .stMarkdown { color: #ffffff !important; }
    .ultimo-producto { background-color: #2a616a; padding: 12px; border-radius: 10px; border-left: 4px solid #00ff88; margin: 10px 0; color: #ffffff; }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #2a616a; border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: #ffffff; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONFIGURACIÓN DE ZONAS, COMPETIDORES Y AUDITORES
# ==========================================

# Diccionario: ZONA -> COMPETIDORES
COMPETIDORES_POR_ZONA = {
    "Barquisimeto": ["Nuevo Siglo", "Farma Clinica Verde", "San Ignacio"],
    "Tucacas": ["Farmartodo", "Costa Azul"],
    "San Felipe": ["Farma Ganga", "Farmatodo", "Farma Bien", "La Economia"],
    "Aroa": ["Satelnet"],
    "Cabudare": ["Farma Clinica Verde", "San Ignacio"],
    "Chivacoa": ["La Economia", "Xana"],  # <--- AGREGADO XANA
    # NUEVAS ZONAS
    "Punto Fijo - Caja de Agua": ["Super 900", "MI FARMA", "Farmacias DIMAWORD", "TU CARNE"],
    "Punto Fijo - La Puerta": ["Farmatodo", "MI FARMA", "Farmacias DIMAWORD", "Super 900"],
    "Punto Fijo - Santa Irene": ["MI FARMA", "FARMATODO", "Super 900", "FARMACIAS SAAS"],
    "Punto Fijo - Santa Maria": ["MI FARMA", "BAIK", "CASA CHINA", "Super 900"],
    "Coro - Las Calderas": ["BARATILLO", "FARMA OFERTAS", "FARMACIA GUAMACHO", "MEGA OFERTAS"],
    "Coro - Mercado Viejo": ["Rami Centro 2026", "YUSI 900", "MEGA OFERTAS", "FARMA OFERTAS"]
}

# Diccionario: ZONA -> AUDITORES
AUDITORES_POR_ZONA = {
    "Barquisimeto": ["Astrid Carrillo", "Ernesto Sanchez", "Miguel Moly"],
    "Aroa": ["Miguel Moly", "Astrid Martinez"],
    "San Felipe": ["Jose Pinto", "Jorge Loyo"],
    "Tucacas": ["Genesis Quintero", "Katherine Rojas"],
    "Chivacoa": ["Dayerlin Silvira", "Yonathan Mujica"],  # auditores de Chivacoa
    "Cabudare": ["Carmen Lobo"],
    # NUEVAS ZONAS - PUNTO FIJO
    "Punto Fijo - Caja de Agua": ["Jessica Yajure", "Orlando Goitia", "Jesus Garrido"],
    "Punto Fijo - La Puerta": ["Jose Guaricuco", "Andres Guanipa"],
    "Punto Fijo - Santa Irene": ["Carlos Silva", "Marianny Camejo", "Natan Trocoso"],
    "Punto Fijo - Santa Maria": ["Ronny Leal", "Rhonal Hernandez"],
    # NUEVAS ZONAS - CORO
    "Coro - Las Calderas": ["Jose Marquez", "Jose Reyes"],
    "Coro - Mercado Viejo": ["Yenireth Pachano"]
}

# Lista de zonas
ZONAS = list(COMPETIDORES_POR_ZONA.keys())

# ==========================================
# 3. ESTADO DE SESIÓN
# ==========================================

if 'zona' not in st.session_state:
    st.session_state.zona = "Barquisimeto"
if 'vendedor' not in st.session_state:
    st.session_state.vendedor = "Astrid Carrillo"
if 'competencia' not in st.session_state:
    st.session_state.competencia = "Nuevo Siglo"
if 'ultimo_producto' not in st.session_state:
    st.session_state.ultimo_producto = None
if 'ultimo_precio' not in st.session_state:
    st.session_state.ultimo_precio = None
if 'ultimo_competencia' not in st.session_state:
    st.session_state.ultimo_competencia = None
if 'scanner_producto' not in st.session_state:
    st.session_state.scanner_producto = None

# ==========================================
# 4. CARGA DE DATOS DESDE CSV
# ==========================================

@st.cache_data(ttl=3600)
def cargar_maestro():
    try:
        rutas_posibles = ["MAESTRO_SUPABASE.csv", "./MAESTRO_SUPABASE.csv", "../MAESTRO_SUPABASE.csv"]
        csv_path = None
        for ruta in rutas_posibles:
            if os.path.exists(ruta):
                csv_path = ruta
                break
        
        if csv_path is None:
            st.error("❌ No se encuentra MAESTRO_SUPABASE.csv")
            return pd.DataFrame()
        
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        df.columns = [str(c).lower().strip() for c in df.columns]
        df["busqueda_texto"] = df["nombre_producto"].astype(str) + " " + df["serial"].astype(str)
        df["nombre_vista"] = df["nombre_producto"].apply(lambda x: x.title() if isinstance(x, str) else str(x))
        
        st.success(f"✅ Productos destacados cargados: {len(df):,}")
        return df
    except Exception as e:
        st.error(f"❌ Error cargando MAESTRO_SUPABASE.csv: {e}")
        return pd.DataFrame()

# ==========================================
# 5. FUNCIONES AUXILIARES
# ==========================================

def formatear_producto(fila):
    nombre = fila.get('nombre_vista', fila.get('nombre_producto', 'N/A'))
    serial = fila.get('serial', 'N/A')
    segmento = fila.get('segmento', 'No especificado')
    proveedor = fila.get('proveedor', 'No especificado')
    rubro = fila.get('rubro', 'No especificado')
    sub_categoria = fila.get('sub_categoria', 'No especificado')
    
    return f"""
    <div class='producto-card'>
        <div class='producto-nombre'>📦 {nombre}</div>
        <div class='producto-serial'>🔢 Serial: {serial}</div>
        <div class='producto-detalle'>
            <span class='info-badge'>📂 {segmento}</span>
            <span class='info-badge'>🏭 {proveedor}</span>
            <span class='info-badge'>📚 {rubro}</span>
            <span class='info-badge'>📌 {sub_categoria}</span>
        </div>
    </div>
    """

def obtener_datos_producto(df_maestro, prod_sel):
    if prod_sel is None:
        return {}
    fila = df_maestro[df_maestro["nombre_producto"] == prod_sel]
    if fila.empty:
        return {}
    fila = fila.iloc[0]
    return {
        "serial": str(fila.get("serial", "N/A")),
        "segmento": str(fila.get("segmento", "No especificado")),
        "proveedor": str(fila.get("proveedor", "No especificado")),
        "rubro": str(fila.get("rubro", "No especificado")),
        "sub_categoria": str(fila.get("sub_categoria", "No especificado"))
    }

# ==========================================
# 6. CARGA PRINCIPAL
# ==========================================

df_maestro = cargar_maestro()
if df_maestro.empty:
    st.stop()

st.markdown("<h1>📊 JMW Store Check</h1>", unsafe_allow_html=True)

# ==========================================
# 7. TASA BCV
# ==========================================

try:
    res = requests.get("https://www.bcv.org.ve/", timeout=5, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    dolar_element = soup.find(id="dolar")
    if dolar_element:
        tasa = float(dolar_element.find('strong').text.strip().replace(',', '.'))
    else:
        tasa = 530.50
except:
    tasa = 530.50

st.markdown(f"<div class='bcv-box'>🇻🇪 Tasa BCV: {tasa:.2f} Bs/$</div>", unsafe_allow_html=True)

# ==========================================
# 8. AUDITOR, ZONA Y ESTABLECIMIENTO
# ==========================================

with st.expander("👤 1. Auditor, Zona y Establecimiento", expanded=True):
    # Seleccionar ZONA (esto filtra competidores y auditores)
    zona = st.selectbox("📍 Zona", ZONAS, key="zona_selector")
    st.session_state.zona = zona
    
    # Seleccionar COMPETIDOR (filtrado por zona)
    competidores_disponibles = COMPETIDORES_POR_ZONA.get(zona, [])
    competencia = st.selectbox("🏪 Establecimiento", competidores_disponibles, key="competencia_selector")
    st.session_state.competencia = competencia
    
    # Seleccionar AUDITOR (filtrado por zona)
    auditores_disponibles = AUDITORES_POR_ZONA.get(zona, [])
    vendedor = st.selectbox("👤 Auditor", auditores_disponibles, key="auditor_selector")
    st.session_state.vendedor = vendedor

# ==========================================
# 9. EVIDENCIA (CÁMARA / ESCÁNER)
# ==========================================

with st.expander("📷 2. Escáner y Evidencia", expanded=True):
    tipo_foto = st.radio("Método de captura", ["📸 Cámara", "📁 Archivo"], horizontal=True)
    
    if tipo_foto == "📸 Cámara":
        foto = st.camera_input("📸 Capturar foto del precio", key="camera_input")
    else:
        foto = st.file_uploader("📁 Subir foto del precio", type=['jpg', 'png', 'jpeg'], key="file_input")
    
    if foto:
        st.image(foto, caption="Foto del precio", width=200)
    
    st.markdown("---")
    st.markdown("### 🔍 Escáner de código de barras")
    st.caption("📌 Usa un escáner USB/BT o escribe manualmente el código")
    
    serial_manual = st.text_input("Código de barras", placeholder="Escanea o escribe el código aquí...", key="serial_input")
    
    if serial_manual:
        df_busqueda_serial = df_maestro[df_maestro['serial'].astype(str).str.contains(serial_manual, case=False, na=False)]
        if not df_busqueda_serial.empty:
            producto_encontrado = df_busqueda_serial.iloc[0]['nombre_producto']
            st.session_state.scanner_producto = producto_encontrado
            st.success(f"✅ Producto encontrado: {df_busqueda_serial.iloc[0]['nombre_vista'][:60]}...")
        else:
            st.session_state.scanner_producto = None
            st.warning("⚠️ Producto no encontrado. Busca manualmente abajo.")

# ==========================================
# 10. SELECCIÓN DE PRODUCTO
# ==========================================

with st.expander("📦 3. Producto y Precio", expanded=True):
    st.markdown("### 🔎 Buscar producto")
    
    prod_sel = None
    buscar_por = st.radio("Buscar por:", ["Nombre", "Serial"], horizontal=True)
    
    if buscar_por == "Nombre":
        busqueda = st.text_input("Nombre del producto:", placeholder="Escribe el nombre...", key="busqueda_nombre")
        if busqueda:
            df_filtrado = df_maestro[df_maestro['nombre_producto'].str.contains(busqueda, case=False, na=False)]
        else:
            df_filtrado = df_maestro
    else:
        busqueda_serial = st.text_input("Serial:", placeholder="Escribe o escanea el código...", key="busqueda_serial")
        if busqueda_serial:
            df_filtrado = df_maestro[df_maestro['serial'].astype(str).str.contains(busqueda_serial, case=False, na=False)]
        else:
            df_filtrado = df_maestro
    
    if st.session_state.scanner_producto and st.session_state.scanner_producto in df_filtrado['nombre_producto'].values:
        prod_sel = st.session_state.scanner_producto
        st.info(f"📌 Producto preseleccionado por escáner: {prod_sel[:60]}...")
    
    if not df_filtrado.empty:
        opciones_productos = []
        opciones_dict = {}
        for idx, row in df_filtrado.iterrows():
            nombre_vista = row['nombre_vista']
            serial = row['serial']
            if len(nombre_vista) > 70:
                nombre_vista = nombre_vista[:67] + "..."
            etiqueta = f"{nombre_vista} | Serial: {serial}"
            opciones_productos.append(etiqueta)
            opciones_dict[etiqueta] = row['nombre_producto']
        
        if prod_sel:
            for etiqueta, nombre in opciones_dict.items():
                if nombre == prod_sel:
                    default_idx = opciones_productos.index(etiqueta)
                    break
            else:
                default_idx = None
        else:
            default_idx = None
        
        prod_sel_etiqueta = st.selectbox("Seleccionar producto", opciones_productos, index=default_idx, key="prod_sel_box")
        if prod_sel_etiqueta:
            prod_sel = opciones_dict[prod_sel_etiqueta]
    else:
        st.warning("⚠️ No se encontraron productos")
        prod_sel = None
    
    if prod_sel:
        datos_producto = obtener_datos_producto(df_maestro, prod_sel)
        st.markdown(formatear_producto(datos_producto), unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 💲 Precio")
    
    col_toggle, col_precio = st.columns([1, 2])
    with col_toggle:
        es_usd = st.toggle("USD / VES", value=True, key="moneda_toggle")
        if es_usd:
            st.caption("💵 Precio en **Dólares**")
        else:
            st.caption("🇻🇪 Precio en **Bolívares**")
    
    with col_precio:
        precio = st.number_input("Precio marcado", min_value=0.0, step=0.01, format="%.2f", key="precio_input")
    
    if es_usd:
        val_usd = precio
        moneda_origen = "USD"
    else:
        val_usd = precio / tasa if tasa > 0 else 0
        moneda_origen = "VES"
    
    st.markdown(f"<div class='price-value'>💲 VALOR: {val_usd:.2f} USD</div>", unsafe_allow_html=True)
    
    if not es_usd and precio > 0:
        st.caption(f"💱 Conversión: {precio:,.2f} Bs ÷ {tasa:.2f} = {val_usd:.2f} USD")

# ==========================================
# 11. TRANSMISIÓN A SUPABASE
# ==========================================

st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([2, 1.5, 2])
with col_btn2:
    enviar = st.button("🚀 TRANSMITIR REGISTRO", use_container_width=True)

if enviar:
    if not prod_sel:
        st.error("⚠️ ¡Debes seleccionar un producto!")
    elif precio <= 0:
        st.error("⚠️ ¡Debes ingresar un precio válido!")
    else:
        datos_producto = obtener_datos_producto(df_maestro, prod_sel)
        
        foto_base64 = None
        if foto:
            try:
                bytes_data = foto.getvalue()
                foto_base64 = base64.b64encode(bytes_data).decode('utf-8')
            except:
                foto_base64 = None
        
        payload = {
            "fecha_captura": str(datetime.date.today()),
            "vendedor": st.session_state.vendedor,
            "competencia": st.session_state.competencia,
            "zona": st.session_state.zona,
            "serial_escaneado": serial_manual if serial_manual else datos_producto.get("serial", "N/A"),
            "nombre_producto": str(prod_sel),
            "segmento": datos_producto.get("segmento", "No especificado"),
            "proveedor": datos_producto.get("proveedor", "No especificado"),
            "rubro": datos_producto.get("rubro", "No especificado"),
            "sub_categoria": datos_producto.get("sub_categoria", "No especificado"),
            "moneda_origen": moneda_origen,
            "precio_bruto_origen": float(precio),
            "tasa_bcv_momento": float(tasa),
            "precio_competencia_usd": float(val_usd),
            "foto_url": "FOTO_ADJUNTA" if foto else "SIN FOTO",
            "foto_base64": foto_base64
        }
        
        with st.expander("📋 Resumen del registro", expanded=True):
            st.markdown(f"""
            - **📍 Zona:** {payload['zona']}
            - **👤 Auditor:** {payload['vendedor']}
            - **🏪 Competencia:** {payload['competencia']}
            - **📦 Producto:** {payload['nombre_producto'][:80]}...
            - **🔢 Serial:** {payload['serial_escaneado']}
            - **💲 Precio:** {payload['precio_competencia_usd']:.2f} USD
            - **📂 Segmento:** {payload['segmento']}
            - **🏭 Proveedor:** {payload['proveedor']}
            - **📚 Rubro:** {payload['rubro']}
            - **📌 Subcategoría:** {payload['sub_categoria']}
            """)
        
        headers = {
            "apikey": "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL",
            "Authorization": "Bearer sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL",
            "Content-Type": "application/json"
        }
        
        with st.spinner("Enviando registro a Supabase..."):
            try:
                payload_clean = {k: v for k, v in payload.items() if k != "foto_base64"}
                
                res = requests.post(
                    "https://ofpqnoinvpumkfifiera.supabase.co/rest/v1/store_check",
                    headers=headers,
                    json=payload_clean,
                    timeout=15
                )
                
                if res.status_code in [200, 201, 204]:
                    st.markdown("""
                    <div style="background-color: #1e5a3a; border-left: 5px solid #00ff88; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <span style="display: inline-flex; align-items: center; justify-content: center; background-color: #00ff88; color: #1e5a3a; border-radius: 50%; width: 24px; height: 24px; font-size: 14px; font-weight: bold; margin-right: 10px;">✓</span>
                        <span style="color: #ffffff; font-weight: bold;">¡Registro enviado exitosamente a Supabase!</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.session_state.ultimo_producto = prod_sel
                    st.session_state.ultimo_precio = val_usd
                    st.session_state.ultimo_competencia = st.session_state.competencia
                    st.session_state.scanner_producto = None
                    
                    try:
                        backup_file = "registros_backup.csv"
                        df_nuevo = pd.DataFrame([payload_clean])
                        if os.path.exists(backup_file):
                            df_existente = pd.read_csv(backup_file)
                            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
                        else:
                            df_final = df_nuevo
                        df_final.to_csv(backup_file, index=False, encoding="utf-8-sig")
                    except:
                        pass
                    
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ Error en Supabase: {res.text}")
                    pendiente_file = "registros_pendientes.csv"
                    df_nuevo = pd.DataFrame([payload_clean])
                    if os.path.exists(pendiente_file):
                        df_existente = pd.read_csv(pendiente_file)
                        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
                    else:
                        df_final = df_nuevo
                    df_final.to_csv(pendiente_file, index=False, encoding="utf-8-sig")
                    st.warning("⚠️ Registro guardado localmente")
                    
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")
                pendiente_file = "registros_pendientes.csv"
                df_nuevo = pd.DataFrame([payload_clean])
                if os.path.exists(pendiente_file):
                    df_existente = pd.read_csv(pendiente_file)
                    df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
                else:
                    df_final = df_nuevo
                df_final.to_csv(pendiente_file, index=False, encoding="utf-8-sig")
                st.success("✅ Registro guardado localmente")

# ==========================================
# 12. MOSTRAR ÚLTIMO REGISTRO
# ==========================================

if st.session_state.ultimo_producto:
    with st.expander("📌 Mi último registro", expanded=False):
        st.markdown(f"""
        <div class='ultimo-producto'>
        <strong>📍 Zona:</strong> {st.session_state.zona}<br>
        <strong>👤 Auditor:</strong> {st.session_state.vendedor}<br>
        <strong>🏪 Competencia:</strong> {st.session_state.ultimo_competencia}<br>
        <strong>📦 Producto:</strong> {st.session_state.ultimo_producto[:80]}...<br>
        <strong>💲 Precio:</strong> {st.session_state.ultimo_precio:.2f} USD
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 13. REGISTROS PENDIENTES
# ==========================================

pendiente_file = "registros_pendientes.csv"
if os.path.exists(pendiente_file):
    with st.expander("⏳ Mis registros pendientes", expanded=False):
        df_pendientes = pd.read_csv(pendiente_file)
        if 'vendedor' in df_pendientes.columns:
            df_mis_pendientes = df_pendientes[df_pendientes['vendedor'] == st.session_state.vendedor]
            if not df_mis_pendientes.empty:
                st.warning(f"📋 {len(df_mis_pendientes)} registros pendientes")
                st.dataframe(df_mis_pendientes[['fecha_captura', 'competencia', 'nombre_producto', 'precio_competencia_usd']])
            else:
                st.info("No tienes registros pendientes")
