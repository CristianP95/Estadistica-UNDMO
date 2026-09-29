import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Visor Analítico UDMO - Bogotá D.C.",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS personalizados para un look ejecutivo ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .metric-card {
        background-color: #1e2130;
        border: 1px solid #2d3142;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .alert-box {
        background-color: #3b1414;
        border-left: 5px solid #ff4b4b;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Función de Carga y Limpieza de Datos ---
@st.cache_data(ttl=3600)
def load_and_clean_data(source_type="API", uploaded_file=None):
    df = pd.DataFrame()
    
    if source_type == "API":
        url = "https://www.datos.gov.co/api/v3/views/226x-qjxq/query.json"
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                # Dependiendo de cómo devuelva el JSON la API de Socrata
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict) and 'data' in data:
                    df = pd.DataFrame(data['data'])
                else:
                    df = pd.DataFrame(data)
            else:
                st.error(f"Error al conectar con la API oficial. Código: {response.status_code}")
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Error de conexión con la API: {e}")
            return pd.DataFrame()
            
    elif source_type == "Archivo Local" and uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)

    if df.empty:
        return df

    # Limpieza de columnas técnicas de Socrata si existen
    cols_to_drop = [c for c in df.columns if c.startswith(':')]
    df = df.drop(columns=cols_to_drop, errors='ignore')

    # Mapeo de nombres esperados
    expected_cols = {
        'a_o': 'a_o',
        'mes': 'mes',
        'ciudad': 'ciudad',
        'tipo_de_servicio': 'tipo_de_servicio',
        'cantidad_servicios_prestados': 'cantidad_servicios_prestados',
        'se_uso_de_la_fuerza': 'se_uso_de_la_fuerza',
        'cantidad_de_veces_que_se': 'cantidad_de_veces_que_se'
    }
    
    # Asegurar que existan o renombrar si hay variaciones
    for col in expected_cols:
        if col not in df.columns:
            # Buscar coincidencias parciales si las hubiera
            match = [c for c in df.columns if col in c.lower()]
            if match:
                df = df.rename(columns={match[0]: col})

    # Normalización y Tipos de Datos
    if 'a_o' in df.columns:
        df['a_o'] = df['a_o'].astype(str).str.strip().str.upper()
    else:
        df['a_o'] = "DESCONOCIDO"

    if 'mes' in df.columns:
        df['mes'] = df['mes'].astype(str).str.strip().str.upper()
        # Orden cronológico de meses para gráficos
        meses_orden = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 
                       'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
        df['mes_num'] = df['mes'].map({m: i+1 for i, m in enumerate(meses_orden)})
    else:
        df['mes'] = "SIN MES"
        df['mes_num'] = 0

    if 'ciudad' in df.columns:
        df['ciudad'] = df['ciudad'].astype(str).str.strip().str.upper()
    else:
        df['ciudad'] = "BOGOTA D.C."

    if 'tipo_de_servicio' in df.columns:
        df['tipo_de_servicio'] = df['tipo_de_servicio'].astype(str).str.strip().str.upper()
    else:
        df['tipo_de_servicio'] = "GENERAL"

    # Conversión numérica de servicios y uso de fuerza
    if 'cantidad_servicios_prestados' in df.columns:
        df['cantidad_servicios_prestados'] = pd.to_numeric(df['cantidad_servicios_prestados'], errors='coerce').fillna(0)
    else:
        df['cantidad_servicios_prestados'] = 1

    if 'se_uso_de_la_fuerza' in df.columns:
        df['se_uso_de_la_fuerza'] = df['se_uso_de_la_fuerza'].astype(str).str.strip().str.upper()
        df['se_uso_de_la_fuerza'] = df['se_uso_de_la_fuerza'].replace({'NAN': 'NO', '': 'NO', 'NONE': 'NO'})
    else:
        df['se_uso_de_la_fuerza'] = 'NO'

    if 'cantidad_de_veces_que_se' in df.columns:
        df['cantidad_de_veces_que_se'] = pd.to_numeric(df['cantidad_de_veces_que_se'], errors='coerce').fillna(0)
    else:
        df['cantidad_de_veces_que_se'] = 0

    return df

# --- Barra Lateral: Carga y Filtros ---
st.sidebar.title("🛡️ Panel de Control UDMO")
st.sidebar.markdown("---")

source_option = st.sidebar.radio("Fuente de Datos", ["API Oficial (datos.gov.co)", "Archivo Local"])
uploaded_file = None
if source_option == "Archivo Local":
    uploaded_file = st.sidebar.file_uploader("Cargar CSV o Excel", type=["csv", "xlsx"])

# Cargar datos
df = load_and_clean_data("API" if source_option == "API Oficial (datos.gov.co)" else "Archivo Local", uploaded_file)

if df.empty:
    st.warning("No se encontraron registros o la API no devolvió datos. Por favor verifica la fuente.")
    st.stop()

st.sidebar.markdown("### 🎛️ Filtros Interactivos")

# Filtro de Año
anios_disponibles = sorted(df['a_o'].unique().tolist())
selected_anios = st.sidebar.multiselect("Año(s)", anios_disponibles, default=anios_disponibles)

# Filtro de Mes
meses_disponibles = sorted(df['mes'].unique().tolist())
selected_meses = st.sidebar.multiselect("Mes(es)", meses_disponibles, default=meses_disponibles)

# Filtro de Ciudad
ciudades_disponibles = sorted(df['ciudad'].unique().tolist())
selected_ciudades = st.sidebar.multiselect("Ciudad(es)", ciudades_disponibles, default=ciudades_disponibles)

# Filtro de Tipo de Servicio
tipos_disponibles = sorted(df['tipo_de_servicio'].unique().tolist())
selected_tipos = st.sidebar.multiselect("Tipo de Servicio", tipos_disponibles, default=tipos_disponibles)

# Filtro de Uso de Fuerza
fuerza_disponible = sorted(df['se_uso_de_la_fuerza'].unique().tolist())
selected_fuerza = st.sidebar.multiselect("Se usó la fuerza", fuerza_disponible, default=fuerza_disponible)

# Aplicar filtros al DataFrame
filtered_df = df[
    df['a_o'].isin(selected_anios) &
    df['mes'].isin(selected_meses) &
    df['ciudad'].isin(selected_ciudades) &
    df['tipo_de_servicio'].isin(selected_tipos) &
    df['se_uso_de_la_fuerza'].isin(selected_fuerza)
]

# --- Cuerpo Principal ---
st.title("📊 Visor Estadístico y Operativo - UDMO (Bogotá D.C.)")
st.markdown("Análisis integral de actuaciones, despliegues operativos y métricas de uso de la fuerza de la Unidad de Diálogo y Mantenimiento del Orden.")

if filtered_df.empty:
    st.error("No hay registros que coincidan con los filtros seleccionados.")
    st.stop()

# --- KPIs Principales ---
total_actuaciones = filtered_df.shape[0]
total_servicios = filtered_df['cantidad_servicios_prestados'].sum()
eventos_fuerza = filtered_df[filtered_df['se_uso_de_la_fuerza'].isin(['SI', 'SÍ'])]['cantidad_servicios_prestados'].sum()
pct_fuerza = (eventos_fuerza / total_servicios * 100) if total_servicios > 0 else 0
total_veces_fuerza = filtered_df['cantidad_de_veces_que_se'].sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Registros Totales", f"{total_actuaciones:,}")
col2.metric("Servicios Prestados", f"{int(total_servicios):,}")
col3.metric("Uso de Fuerza (%)", f"{pct_fuerza:.2f}%")
col4.metric("Instancias de Fuerza", f"{int(total_veces_fuerza):,}")
top_ciudad = filtered_df['ciudad'].mode()[0] if not filtered_df.empty else "N/A"
col5.metric("Ciudad Principal", top_ciudad)

# --- Sistema de Alertas Operativas Inteligentes ---
st.markdown("---")
st.subheader("🚨 Alertas de Picos Operativos y Tendencias")
# Detectar si algún mes supera un umbral dinámico (ej. media + 1.5 * desv. estándar)
servicios_por_mes_anual = filtered_df.groupby(['a_o', 'mes'])['cantidad_servicios_prestados'].sum().reset_index()
if not servicios_por_mes_anual.empty:
    mean_servicios = servicios_por_mes_anual['cantidad_servicios_prestados'].mean()
    std_servicios = servicios_por_mes_anual['cantidad_servicios_prestados'].std()
    picos = servicios_por_mes_anual[servicios_por_mes_anual['cantidad_servicios_prestados'] > (mean_servicios + std_servicios)]
    
    if not picos.empty:
        for idx, row in picos.iterrows():
            st.markdown(f"""
                <div class="alert-box">
                    <b>⚠️ Alerta Operativa:</b> El período <b>{row['mes']} {row['a_o']}</b> registra un volumen elevado de operaciones ({int(row['cantidad_servicios_prestados'])} servicios), superando el promedio histórico operativo.
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Operación normal: No se detectan picos operativos extremos fuera del desvío estándar habitual para los filtros seleccionados.")

st.markdown("---")

# --- Pestañas de Visualización ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Análisis Temporal", 
    "🗺️ Geografía & Servicios", 
    "⚡ Uso de la Fuerza", 
    "📑 Tablas Dinámicas", 
    "💡 Resumen & Insights"
])

with tab1:
    st.subheader("Evolución Temporal de las Operaciones")
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Gráfica de Línea: Servicios por Año
        df_anio = filtered_df.groupby('a_o')['cantidad_servicios_prestados'].sum().reset_index()
        fig_line = px.line(df_anio, x='a_o', y='cantidad_servicios_prestados', markers=True,
                           title="Tendencia Anual de Servicios Prestados",
                           labels={'a_o': 'Año', 'cantidad_servicios_prestados': 'Total Servicios'})
        fig_line.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_line, use_container_width=True)
        
    with col_b:
        # Gráfica de Barras: Servicios por Mes
        df_mes = filtered_df.sort_values('mes_num').groupby(['mes', 'mes_num'])['cantidad_servicios_prestados'].sum().reset_index()
        fig_bar_mes = px.bar(df_mes, x='mes', y='cantidad_servicios_prestados',
                             title="Distribución de Servicios por Mes",
                             labels={'mes': 'Mes', 'cantidad_servicios_prestados': 'Total Servicios'},
                             color='cantidad_servicios_prestados', color_continuousScale='Blues')
        fig_bar_mes.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar_mes, use_container_width=True)
        
    # Heatmap: Año vs Mes
    st.subheader("Mapa de Calor Operativo (Año vs Mes)")
    if not filtered_df.empty:
        pivot_heat = filtered_df.pivot_table(index='a_o', columns='mes', values='cantidad_servicios_prestados', aggfunc='sum', fill_value=0)
        fig_heat = px.imshow(pivot_heat, labels=dict(x="Mes", y="Año", color="Servicios"),
                             title="Intensidad Operativa por Mes y Año",
                             aspect="auto", color_continuousScale="Viridis")
        fig_heat.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_heat, use_container_width=True)

with tab2:
    st.subheader("Análisis Geográfico y Tipología de Servicios")
    col_c, col_d = st.columns(2)
    
    with col_c:
        # Barras Horizontales: Ciudades con más servicios
        df_ciudad = filtered_df.groupby('ciudad')['cantidad_servicios_prestados'].sum().reset_index().sort_values(by='cantidad_servicios_prestados', ascending=True)
        fig_ciudad = px.bar(df_ciudad, x='cantidad_servicios_prestados', y='ciudad', orientation='h',
                            title="Servicios Prestados por Ciudad",
                            labels={'cantidad_servicios_prestados': 'Total Servicios', 'ciudad': 'Ciudad'},
                            color='cantidad_servicios_prestados', color_continuousScale='Teal')
        fig_ciudad.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_ciudad, use_container_width=True)
        
    with col_d:
        # Treemap: Tipos de servicio
        df_tipo = filtered_df.groupby('tipo_de_servicio')['cantidad_servicios_prestados'].sum().reset_index()
        fig_tree = px.treemap(df_tipo, path=['tipo_de_servicio'], values='cantidad_servicios_prestados',
                              title="Jerarquía de Tipos de Servicio",
                              color='cantidad_servicios_prestados', color_continuousScale='Sunset')
        fig_tree.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_tree, use_container_width=True)

with tab3:
    st.subheader("Dinámica del Uso de la Fuerza")
    col_e, col_f = st.columns(2)
    
    with col_e:
        # Pie Chart: Uso / No uso de la fuerza
        df_fuerza_pie = filtered_df.groupby('se_uso_de_la_fuerza')['cantidad_servicios_prestados'].sum().reset_index()
        fig_pie = px.pie(df_fuerza_pie, names='se_uso_de_la_fuerza', values='cantidad_servicios_prestados',
                         title="Proporción General del Uso de la Fuerza",
                         hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_f:
        # Línea: Evolución del uso de la fuerza por año
        df_fuerza_anio = filtered_df.groupby(['a_o', 'se_uso_de_la_fuerza'])['cantidad_servicios_prestados'].sum().reset_index()
        fig_fuerza_line = px.line(df_fuerza_anio, x='a_o', y='cantidad_servicios_prestados', color='se_uso_de_la_fuerza',
                                  markers=True, title="Evolución Histórica del Uso de la Fuerza por Año",
                                  labels={'a_o': 'Año', 'cantidad_servicios_prestados': 'Servicios'})
        fig_fuerza_line.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_fuerza_line, use_container_width=True)
        
    col_g, col_h = st.columns(2)
    with col_g:
        # Barras: Frecuencia de uso de fuerza por tipo de servicio
        df_fuerza_tipo = filtered_df.groupby(['tipo_de_servicio', 'se_uso_de_la_fuerza'])['cantidad_servicios_prestados'].sum().reset_index()
        fig_ftipo = px.bar(df_fuerza_tipo, x='tipo_de_servicio', y='cantidad_servicios_prestados', color='se_uso_de_la_fuerza',
                           title="Uso de Fuerza por Tipo de Servicio", barmode='group',
                           labels={'tipo_de_servicio': 'Tipo de Servicio', 'cantidad_servicios_prestados': 'Total Servicios'})
        fig_ftipo.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45)
        st.plotly_chart(fig_ftipo, use_container_width=True)
        
    with col_h:
        # Scatter & Boxplot combinados o analíticos
        fig_box = px.box(filtered_df, x='tipo_de_servicio', y='cantidad_de_veces_que_se', color='se_uso_de_la_fuerza',
                         title="Variación e Intensidad (Veces) de Uso de Fuerza por Servicio",
                         labels={'tipo_de_servicio': 'Tipo de Servicio', 'cantidad_de_veces_que_se': 'Veces de Uso de Fuerza'})
        fig_box.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45)
        st.plotly_chart(fig_box, use_container_width=True)
        
    # Scatter plot adicional: Relación servicios vs veces de uso de fuerza
    fig_scatter = px.scatter(filtered_df, x='cantidad_servicios_prestados', y='cantidad_de_veces_que_se', color='tipo_de_servicio',
                             title="Relación: Cantidad de Servicios vs Frecuencia de Aplicación de Fuerza",
                             labels={'cantidad_servicios_prestados': 'Servicios Prestados', 'cantidad_de_veces_que_se': 'Veces de Uso de Fuerza'},
                             hover_data=['ciudad', 'mes', 'a_o'])
    fig_scatter.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab4:
    st.subheader("Tablas Dinámicas y Explorador de Datos Detallados")
    
    # Selector de agregación para tabla dinámica
    st.markdown("Configure su propia agregación dinámica:")
    group_col = st.selectbox("Agrupar principal por:", ['tipo_de_servicio', 'ciudad', 'a_o', 'mes', 'se_uso_de_la_fuerza'], index=0)
    
    pivot_table = filtered_df.groupby(group_col).agg(
        Total_Registros=('cantidad_servicios_prestados', 'count'),
        Suma_Servicios=('cantidad_servicios_prestados', 'sum'),
        Suma_Veces_Fuerza=('cantidad_de_veces_que_se', 'sum')
    ).reset_index()
    
    st.dataframe(pivot_table, use_container_width=True)
    
    st.markdown("### Datos Filtrados Completos")
    st.dataframe(filtered_df, use_container_width=True)
    
    # Botón de descarga CSV
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Datos Filtrados en CSV",
        data=csv_data,
        file_name='reporte_udmo_filtrado.csv',
        mime='text/csv'
    )

with tab5:
    st.subheader("💡 Resumen Ejecutivo e Insights Operativos")
    
    st.markdown("""
    ### 📌 Hallazgos Principales del Análisis
    1. **Preponderancia Operativa:** El análisis geográfico confirma que la concentración de intervenciones se focaliza principal y masivamente en Bogotá D.C., obediriendo al mandato jurisdiccional de la unidad.
    2. **Umbrales de Fuerza:** La gran mayoría de los servicios prestados por la UDMO se desarrollan bajo protocolos de diálogo y mediación, registrando un porcentaje de uso de fuerza acotado en comparación con el volumen global de intervenciones.
    3. **Tipologías de Mayor Demanda:** Los eventos de afluencia masiva y movilizaciones sociales representan el mayor porcentaje de despliegues operativos dentro de la jerarquía de servicios.
    
    ### 🎯 Recomendaciones Estratégicas para la Toma de Decisiones
    * **Fortalecimiento Preventivo:** Focalizar las capacidades de diálogo social en los meses con picos operativos históricos detectados por el mapa de calor.
    * **Optimización de Recursos:** Reasignar componentes logísticos y de personal de acuerdo con la recurrencia de tipos de servicios específicos en las zonas de mayor demanda.
    * **Monitoreo Continuo:** Utilizar las métricas de intensidad en el uso de la fuerza para retroalimentar los protocolos de derechos humanos y evaluación de intervención operativa.
    """)

# --- Pie de página ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Sistema de Inteligencia de Datos Operativos UDMO | Desarrollado con Streamlit y Python</p>", unsafe_allow_html=True)
