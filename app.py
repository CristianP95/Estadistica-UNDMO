import streamlit as st

st.set_page_config(
    page_title="Portal UNDMO - Inicio",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ Portal de Transparencia y Análisis Operativo - UNDMO")
st.markdown("""
Bienvenido a la plataforma oficial de consulta, visualización y análisis estadístico de las actuaciones y operativos 
de la **Unidad de Diálogo y Mantenimiento del Orden (UNDMO)** de la Policía Nacional.

Esta herramienta centraliza información pública abierta para facilitar la fiscalización ciudadana, el estudio técnico 
y la transparencia institucional a través de dos módulos principales:
""")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Estadísticas UNDMO")
    st.markdown("""
    Visualiza el consolidado general de actuaciones, servicios prestados por año y mes, mapas de calor, 
    mapas de árbol por tipo de servicio y el análisis detallado del uso de la fuerza institucional.
    """)
    st.info("👈 Utiliza el menú lateral izquierdo para acceder a **Estadisticas_UNDMO**.")

with col2:
    st.markdown("### 🔍 Intervenciones UNDMO")
    st.markdown("""
    Explora el detalle operativo de intervenciones específicas, factores de atención desencadenantes, 
    distribución geográfica (departamentos y ciudades), grupos GUDMO asignados y el registro técnico 
    de municiones y elementos empleados (cartuchos de gas, granadas de aturdimiento, humo, etc.).
    """)
    st.success("👈 Utiliza el menú lateral izquierdo para acceder a **Intervenciones_UNDMO**.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Datos abiertos obtenidos en tiempo real desde datos.gov.co</p>", unsafe_allow_html=True)
