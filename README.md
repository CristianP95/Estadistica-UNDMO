# Estadistica-UNDMO


Aplicación web interactiva desarrollada en Python y desplegada en la nube para el análisis, consulta y monitoreo histórico, Accede a los datos abiertos de la DIPON y realiza un analisis de la informacion via API. Los datos se consumen dinámicamente en tiempo real desde el portal oficial de datos abiertos del gobierno (datos.gov.co), abarcando registros desde 1991 hasta la actualidad.

VISUALIZAR LOS DATOS

Visualice los datos en Streamlit, si la App esta caída. De Click en poner en marcha esta aplicación. https://visor-estadistica-undmo.streamlit.app/

CARACTERÍSTICAS PRINCIPALES

Consumo de API REST en Tiempo Real: Extracción automatizada de más de 30 años de registros financieros oficiales de la TMR mediante solicitudes HTTP eficientes y codificación de URLs seguras.

Jerarquía y Agrupación Temporal Dinámica: Permite segmentar el análisis de los datos por Anual, Mensual, Semanal o Diario, ajustando de manera inteligente los controles deslizantes del eje X según la granularidad seleccionada.

Filtros Avanzados y Accesos Rápidos:

Sliders interactivos de rangos amplios para navegar con precisión entre cualquier período histórico.

Opciones de filtrado rápido para vistas diarias (últimos 5, 15, 30 días o rangos personalizados).

Indicadores Estadísticos Clave (KPIs): Visualización instantánea de la TMR de Hoy (con fecha formateada en español), TMR Final del Rango, Promedio del Periodo, Valor Máximo, Valor Mínimo y porcentaje de variación histórica.

Sistema de Alertas Financieras: Configuración de umbrales personalizados por el usuario con notificaciones automáticas en pantalla ante fluctuaciones o superación de límites de precio en la divisa.

TECNOLOGÍAS Y LIBRERÍAS UTILIZADAS

Python 3.12+

Streamlit: Construcción y despliegue del panel de control web interactivo con gestión avanzada de estado (st.session_state).

urllib & json: Conexión nativa, parseo y estructuración de respuestas JSON provenientes de la API abierta.

AUTOR

Cristian Dario Pineda Rodriguez

Ingeniería Informática

GitHub: https://github.com/cristianp95

