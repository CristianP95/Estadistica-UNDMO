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

API_URL_INTERVENCIONES = "https://www.datos.gov.co/resource/3fu3-w3iv.json?$limit=5000"

@st.cache_data(ttl=3600)
def cargar_datos_intervenciones():
    try:
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
    
    cols_a_mantener = [c for c in df.columns if not c.startswith(':')]
    df = df[cols_a_mantener].copy()
    
    # Columnas de municiones técnicas a convertir a numérico
    cols_municiones = [
        'esfera_fragmentable_o_c_0', 
        'cartucho_de_gas_cs_37_38',
        'granada_de_aturdimiento', 
        'granada_fum_gena_de_humo', 
        'granada_gas_cs_de_mano',
        'cartucho_gas_cs_lanzador', 
        'cartucho_aturdimiento_lanzador'
    ]
    
    cols_numericas = ['a_o', 'ciudadanos_lesionados', 'policias_lesionados'] + cols_municiones
    
    for col in cols_numericas:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Limpieza de textos
    for col in ['factor_de_atenci_n_que_genera', 'mes', 'ciudad', 'departamento', 'gudmo']:
        if col not in df.columns:
            df[col] = 'NO REGISTRA'
        df[col] = df[col].fillna('NO REGISTRA').astype(str).str.strip().str.upper()

    df['a_o'] = df['a_o'].astype(int).astype(str)
    
    # Suma total de municiones por registro individual
    df['total_municiones_evento'] = df[cols_municiones].sum(axis=1)
    
    return df

st.title("🔍 Detalle Operativo - Intervenciones UNDMO")
st.markdown("""
Módulo especializado en el registro y fiscalización de intervenciones específicas, abarcando factores de atención, 
unidades GUDMO participantes, análisis detallado de municiones y el personal afectado.
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

# ---------------------------------------------------------
# FILTROS LATERALES
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# CÁLCULOS DE MUNICIONES Y HALLAZGOS CLAVE
# ---------------------------------------------------------
cols_mun_dict = {
    'Esfera Fragmentable O.C.': 'esfera_fragmentable_o_c_0',
    'Cartucho Gas CS 37/38mm': 'cartucho_de_gas_cs_37_38',
    'Granada de Aturdimiento': 'granada_de_aturdimiento',
    'Granada Fumígena de Humo': 'granada_fum_gena_de_humo',
    'Granada Gas CS de Mano': 'granada_gas_cs_de_mano',
    'Cartucho Gas CS Lanzador': 'cartucho_gas_cs_lanzador',
    'Cartucho Aturdimiento Lanzador': 'cartucho_aturdimiento_lanzador'
}

# Totales globales por cada tipo de munición
totales_por_tipo = {nombre: int(df[col].sum()) for nombre, col in cols_mun_dict.items()}
tipo_mas_usado = max(totales_por_tipo, key=totales_por_tipo.get)
cantidad_max_mun = totales_por_tipo[tipo_mas_usado]

# GUDMO que más municiones ha usado (Corregido y especificado nominalmente)
df_gudmo_mun = df.groupby('gudmo')['total_municiones_evento'].sum().reset_index()
if not df_gudmo_mun.empty:
    top_gudmo_row = df_gudmo_mun.loc[df_gudmo_mun['total_municiones_evento'].idxmax()]
    gudmo_mas_activo = str(top_gudmo_row['gudmo'])
    gudmo_cant = int(top_gudmo_row['total_municiones_evento'])
else:
    gudmo_mas_activo = "No registra"
    gudmo_cant = 0

# KPIs Principales
total_intervenciones = len(df)
total_ciudadanos_les = int(df['ciudadanos_lesionados'].sum())
total_policias_les = int(df['policias_lesionados'].sum())
total_municiones_global = int(df['total_municiones_evento'].sum())

k1, k2, k3, k4 = st.columns(4)
k1.metric("Intervenciones Registradas", f"{total_intervenciones:,}")
k2.metric("Total Municiones Usadas", f"{total_municiones_global:,}")
k3.metric("Ciudadanos Lesionados", f"{total_ciudadanos_les:,}")
k4.metric("Policías Lesionados", f"{total_policias_les:,}")

st.markdown("---")

# ---------------------------------------------------------
# SECCIÓN DE RESALTADO DE HALLAZGOS (MUNICIÓN Y GUDMO)
# ---------------------------------------------------------
st.markdown("### 🏆 Hallazgos Destacados en Uso de Municiones")
col_h1, col_h2 = st.columns(2)

with col_h1:
    st.success(f"""
    **🔥 Tipo de Munición Más Usada:**
    * **{tipo_mas_usado}**
    * **Total consumido:** {cantidad_max_mun:,} unidades.
    """)

with col_h2:
    st.info(f"""
    **🛡️ Grupo GUDMO con Mayor Consumo:**
    * **{gudmo_mas_activo}**
    * **Total municiones empleadas:** {gudmo_cant:,} unidades.
    """)

st.markdown("---")

# ---------------------------------------------------------
# GRÁFICAS GENERALES
# ---------------------------------------------------------
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
                   title="Participación de Grupos GUDMO por Intervenciones",
                   labels={'conteo': 'Intervenciones Atendidas', 'gudmo': 'Grupo GUDMO'})
    st.plotly_chart(fig_g, use_container_width=True)

# ---------------------------------------------------------
# NUEVO: ANÁLISIS Y GRÁFICAS POR TIPO DE MUNICIÓN, CIUDAD Y FACTOR DE ATENCIÓN
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Análisis Visual y Agrupado de Municiones (Ciudad y Factor de Atención)")
st.markdown("""
Gráfica interactiva de consumo de elementos tácticos agrupada por factores de atención y ciudades. 
Utiliza los filtros de abajo para refinar la visualización gráfica.
""")

# Selector para la gráfica de municiones agrupadas
col_f1, col_f2 = st.columns(2)
with col_f1:
    ciudades_disp = sorted(df['ciudad'].unique().tolist())
    sel_ciudad_grafica = st.multiselect("Filtrar Ciudad(es) para Gráfica", ciudades_disp, default=ciudades_disp[:5] if len(ciudades_disp) > 5 else ciudades_disp)
with col_f2:
    factores_disp = sorted(df['factor_de_atenci_n_que_genera'].unique().tolist())
    sel_factor_grafica = st.multiselect("Filtrar Factor(es) para Gráfica", factores_disp, default=factores_disp[:5] if len(factores_disp) > 5 else factores_disp)

# Filtrar dataframe para la gráfica
df_graf_mun = df.copy()
if sel_ciudad_grafica:
    df_graf_mun = df_graf_mun[df_graf_mun['ciudad'].isin(sel_ciudad_grafica)]
if sel_factor_grafica:
    df_graf_mun = df_graf_mun[df_graf_mun['factor_de_atenci_n_que_genera'].isin(sel_factor_grafica)]

# Preparar datos formato largo (melt) para graficar tipos de munición agrupados
df_melted = pd.melt(
    df_graf_mun,
    id_vars=['ciudad', 'factor_de_atenci_n_que_genera'],
    value_vars=list(cols_mun_dict.values()),
    var_name='tipo_municion_tec',
    value_name='cantidad'
)

# Mapear nombres técnicos a legibles
inv_cols_mun_dict = {v: k for k, v in cols_mun_dict.items()}
df_melted['Tipo de Munición'] = df_melted['tipo_municion_tec'].map(inv_cols_mun_dict)

# Agrupar por Factor de Atención y Tipo de Munición
df_agrupado_graf = df_melted.groupby(['factor_de_atenci_n_que_genera', 'Tipo de Munición'])['cantidad'].sum().reset_index()

fig_municiones = px.bar(
    df_agrupado_graf,
    x='factor_de_atenci_n_que_genera',
    y='cantidad',
    color='Tipo de Munición',
    title="Consumo de Municiones por Factor de Atención",
    labels={'factor_de_atenci_n_que_genera': 'Factor de Atención', 'cantidad': 'Cantidad Total Consumida'},
    barmode='group'
)
fig_municiones.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_municiones, use_container_width=True)

# ---------------------------------------------------------
# TABLA DINÁMICA: CIUDAD Y FACTOR DE ATENCIÓN
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📋 Tabla Dinámica Consolidada por Ciudad y Factor de Atención")

cols_agrupacion = ['ciudad', 'factor_de_atenci_n_que_genera']
dict_agregacion = {col: 'sum' for col in list(cols_mun_dict.values()) + ['total_municiones_evento']}
dict_agregacion['a_o'] = 'count'

df_agrupado = df.groupby(cols_agrupacion).agg(dict_agregacion).reset_index()
df_agrupado = df_agrupado.rename(columns={'a_o': 'total_intervenciones'})

renombres_columnas = {
    'ciudad': 'Ciudad',
    'factor_de_atenci_n_que_genera': 'Factor de Atención',
    'total_intervenciones': 'N° Intervenciones',
    'total_municiones_evento': 'Total Municiones'
}
for nombre_legible, col_tecnica in cols_mun_dict.items():
    renombres_columnas[col_tecnica] = nombre_legible

df_tabla_final = df_agrupado.rename(columns=renombres_columnas)
df_tabla_final = df_tabla_final.sort_values(by='Total Municiones', ascending=False)

st.dataframe(df_tabla_final, use_container_width=True)

# ---------------------------------------------------------
# TABLA DE REGISTROS RAW
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📁 Registro Detallado Individual de Intervenciones")
st.dataframe(df, use_container_width=True)
