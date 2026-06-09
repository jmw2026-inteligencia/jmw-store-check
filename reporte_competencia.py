# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Reporte de Competencia - FarmaSI", layout="wide")

# ==========================================
# 1. CONFIGURACIÓN DE SUPABASE
# ==========================================

SUPABASE_URL = "https://ofpqnoinvpumkfifiera.supabase.co"
SUPABASE_KEY = "sb_publishable_ZSFE2QL0Bh1VwPHq2lEHlw_ENCm5FfL"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ==========================================
# 2. ESTILOS (con fondo oscuro para filtros)
# ==========================================

st.markdown("""
    <style>
    .stApp { background-color: #0d2a30 !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: bold !important; }
    .stMarkdown, p, span, div { color: #ffffff !important; }
    
    /* Labels de filtros - BLANCOS */
    .stSelectbox label, .stDateInput label, .stMultiSelect label, .stCheckbox label {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    /* Filtros (selectores) - FONDO OSCURO, TEXTO BLANCO */
    div[data-baseweb="select"] > div {
        background-color: #1e4a55 !important;
        border-radius: 8px !important;
        border: 1px solid #ffaa00 !important;
    }
    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }
    div[data-baseweb="select"] svg {
        fill: #ffffff !important;
    }
    
    /* Inputs de fecha - FONDO OSCURO, TEXTO BLANCO */
    .stDateInput input {
        background-color: #1e4a55 !important;
        color: #ffffff !important;
        border: 1px solid #ffaa00 !important;
        border-radius: 8px !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0a1f24 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    
    /* Tarjetas de métricas */
    .metric-card {
        background-color: #1e4a55; padding: 20px; border-radius: 12px; text-align: center;
        border-bottom: 3px solid #ffaa00; margin: 10px 0;
    }
    .metric-value { font-size: 28px; font-weight: bold; color: #ffaa00; word-break: break-word; }
    .metric-label { font-size: 14px; color: #ffffff; }
    
    /* Tablas */
    .stDataFrame { background-color: #1e4a55 !important; border-radius: 10px; }
    .stDataFrame th { background-color: #0d2a30 !important; color: #ffaa00 !important; }
    .stDataFrame td { color: #ffffff !important; }
    
    /* Botón de descarga */
    .stDownloadButton button {
        background: linear-gradient(90deg, #ffaa00, #ffcc44) !important;
        color: #0d2a30 !important; font-weight: bold !important; font-size: 18px !important;
        padding: 12px 24px !important; border: none !important; border-radius: 12px !important;
        width: 100% !important; box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
    }
    .stDownloadButton button:hover {
        background: linear-gradient(90deg, #ffcc44, #ffdd88) !important;
        transform: translateY(-2px) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FUNCIONES DE CARGA DE DATOS
# ==========================================

@st.cache_data(ttl=300)
def cargar_datos_supabase():
    try:
        url = f"{SUPABASE_URL}/rest/v1/store_check"
        params = {"select": "*", "order": "fecha_captura.desc"}
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error(f"Error: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

def procesar_datos(df):
    if df.empty:
        return df
    
    if 'fecha_captura' in df.columns:
        df['fecha_captura'] = pd.to_datetime(df['fecha_captura'])
        df['fecha'] = df['fecha_captura'].dt.date
        df['dia_semana'] = df['fecha_captura'].dt.day_name()
        dias_es = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 
                   'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
        df['dia_semana_es'] = df['dia_semana'].map(dias_es)
    
    renombrar = {
        'vendedor': 'Auditor',
        'competencia': 'Competencia',
        'zona': 'Zona',
        'nombre_producto': 'Producto',
        'precio_competencia_usd': 'Precio USD',
        'fecha': 'Fecha',
        'dia_semana_es': 'Día Semana'
    }
    df = df.rename(columns={k: v for k, v in renombrar.items() if k in df.columns})
    return df

# ==========================================
# 4. MÉTRICAS (3 tarjetas)
# ==========================================

def mostrar_metricas(df):
    col1, col2, col3 = st.columns(3)
    
    total_skus = df['Producto'].nunique() if 'Producto' in df.columns else 0
    
    if 'Zona' in df.columns and not df.empty:
        zona_top = df['Zona'].value_counts().index[0]
        zona_count = df['Zona'].value_counts().iloc[0]
        zona_text = f"{zona_top} ({zona_count})"
    else:
        zona_text = "-"
    
    if 'Auditor' in df.columns and not df.empty:
        auditor_top = df['Auditor'].value_counts().index[0]
        auditor_count = df['Auditor'].value_counts().iloc[0]
        if len(auditor_top) > 25:
            auditor_top = auditor_top[:22] + "..."
        auditor_text = f"{auditor_top} ({auditor_count})"
    else:
        auditor_text = "-"
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{total_skus:,}</div>
            <div class='metric-label'>SKU Únicos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{zona_text}</div>
            <div class='metric-label'>🏆 Zona con más registros</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{auditor_text}</div>
            <div class='metric-label'>🏆 Auditor con más registros</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 5. GRÁFICOS
# ==========================================

def grafico_registros_por_dia(df):
    if 'Fecha' not in df.columns:
        return
    registros_dia = df.groupby('Fecha').size().reset_index(name='Registros')
    fig = px.line(registros_dia, x='Fecha', y='Registros', 
                  title='📈 Registros por Día',
                  labels={'Fecha': 'Fecha', 'Registros': 'Cantidad de Registros'})
    fig.update_traces(line=dict(color='#ffaa00', width=3), mode='lines+markers', marker=dict(size=8, color='#ffaa00'))
    fig.update_layout(paper_bgcolor='#0d2a30', plot_bgcolor='#0d2a30', 
                      font=dict(color='white', size=12), title_font=dict(color='white', size=16))
    fig.update_xaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65', dtick="D1")
    fig.update_yaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65', 
                     tickformat='d', tick0=0, dtick=1)
    st.plotly_chart(fig, use_container_width=True)

def grafico_top_auditores(df):
    if 'Auditor' not in df.columns:
        return
    top = df['Auditor'].value_counts().head(10).reset_index()
    top.columns = ['Auditor', 'Registros']
    top = top.sort_values('Registros', ascending=True)
    top['Auditor'] = top['Auditor'].apply(lambda x: x[:30] + "..." if len(x) > 30 else x)
    fig = px.bar(top, x='Registros', y='Auditor', orientation='h',
                 title='🏆 Top 10 Auditores por Cantidad de Registros',
                 labels={'Registros': 'Cantidad de Registros', 'Auditor': 'Auditor'},
                 color='Registros', color_continuous_scale='Oranges',
                 text='Registros')
    fig.update_traces(texttemplate='%{x}', textposition='outside', 
                      textfont=dict(color='white', size=12, weight='bold'))
    fig.update_layout(paper_bgcolor='#0d2a30', plot_bgcolor='#0d2a30', 
                      font=dict(color='white', size=12), title_font=dict(color='white', size=16),
                      height=450)
    fig.update_xaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65',
                     tickformat='d', tick0=0, dtick=1)
    fig.update_yaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65')
    st.plotly_chart(fig, use_container_width=True)

def grafico_registros_por_zona(df):
    """Gráfico de barras vertical - Registros por Zona"""
    if 'Zona' not in df.columns:
        return
    zona_counts = df.groupby('Zona').size().reset_index(name='Registros')
    zona_counts = zona_counts.sort_values('Registros', ascending=False)
    fig = px.bar(zona_counts, x='Zona', y='Registros',
                 title='📍 Registros por Zona',
                 labels={'Zona': 'Zona', 'Registros': 'Cantidad de Registros'},
                 color='Registros', color_continuous_scale='Oranges',
                 text='Registros')
    fig.update_traces(texttemplate='%{y}', textposition='outside', 
                      textfont=dict(color='white', size=11, weight='bold'))
    fig.update_layout(paper_bgcolor='#0d2a30', plot_bgcolor='#0d2a30', 
                      font=dict(color='white', size=12), title_font=dict(color='white', size=16),
                      xaxis_tickangle=-45)
    fig.update_xaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65')
    fig.update_yaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65',
                     tickformat='d', tick0=0, dtick=1)
    st.plotly_chart(fig, use_container_width=True)

def grafico_registros_por_competencia(df):
    """Gráfico de barras vertical - Registros por Competencia (orden descendente)"""
    if 'Competencia' not in df.columns:
        return
    comp_counts = df.groupby('Competencia').size().reset_index(name='Registros')
    comp_counts = comp_counts.sort_values('Registros', ascending=False).head(15)
    fig = px.bar(comp_counts, x='Competencia', y='Registros',
                 title='🏪 Registros por Competencia',
                 labels={'Competencia': 'Competencia', 'Registros': 'Cantidad de Registros'},
                 color='Registros', color_continuous_scale='Oranges',
                 text='Registros')
    fig.update_traces(texttemplate='%{y}', textposition='outside', 
                      textfont=dict(color='white', size=10, weight='bold'))
    fig.update_layout(paper_bgcolor='#0d2a30', plot_bgcolor='#0d2a30', 
                      font=dict(color='white', size=12), title_font=dict(color='white', size=16),
                      height=500, xaxis_tickangle=-45)
    fig.update_xaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65')
    fig.update_yaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65',
                     tickformat='d', tick0=0, dtick=1)
    st.plotly_chart(fig, use_container_width=True)

def grafico_top_sku_precio(df):
    if 'Producto' not in df.columns or 'Precio USD' not in df.columns:
        return
    top_precio = df.groupby('Producto')['Precio USD'].mean().sort_values(ascending=False).head(10).reset_index()
    top_precio.columns = ['Producto', 'Precio Promedio USD']
    top_precio = top_precio.sort_values('Precio Promedio USD', ascending=True)
    top_precio['Producto'] = top_precio['Producto'].apply(lambda x: x[:45] + "..." if len(x) > 45 else x)
    
    fig = px.bar(top_precio, x='Precio Promedio USD', y='Producto', orientation='h',
                 title='💰 Top 10 SKU con Mayor Precio Promedio (USD)',
                 labels={'Precio Promedio USD': 'Precio Promedio (USD)', 'Producto': 'Producto'},
                 color='Precio Promedio USD', color_continuous_scale='Oranges',
                 text='Precio Promedio USD')
    fig.update_traces(texttemplate='%{x:.2f} USD', textposition='outside', 
                      textfont=dict(color='white', size=11, weight='bold'))
    fig.update_layout(paper_bgcolor='#0d2a30', plot_bgcolor='#0d2a30', 
                      font=dict(color='white', size=12), title_font=dict(color='white', size=16),
                      height=550)
    fig.update_xaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65',
                     tickprefix='$ ', tickformat='.2f')
    fig.update_yaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65')
    st.plotly_chart(fig, use_container_width=True)

def grafico_registros_por_dia_semana(df):
    if 'Día Semana' not in df.columns:
        return
    orden = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_counts = df.groupby('Día Semana').size().reset_index(name='Registros')
    fig = px.bar(dia_counts, x='Día Semana', y='Registros',
                 title='📅 Distribución por Día de la Semana',
                 labels={'Día Semana': 'Día', 'Registros': 'Cantidad de Registros'},
                 category_orders={'Día Semana': orden},
                 color='Registros', color_continuous_scale='Oranges',
                 text='Registros')
    fig.update_traces(texttemplate='%{y}', textposition='outside', 
                      textfont=dict(color='white', size=12, weight='bold'))
    fig.update_layout(paper_bgcolor='#0d2a30', plot_bgcolor='#0d2a30', 
                      font=dict(color='white', size=12), title_font=dict(color='white', size=16))
    fig.update_xaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65')
    fig.update_yaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65',
                     tickformat='d', tick0=0, dtick=1)
    st.plotly_chart(fig, use_container_width=True)

def grafico_evolucion_sku(df):
    if 'Fecha' not in df.columns or 'Producto' not in df.columns:
        return
    sku_dia = df.groupby('Fecha')['Producto'].nunique().reset_index(name='SKU Únicos')
    fig = px.line(sku_dia, x='Fecha', y='SKU Únicos',
                  title='📊 Evolución de SKU Únicos por Día',
                  labels={'Fecha': 'Fecha', 'SKU Únicos': 'Cantidad de SKU'})
    fig.update_traces(line=dict(color='#ffaa00', width=3), mode='lines+markers', marker=dict(size=8, color='#ffaa00'))
    fig.update_layout(paper_bgcolor='#0d2a30', plot_bgcolor='#0d2a30', 
                      font=dict(color='white', size=12), title_font=dict(color='white', size=16))
    fig.update_xaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65', dtick="D1")
    fig.update_yaxes(title_font_color='white', tickfont_color='white', gridcolor='#2a5a65',
                     tickformat='d', tick0=0, dtick=1)
    st.plotly_chart(fig, use_container_width=True)

def tabla_detallada(df):
    st.subheader("📋 Detalle de Registros")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        auditores = ['Todos'] + sorted(df['Auditor'].unique().tolist()) if 'Auditor' in df.columns else ['Todos']
        filtro_auditor = st.selectbox("👤 Filtrar por Auditor", auditores, key="filtro_auditor")
    with col2:
        zonas = ['Todas'] + sorted(df['Zona'].unique().tolist()) if 'Zona' in df.columns else ['Todas']
        filtro_zona = st.selectbox("📍 Filtrar por Zona", zonas, key="filtro_zona")
    with col3:
        competencias = ['Todas'] + sorted(df['Competencia'].unique().tolist()) if 'Competencia' in df.columns else ['Todas']
        filtro_competencia = st.selectbox("🏪 Filtrar por Competencia", competencias, key="filtro_competencia")
    
    df_filtrado = df.copy()
    if filtro_auditor != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Auditor'] == filtro_auditor]
    if filtro_zona != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Zona'] == filtro_zona]
    if filtro_competencia != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Competencia'] == filtro_competencia]
    
    columnas_mostrar = ['Fecha', 'Día Semana', 'Zona', 'Auditor', 'Competencia', 'Producto']
    if 'Precio USD' in df_filtrado.columns:
        columnas_mostrar.append('Precio USD')
    
    columnas_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
    st.dataframe(df_filtrado[columnas_existentes], use_container_width=True, height=400)
    
    st.caption(f"📌 Mostrando {len(df_filtrado)} registros de {len(df)} totales")

def selector_fechas(df):
    st.sidebar.header("📅 Filtros de Fecha")
    
    if 'fecha_captura' in df.columns and not df.empty:
        fecha_min = df['fecha_captura'].min().date()
        fecha_max = df['fecha_captura'].max().date()
        
        fecha_inicio = st.sidebar.date_input("📅 Desde", fecha_min, min_value=fecha_min, max_value=fecha_max)
        fecha_fin = st.sidebar.date_input("📅 Hasta", fecha_max, min_value=fecha_min, max_value=fecha_max)
        
        return df[(df['fecha_captura'].dt.date >= fecha_inicio) & (df['fecha_captura'].dt.date <= fecha_fin)]
    return df

# ==========================================
# 6. MAIN
# ==========================================

def main():
    st.title("📊 Reporte de Competencia - FarmaSI")
    st.markdown("---")
    
    with st.spinner("🔄 Cargando datos..."):
        df_raw = cargar_datos_supabase()
    
    if df_raw.empty:
        st.warning("⚠️ No hay datos disponibles.")
        return
    
    df = procesar_datos(df_raw)
    
    if 'fecha_captura' in df_raw.columns:
        ultima_act = df_raw['fecha_captura'].max()
        st.sidebar.success(f"✅ Última actualización: {ultima_act.strftime('%d/%m/%Y %H:%M:%S')}")
    
    df_filtrado = selector_fechas(df_raw)
    df_filtrado = procesar_datos(df_filtrado)
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Datos actualizados cada 5 minutos")
    
    mostrar_metricas(df_filtrado)
    
    col1, col2 = st.columns(2)
    with col1:
        grafico_registros_por_dia(df_filtrado)
    with col2:
        grafico_top_auditores(df_filtrado)
    
    col3, col4 = st.columns(2)
    with col3:
        grafico_registros_por_zona(df_filtrado)
    with col4:
        grafico_top_sku_precio(df_filtrado)
    
    col5, col6 = st.columns(2)
    with col5:
        grafico_registros_por_competencia(df_filtrado)
    with col6:
        grafico_registros_por_dia_semana(df_filtrado)
    
    grafico_evolucion_sku(df_filtrado)
    
    st.markdown("---")
    tabla_detallada(df_filtrado)
    
    csv = df_filtrado.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 DESCARGAR REPORTE (CSV)",
        data=csv,
        file_name=f"reporte_competencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

if __name__ == "__main__":
    main()
