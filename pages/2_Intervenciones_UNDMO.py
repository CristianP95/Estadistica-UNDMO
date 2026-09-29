import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

st.set_page_config(
    page_title="Intervenciones UNDMO",
    page_icon="🔍",
    layout="wide"
)

# Endpoint Socrata optimizado para recursos JSON directos
API_URL_INTERVENCIONES = "https://www.datos.gov.co/resource/3fu3-w3iv.json?$limit=5000"

@st.cache_data(ttl=3600)
def cargar_datos_intervenciones():
    try:
        # Aumentamos el timeout a 30 segundos para evitar cortes por latencia en la red
        response = requests.get(API_URL_INTERVENCIONES, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            for key in ['data', 'rows', 'result']:
                if key in data and isinstance(data[key], list):
                    return pd.DataFrame(data[key])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al conectar con la API de Intervenciones: {e}")
        return None

def limpiar_intervenciones(df):
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Filtrar metadatos internos de Socrata si los hay
    cols_a_mantener = [c for c in df.columns if not c.startswith(':')]
    df = df[cols_a_mantener].copy()
    
    # Asegurar columnas numéricas técnicas de municiones y lesiones
    cols_numericas = [
        'a_o', 'esfera_fragmentable_o_c_0', 'cartucho_de_gas_cs_37_38',
        'granada_de_aturdimiento', 'granada_fum_gena_de_humo', 'granada_gas_cs_de_mano',
        'cartucho_gas_cs_lanzador', 'cartucho_aturdimiento_lanzador', 'ciudadanos_lesionados', 'policias_lesionados'
    ]
    
    for col in cols_numericas:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Limpieza y normalización de textos
    for col in ['factor_de_atenci_n_que_genera', 'mes', 'ciudad', 'departamento', 'gudmo']:
        if col not in df.columns:
            df[col] = 'NO REGISTRA'
        df[col] = df[col].fillna('NO REGISTRA').astype(str).str.strip().str.upper()

    df['a_o'] = df['a_o'].astype(int).astype(str)
    return df

st.title("🔍 Detalle Operativo - Intervenciones UNDMO")
st.markdown("""
Módulo especializado en el registro y fiscalización de intervenciones específicas, abarcando factores de atención, 
unidades GUDMO participantes y el reporte detallado de municiones, elementos tácticos y personal afectado.
""")

with st.spinner("Descargando registro oficial de intervenciones desde datos.gov.co..."):
    raw_df = cargar_datos_intervenciones()

if raw_df is None or raw_df.empty:
    st.warning("No se pudieron obtener registros desde la API de Intervenciones. Por favor, verifica tu conexión o intenta recargar.")
    st.stop()

df = limpiar_intervenciones(raw_df)

if df.empty:
    st.error("El conjunto de datos procesado está vacío.")
    st.stop()

# Filtros laterales
st.sidebar.markdown("### 🎛️ Filtros de Intervención")
anios = sorted(df['a_o'].unique().tolist())
sel_anios = st.sidebar.multiselect("Año(s)", anios, default=anios)
if sel_anios: df = df[df['a_o'].isin(sel_anios)]

departamentos = sorted(df['departamento'].unique().tolist())
sel_dpto = st.sidebar.multiselect("Departamento(s)", departamentos, default=departamentos)
if sel_dpto: df = df[df['departamento'].isin(sel_dpto)]

factores = sorted(df['factor_de_atenci_n_que_genera'].unique().tolist())
sel_factor = st.sidebar.multiselect("Factor de Atención", factores, default=factores)
if sel_factor: df = df[df['factor_de_atenci_n_que_genera'].isin(sel_factor)]

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Recargar Datos"):
    st.cache_data.clear()
    st.rerun()

# KPIs de Intervenciones
total_intervenciones = len(df)
total_ciudadanos_les = int(df['ciudadanos_lesionados'].sum())
total_policias_les = int(df['policias_lesionados'].sum())
total_municiones = int(
    df['cartucho_de_gas_cs_37_38'].sum() + 
    df['granada_de_aturdimiento'].sum() + 
    df['granada_fum_gena_de_humo'].sum() + 
    df['granada_gas_cs_de_mano'].sum() +
    df['cartucho_gas_cs_lanzador'].sum()
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Intervenciones Registradas", f"{total_intervenciones:,}")
k2.metric("Municiones / Elementos Totales", f"{total_municiones:,}")
k3.metric("Ciudadanos Lesionados", f"{total_ciudadanos_les:,}")
k4.metric("Policías Lesionados", f"{total_policias_les:,}")

st.markdown("---")

# Gráficas y análisis
col_1, col_2 = st.columns(2)

with col_1:
    df_factor = df.groupby('factor_de_atenci_n_que_genera')['a_o'].count().reset_index()
    df_factor.columns = ['factor', 'conteo']
    df_factor = df_factor.sort_values('conteo', ascending=False).head(10)
    fig_f = px.bar(df_factor, x='conteo', y='factor', orientation='h',
                   title="Top Factores de Atención que Generan Intervención",
                   labels={'conteo': 'Cantidad de Intervenciones', 'factor': 'Factor'})
    st.plotly_chart(fig_f, use_container_width=True)

with col_2:
    df_gudmo = df.groupby('gudmo')['a_o'].count().reset_index()
    df_gudmo.columns = ['gudmo', 'conteo']
    df_gudmo = df_gudmo.sort_values('conteo', ascending=False).head(10)
    fig_g = px.bar(df_gudmo, x='conteo', y='gudmo', orientation='h',
                   title="Participación de Grupos GUDMO",
                   labels={'conteo': 'Intervenciones Atendidas', 'gudmo': 'Grupo GUDMO'})
    st.plotly_chart(fig_g, use_container_width=True)

st.markdown("### 📊 Consumo de Municiones y Elementos Tácticos")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Cartuchos Gas CS 37/38mm", f"{int(df['cartucho_de_gas_cs_37_38'].sum()):,}")
col_m2.metric("Granadas de Aturdimiento", f"{int(df['granada_de_aturdimiento'].sum()):,}")
col_m3.metric("Granadas Fumígenas de Humo", f"{int(df['granada_fum_gena_de_humo'].sum()):,}")
col_m4.metric("Granadas Gas CS de Mano", f"{int(df['granada_gas_cs_de_mano'].sum()):,}")

st.markdown("---")
st.subheader("📋 Tabla Detallada de Intervenciones")
st.dataframe(df, use_container_width=True)
