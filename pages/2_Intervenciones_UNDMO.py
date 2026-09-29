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
    
    # Diccionario completo de columnas técnicas de munición y elementos tácticos según JSON oficial
    cols_municiones_dict = {
        'Esfera Fragmentable O.C.': 'esfera_fragmentable_o_c_0',
        'Cartucho Gas CS 37/38mm': 'cartucho_de_gas_cs_37_38',
        'Granada de Aturdimiento': 'granada_de_aturdimiento',
        'Granada Fumígena de Humo': 'granada_fum_gena_de_humo',
        'Granada Gas CS de Mano': 'granada_gas_cs_de_mano',
        'Cartucho Gas CS Lanzador': 'cartucho_gas_cs_lanzador',
        'Cartucho Aturdimiento Lanzador': 'cartucho_aturdimiento_lanzador',
        'Cartucho Dispositivo Defensivo': 'cartucho_dispositivo_de',
        'Cartucho Impulsor 37mm': 'cartucho_impulsor_37_mm',
        'Cartucho Gas CS 40mm': 'cartucho_de_gas_cs_40_mm',
        'Cartucho Impacto Dirigido': 'cartucho_impacto_dirigido',
        'Granada Gas CS con Con': 'granada_de_gas_cs_con'
    }
    
    # Asegurar que todas las columnas existan y sean numéricas
    for nombre_legible, col_tec in cols_municiones_dict.items():
        if col_tec not in df.columns:
            df[col_tec] = 0
        df[col_tec] = pd.to_numeric(df[col_tec], errors='coerce').fillna(0)

    for col_lesion in ['ciudadanos_lesionados', 'policias_lesionados']:
        if col_lesion not in df.columns:
            df[col_lesion] = 0
        df[col_lesion] = pd.to_numeric(df[col_lesion], errors='coerce').fillna(0)

    # Limpieza de textos
    for col in ['factor_de_atenci_n_que_genera', 'mes', 'ciudad', 'departamento', 'gudmo']:
        if col not in df.columns:
            df[col] = 'NO REGISTRA'
        df[col] = df[col].fillna('NO REGISTRA').astype(str).str.strip().str.upper()

    if 'a_o' in df.columns:
        df['a_o'] = pd.to_numeric(df['a_o'], errors='coerce').fillna(0).astype(int).astype(str)
    else:
        df['a_o'] = 'DESCONOCIDO'

    # Calcular total de municiones por evento sumando todas las columnas técnicas
    df['total_municiones_evento'] = df[list(cols_municiones_dict.values())].sum(axis=1)
    
    return df

st.title("🔍 Detalle Operativo - Intervenciones UNDMO")
st.markdown("""
Módulo especializado en el registro y fiscalización de intervenciones específicas, abarcando factores de atención, 
unidades GUDMO participantes, análisis detallado de municiones, elementos tácticos y personal afectado.
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
    'Cartucho Aturdimiento Lanzador': 'cartucho_aturdimiento_lanzador',
    'Cartucho Dispositivo Defensivo': 'cartucho_dispositivo_de',
    'Cartucho Impulsor 37mm': 'cartucho_impulsor_37_mm',
    'Cartucho Gas CS 40mm': 'cartucho_de_gas_cs_40_mm',
    'Cartucho Impacto Dirigido': 'cartucho_impacto_dirigido',
    'Granada Gas CS con Con': 'granada_de_gas_cs_con'
}

# Totales globales por cada tipo de munición
totales_por_tipo = {nombre: int(df[col].sum()) for nombre, col in cols_mun_dict.items()}
tipo_mas_usado = max(totales_por_tipo, key=totales_por_tipo.get) if totales_por_tipo else "N/A"
cantidad_max_mun = totales_por_tipo.get(tipo_mas_usado, 0)

# GUDMO que más municiones ha usado (Agrupado explícitamente y seleccionado el máximo)
df_gudmo_mun = df.groupby('gudmo')['total_municiones_evento'].sum().reset_index()
if not df_gudmo_mun.empty:
    df_gudmo_mun = df_gudmo_mun.sort_values(by='total_municiones_evento', ascending=False)
    gudmo_mas_activo = str(df_gudmo_mun.iloc[0]['gudmo'])
    gudmo_cant = int(df_gudmo_mun.iloc[0]['total_municiones_evento'])
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
# ANÁLISIS VISUAL: GUDMO VS TIPO DE MUNICIÓN
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Análisis de Consumo: Grupo GUDMO vs. Tipo de Munición")
st.markdown("""
Gráfica comparativa que muestra qué tipos de munición y elementos tácticos emplean los diferentes grupos GUDMO.
""")

df_melted_gudmo = pd.melt(
    df,
    id_vars=['gudmo'],
    value_vars=list(cols_mun_dict.values()),
    var_name='tipo_municion_tec',
    value_name='cantidad'
)
inv_cols_mun_dict = {v: k for k, v in cols_mun_dict.items()}
df_melted_gudmo['Tipo de Munición'] = df_melted_gudmo['tipo_municion_tec'].map(inv_cols_mun_dict)

df_gudmo_mun_tipo = df_melted_gudmo.groupby(['gudmo', 'Tipo de Munición'])['cantidad'].sum().reset_index()
df_gudmo_mun_tipo = df_gudmo_mun_tipo[df_gudmo_mun_tipo['cantidad'] > 0] # Mostrar solo consumo activo

fig_gudmo_mun = px.bar(
    df_gudmo_mun_tipo,
    x='gudmo',
    y='cantidad',
    color='Tipo de Munición',
    title="Consumo de Municiones por Grupo GUDMO",
    labels={'gudmo': 'Grupo GUDMO', 'cantidad': 'Cantidad Total Consumida'},
    barmode='group'
)
fig_gudmo_mun.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_gudmo_mun, use_container_width=True)

# ---------------------------------------------------------
# ANÁLISIS VISUAL Y AGRUPADO: CIUDAD Y FACTOR DE ATENCIÓN
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Análisis Visual de Municiones por Ciudad y Factor de Atención")

col_f1, col_f2 = st.columns(2)
with col_f1:
    ciudades_disp = sorted(df['ciudad'].unique().tolist())
    sel_ciudad_grafica = st.multiselect("Filtrar Ciudad(es) para Gráfica", ciudades_disp, default=ciudades_disp[:5] if len(ciudades_disp) > 5 else ciudades_disp)
with col_f2:
    factores_disp = sorted(df['factor_de_atenci_n_que_genera'].unique().tolist())
    sel_factor_grafica = st.multiselect("Filtrar Factor(es) para Gráfica", factores_disp, default=factores_disp[:5] if len(factores_disp) > 5 else factores_disp)

df_graf_mun = df.copy()
if sel_ciudad_grafica:
    df_graf_mun = df_graf_mun[df_graf_mun['ciudad'].isin(sel_ciudad_grafica)]
if sel_factor_grafica:
    df_graf_mun = df_graf_mun[df_graf_mun['factor_de_atenci_n_que_genera'].isin(sel_factor_grafica)]

df_melted_fact = pd.melt(
    df_graf_mun,
    id_vars=['ciudad', 'factor_de_atenci_n_que_genera'],
    value_vars=list(cols_mun_dict.values()),
    var_name='tipo_municion_tec',
    value_name='cantidad'
)
df_melted_fact['Tipo de Munición'] = df_melted_fact['tipo_municion_tec'].map(inv_cols_mun_dict)

df_agrupado_graf = df_melted_fact.groupby(['factor_de_atenci_n_que_genera', 'Tipo de Munición'])['cantidad'].sum().reset_index()

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
