import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Visor Estadístico UNDMO - Bogotá D.C.",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# CONSTANTES Y URL DE LA API
# ---------------------------------------------------------
API_URL = "https://www.datos.gov.co/api/v3/views/226x-qjxq/query.json"

# ---------------------------------------------------------
# FUNCIÓN DE CARGA Y LIMPIEZA EXCLUSIVA DESDE LA API
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def cargar_datos_api():
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            for key in ['data', 'rows', 'result']:
                if key in data and isinstance(data[key], list):
                    df = pd.DataFrame(data[key])
                    break
            else:
                df = pd.DataFrame([data])
        else:
            return None
            
        return df
    except Exception as e:
        st.error(f"Error al conectar con la API de datos.gov.co: {e}")
        return None

def limpiar_datos(df):
    if df is None or df.empty:
        return pd.DataFrame()
    
    cols_a_mantener = [c for c in df.columns if not c.startswith(':')]
    df = df[cols_a_mantener].copy()
    
    columnas_esperadas = {
        'a_o': 'a_o',
        'mes': 'mes',
        'ciudad': 'ciudad',
        'tipo_de_servicio': 'tipo_de_servicio',
        'cantidad_servicios_prestados': 'cantidad_servicios_prestados',
        'se_uso_de_la_fuerza': 'se_uso_de_la_fuerza',
        'cantidad_de_veces_que_se': 'cantidad_de_veces_que_se'
    }
    
    for col in columnas_esperadas.keys():
        if col not in df.columns:
            df[col] = np.nan

    df['a_o'] = df['a_o'].fillna('Desconocido').astype(str).str.strip().str.upper()
    df['mes'] = df['mes'].fillna('DESCONOCIDO').astype(str).str.strip().str.upper()
    df['ciudad'] = df['ciudad'].fillna('NO ESPECIFICADA').astype(str).str.strip().str.upper()
    df['tipo_de_servicio'] = df['tipo_de_servicio'].fillna('NO ESPECIFICADO').astype(str).str.strip().str.upper()
    df['se_uso_de_la_fuerza'] = df['se_uso_de_la_fuerza'].fillna('NO').astype(str).str.strip().str.upper()
    
    df['se_uso_de_la_fuerza'] = df['se_uso_de_la_fuerza'].replace({
        'SI': 'SÍ', 'S': 'SÍ', 'YES': 'SÍ', '1': 'SÍ'
    })
    df['se_uso_de_la_fuerza'] = df['se_uso_de_la_fuerza'].replace({
        'N': 'NO', 'NOT': 'NO', '0': 'NO', '': 'NO'
    })

    df['cantidad_servicios_prestados'] = pd.to_numeric(df['cantidad_servicios_prestados'], errors='coerce').fillna(0)
    df['cantidad_de_veces_que_se'] = pd.to_numeric(df['cantidad_de_veces_que_se'], errors='coerce').fillna(0)

    orden_meses = {
        'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
        'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
    }
    df['mes_num'] = df['mes'].map(orden_meses).fillna(99)
    
    return df

# ---------------------------------------------------------
# INTERFAZ PRINCIPAL - CARGA DE DATOS
# ---------------------------------------------------------
st.title("🛡️ Visor Estadístico e Integral - Actuaciones UNDMO (Bogotá D.C.)")
st.markdown("""
Plataforma pública de análisis de datos sobre las actuaciones de la **Unidad de Diálogo y Mantenimiento del Orden (UNDMO)** 
de la Policía Nacional, construida para facilitar la consulta ciudadana y la transparencia institucional.
""")

with st.spinner("Conectando y descargando datos desde la API oficial..."):
    raw_df = cargar_datos_api()

if raw_df is None or raw_df.empty:
    st.warning("No se pudieron obtener registros desde la API. Por favor, verifica la conexión o intenta recargar la página.")
    st.stop()

df = limpiar_datos(raw_df)

if df.empty:
    st.error("El conjunto de datos procesado está vacío.")
    st.stop()

# ---------------------------------------------------------
# BARRA LATERAL - FILTROS INTERACTIVOS
# ---------------------------------------------------------
st.sidebar.markdown("### 🎛️ Filtros Interactivos")

anios_disponibles = sorted([str(x) for x in df['a_o'].unique() if str(x).lower() != 'nan'])
selected_anios = st.sidebar.multiselect("Año(s)", anios_disponibles, default=anios_disponibles)

df_f = df[df['a_o'].isin(selected_anios)] if selected_anios else df

meses_disponibles = sorted(df_f['mes'].unique().tolist())
selected_meses = st.sidebar.multiselect("Mes(es)", meses_disponibles, default=meses_disponibles)

if selected_meses:
    df_f = df_f[df_f['mes'].isin(selected_meses)]

ciudades_disponibles = sorted(df_f['ciudad'].unique().tolist())
selected_ciudades = st.sidebar.multiselect("Ciudad(es)", ciudades_disponibles, default=ciudades_disponibles)

if selected_ciudades:
    df_f = df_f[df_f['ciudad'].isin(selected_ciudades)]

servicios_disponibles = sorted(df_f['tipo_de_servicio'].unique().tolist())
selected_servicios = st.sidebar.multiselect("Tipo de Servicio", servicios_disponibles, default=servicios_disponibles)

if selected_servicios:
    df_f = df_f[df_f['tipo_de_servicio'].isin(selected_servicios)]

uso_fuerza_opciones = sorted(df_f['se_uso_de_la_fuerza'].unique().tolist())
selected_uso_fuerza = st.sidebar.multiselect("¿Se usó la fuerza?", uso_fuerza_opciones, default=uso_fuerza_opciones)

if selected_uso_fuerza:
    df_f = df_f[df_f['se_uso_de_la_fuerza'].isin(selected_uso_fuerza)]

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Recargar Datos de la API"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------
# CÁLCULOS DE KPIS PRINCIPALES
# ---------------------------------------------------------
total_actuaciones = len(df_f)
suma_servicios_prestados = int(df_f['cantidad_servicios_prestados'].sum())
total_fuerza_usada = int(df_f['cantidad_de_veces_que_se'].sum())

eventos_con_fuerza = len(df_f[df_f['se_uso_de_la_fuerza'] == 'SÍ'])
porcentaje_fuerza = (eventos_con_fuerza / total_actuaciones * 100) if total_actuaciones > 0 else 0.0

# ---------------------------------------------------------
# SECCIÓN DE KPIS
# ---------------------------------------------------------
st.markdown("### 📈 Indicadores Clave de Desempeño (KPIs)")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Registros", f"{total_actuaciones:,}")
col2.metric("Servicios Acumulados", f"{suma_servicios_prestados:,}")
col3.metric("Eventos con Fuerza", f"{eventos_con_fuerza:,}")
col4.metric("% Eventos Uso Fuerza", f"{porcentaje_fuerza:.2f}%")
col5.metric("Total Veces Fuerza Usada", f"{total_fuerza_usada:,}")

if total_actuaciones > 0:
    promedio_servicios = df_f['cantidad_servicios_prestados'].mean()
    if promedio_servicios > 10:
        st.warning(f"⚠️ **Alerta Informativa:** Alta concentración de servicios registrados (Promedio de {promedio_servicios:.1f} servicios por registro bajo los filtros actuales).")

st.markdown("---")

# ---------------------------------------------------------
# PESTAÑAS DE VISUALIZACIÓN Y ANÁLISIS
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Análisis Temporal y Geográfico", 
    "⚙️ Operatividad General", 
    "🔍 Análisis Profundo del Uso de la Fuerza",
    "📋 Tablas Dinámicas", 
    "💡 Resumen Ciudadano e Insights"
])

with tab1:
    st.subheader("Análisis Temporal y Geográfico")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        df_anual = df_f.groupby('a_o')['cantidad_servicios_prestados'].sum().reset_index().sort_values('a_o')
        fig_line_anio = px.line(df_anual, x='a_o', y='cantidad_servicios_prestados', markers=True,
                                title="Evolución de Servicios por Año",
                                labels={'a_o': 'Año', 'cantidad_servicios_prestados': 'Total Servicios'})
        st.plotly_chart(fig_line_anio, use_container_width=True)
        
    with col_b:
        df_mes = df_f.sort_values('mes_num').groupby(['mes', 'mes_num'])['cantidad_servicios_prestados'].sum().reset_index()
        fig_bar_mes = px.bar(df_mes, x='mes', y='cantidad_servicios_prestados',
                             title="Distribución de Servicios por Mes",
                             labels={'mes': 'Mes', 'cantidad_servicios_prestados': 'Total Servicios'},
                             color='cantidad_servicios_prestados', color_continuous_scale='Blues')
        st.plotly_chart(fig_bar_mes, use_container_width=True)

    col_c, col_d = st.columns(2)
    
    with col_c:
        df_heatmap = df_f.pivot_table(index='a_o', columns='mes', values='cantidad_servicios_prestados', aggfunc='sum', fill_value=0)
        fig_heat = px.imshow(df_heatmap, text_auto=True, color_continuous_scale="Viridis",
                             title="Heatmap: Servicios (Año vs Mes)")
        st.plotly_chart(fig_heat, use_container_width=True)
        
    with col_d:
        df_ciudad = df_f.groupby('ciudad')['cantidad_servicios_prestados'].sum().reset_index().sort_values('cantidad_servicios_prestados', ascending=True).tail(10)
        fig_ciudad = px.bar(df_ciudad, x='cantidad_servicios_prestados', y='ciudad', orientation='h',
                            title="Top Ciudades con Mayor Número de Servicios",
                            labels={'cantidad_servicios_prestados': 'Servicios', 'ciudad': 'Ciudad'})
        st.plotly_chart(fig_ciudad, use_container_width=True)

with tab2:
    st.subheader("Análisis de Operatividad General")
    
    col_e, col_f = st.columns(2)
    
    with col_e:
        df_tree = df_f.groupby('tipo_de_servicio')['cantidad_servicios_prestados'].sum().reset_index()
        fig_tree = px.treemap(df_tree, path=['tipo_de_servicio'], values='cantidad_servicios_prestados',
                              title="Treemap: Tipos de Servicio Más Frecuentes")
        st.plotly_chart(fig_tree, use_container_width=True)
        
    with col_f:
        df_pie = df_f['se_uso_de_la_fuerza'].value_counts().reset_index()
        df_pie.columns = ['se_uso_de_la_fuerza', 'conteo']
        fig_pie = px.pie(df_pie, names='se_uso_de_la_fuerza', values='conteo', hole=0.4,
                         title="Proporción general de Eventos con / sin Uso de la Fuerza")
        st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.subheader("🔍 Análisis Específico del Uso de la Fuerza")
    st.markdown("""
    Esta sección examina de manera detallada las estadísticas, recurrencia y comportamiento del uso de la fuerza 
    en las intervenciones reportadas, permitiendo a la ciudadanía comprender en qué contextos o tipos de servicio se requiere dicha medida.
    """)
    
    col_g, col_h = st.columns(2)
    
    with col_g:
        # Frecuencia del uso de la fuerza por tipo de servicio
        df_fuerza_serv = df_f.groupby('tipo_de_servicio')['cantidad_de_veces_que_se'].sum().reset_index().sort_values('cantidad_de_veces_que_se', ascending=False).head(10)
        fig_fuerza_serv = px.bar(df_fuerza_serv, x='tipo_de_servicio', y='cantidad_de_veces_que_se',
                                 title="Intensidad: Veces que se Usó la Fuerza por Tipo de Servicio",
                                 labels={'tipo_de_servicio': 'Tipo de Servicio', 'cantidad_de_veces_que_se': 'Veces Usada la Fuerza'},
                                 color='cantidad_de_veces_que_se', color_continuous_scale='Reds')
        fig_fuerza_serv.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_fuerza_serv, use_container_width=True)
        
    with col_h:
        # Evolución histórica del uso de la fuerza por año
        df_fuerza_anio = df_f.groupby('a_o')['cantidad_de_veces_que_se'].sum().reset_index().sort_values('a_o')
        fig_fuerza_anio = px.line(df_fuerza_anio, x='a_o', y='cantidad_de_veces_que_se', markers=True,
                                  title="Evolución Histórica de la Intensidad del Uso de la Fuerza",
                                  labels={'a_o': 'Año', 'cantidad_de_veces_que_se': 'Frecuencia de Uso'})
        st.plotly_chart(fig_fuerza_anio, use_container_width=True)

    col_i, col_j = st.columns(2)
    
    with col_i:
        # Scatter: relación entre servicios y uso de fuerza
        df_scatter = df_f.groupby(['tipo_de_servicio', 'a_o']).agg({
            'cantidad_servicios_prestados': 'sum',
            'cantidad_de_veces_que_se': 'sum'
        }).reset_index()
        fig_scatter = px.scatter(df_scatter, x='cantidad_servicios_prestados', y='cantidad_de_veces_que_se',
                                 color='tipo_de_servicio', size='cantidad_servicios_prestados',
                                 title="Relación: Servicios Totales vs Intensidad de Fuerza",
                                 labels={'cantidad_servicios_prestados': 'Servicios Prestados', 'cantidad_de_veces_que_se': 'Veces Uso de Fuerza'})
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with col_j:
        # Boxplot: variación del uso de fuerza por tipo de servicio
        fig_box = px.box(df_f, x='tipo_de_servicio', y='cantidad_de_veces_que_se',
                         title="Variación Estadística (Boxplot) de Uso de Fuerza por Servicio",
                         labels={'tipo_de_servicio': 'Tipo de Servicio', 'cantidad_de_veces_que_se': 'Cantidad de Veces'})
        fig_box.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_box, use_container_width=True)

with tab4:
    st.subheader("Tablas Dinámicas y Datos Detallados")
    
    st.markdown("##### 🔍 Consolidado por Ciudad y Tipo de Servicio")
    tabla_dinamica = pd.pivot_table(
        df_f, 
        index=['ciudad', 'tipo_de_servicio'], 
        values=['cantidad_servicios_prestados', 'cantidad_de_veces_que_se'], 
        aggfunc={'cantidad_servicios_prestados': 'sum', 'cantidad_de_veces_que_se': 'sum'}
    ).reset_index()
    
    st.dataframe(tabla_dinamica, use_container_width=True)
    
    st.markdown("##### 📁 Vista Previa de Registros Filtrados")
    st.dataframe(df_f.head(100), use_container_width=True)

with tab5:
    st.subheader("Resumen Ejecutivo e Información Ciudadana")
    
    st.markdown(f"""
    ### 📝 Resumen Ejecutivo para la Ciudadanía
    * **Alcance General:** El sistema registra un total de **{total_actuaciones:,}** intervenciones operativas de la UNDMO, reflejando el despliegue institucional en el periodo analizado.
    * **Volumen de Actividad:** La acumulación de servicios prestados asciende a **{suma_servicios_prestados:,}** atenciones focalizadas en la gestión de convivencia y orden público.
    * **Proporcionalidad del Uso de la Fuerza:** Tan solo un **{porcentaje_fuerza:.2f}%** de los eventos totales reportan el empleo de medidas de fuerza, lo que evidencia que la gran mayoría de las labores se desarrollan mediante protocolos de diálogo, disuasión y contención preventiva.
    """)
    
    st.markdown("""
    ### 📊 Hallazgos e Insights Relevantes
    1. **Enfoque Territorial:** La ciudad de Bogotá D.C. concentra la mayor parte de la actividad operativa y presencia institucional de la unidad.
    2. **Tipología Predominante:** Los servicios de afluencia masiva y acompañamiento a movilizaciones representan el mayor volumen de intervenciones reportadas en los registros oficiales.
    3. **Transparencia Institucional:** Gracias al acceso público a estos datos abiertos, cualquier ciudadano o investigador puede auditar, medir y conocer con exactitud la frecuencia, estacionalidad y el comportamiento de la fuerza pública frente a diferentes situaciones sociales.
    """)

# ---------------------------------------------------------
# PIE DE PÁGINA
# ---------------------------------------------------------
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Plataforma pública de visualización y análisis de actuaciones de la Unidad de Diálogo y Mantenimiento del Orden (UNDMO) - Bogotá D.C.</p>", unsafe_allow_html=True)
