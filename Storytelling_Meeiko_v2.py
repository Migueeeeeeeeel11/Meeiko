import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import tempfile, os
import re
import numpy as np
from PIL import Image

st.set_page_config(page_title="📊 Storytelling", layout="wide")

# ======================
# Funciones para la carga y limpieza de datos
# ======================
@st.cache_data
def read_clv_csv(path: str):
    """
    Carga el archivo CSV de clientes, ajusta el delimitador y limpia los nombres de las columnas.
    """
    try:
        df = pd.read_csv(path, delimiter=";", dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except FileNotFoundError:
        st.error(f"Error: El archivo '{path}' no se encuentra. Asegúrate de que esté en la misma carpeta que tu script de Streamlit.")
        st.stop()
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo: {e}")
        st.stop()

def to_numeric_smart(s: pd.Series) -> pd.Series:
    """
    Convierte una serie a tipo numérico, manejando formatos europeos (1.234,56) y otros.
    """
    s = s.astype(str).str.strip()
    euro_pat = re.compile(r"^\d{1,3}(\.\d{3})+(,\d+)?$")
    
    def parse_one(x):
        if x in ("", "None", "nan", "NaN"):
            return np.nan
        if isinstance(x, (int, float)):
            return x
        if euro_pat.match(x):
            x2 = x.replace(".", "").replace(",", ".")
            try:
                return float(x2)
            except:
                return np.nan
        try:
            return float(x)
        except:
            try:
                return float(x.replace(",", ""))
            except:
                return np.nan
    return s.map(parse_one)

# ======================
# Título y carga de datos
# ======================
st.title("La Historia detrás de nuestros Clientes")
st.markdown("---")
st.markdown("""
### ¡Explora los datos de nuestros clientes!
Aquí te presento un análisis de marketing basado en datos de clientes. Descubriremos quiénes son nuestros clientes más valiosos, cómo nos encontraron y qué tipo de productos tienen.
""")

df_clv = read_clv_csv("CLV.csv")

# ======================
# Limpieza de las columnas clave
# ======================
df_clv['Customer Lifetime Value'] = to_numeric_smart(df_clv['Customer Lifetime Value'])
df_clv['Total Claim Amount'] = to_numeric_smart(df_clv['Total Claim Amount'])
df_clv['Effective To Date'] = pd.to_datetime(df_clv['Effective To Date'], format='%m/%d/%y', errors='coerce')
df_clv.dropna(subset=['Effective To Date'], inplace=True)
df_clv.sort_values(by='Effective To Date', inplace=True)

# ======================
# 1. Dashboard Interactivo - Analizando el Customer Lifetime Value (CLV)
# ======================
st.header("📈 ¿Quiénes son nuestros clientes más valiosos?")
st.write("El Customer Lifetime Value (CLV) nos dice el valor total que un cliente aporta a nuestra empresa. Analicemos su distribución.")

fig_clv = px.histogram(df_clv, x="Customer Lifetime Value", nbins=50, 
                       title="Distribución del Valor de Vida del Cliente",
                       template="plotly_white")
st.plotly_chart(fig_clv, use_container_width=True)

st.markdown("""
<div style="background-color:#f0f2f6;padding:10px;border-radius:10px;font-size:18px;">
<b>Insight Clave:</b> La mayoría de nuestros clientes tienen un CLV bajo, pero un pequeño grupo representa un valor excepcionalmente alto.
</div>
""", unsafe_allow_html=True)
st.write("---")

# ======================
# 2. Infografía de reclamaciones por canal de ventas con Seaborn
# ======================
st.header("🖼️ ¿Cómo nos encontramos con nuestros clientes?")
st.write("El canal de ventas es crucial. A continuación, vemos qué canales generan las mayores reclamaciones, un indicador de posibles fricciones en el proceso.")

claim_by_channel = df_clv.groupby('Sales Channel')['Total Claim Amount'].sum().reset_index()
sns.set(style="whitegrid")
fig_channel, ax_channel = plt.subplots(figsize=(10, 6))
sns.barplot(x="Sales Channel", y="Total Claim Amount", data=claim_by_channel, ax=ax_channel, palette="viridis")
ax_channel.set_title("Total de reclamaciones por Canal de Ventas")
ax_channel.set_ylabel("Total de Reclamaciones")
ax_channel.set_xlabel("Canal de Ventas")
st.pyplot(fig_channel)

st.markdown("""
<div style="background-color:#f0f2f6;padding:10px;border-radius:10px;font-size:18px;">
<b>Insight Clave:</b> El canal 'Agent' y 'Branch' son los que más reclamaciones generan. Esto podría sugerir un área de oportunidad para mejorar la capacitación o los procesos en estos canales.
</div>
""", unsafe_allow_html=True)
st.write("---")

# ======================
# 3. Gráfico Interactivo: La dinámica de las reclamaciones por tipo de vehículo
# ======================
st.header("🎥 La dinámica de las reclamaciones por tipo de vehículo")
st.write("En lugar de una animación, usa este control deslizante para explorar cómo las reclamaciones por tipo de vehículo han evolucionado a lo largo del tiempo.")

# Obtener los puntos de tiempo para el slider
# Se obtiene un array de fechas únicas, se eliminan los NaT y se ordenan.
timeline = sorted(df_clv['Effective To Date'].dropna().unique())

# Crear el slider de tiempo
selected_date = st.select_slider(
    'Selecciona una fecha para ver el estado de las reclamaciones:',
    options=timeline,
    format_func=lambda d: d.strftime('%Y-%m-%d')
)

# Filtrar los datos hasta la fecha seleccionada
filtered_df = df_clv[df_clv['Effective To Date'] <= selected_date]

# Agrupar los datos filtrados
claim_by_vehicle = filtered_df.groupby('Vehicle Class')['Total Claim Amount'].sum().reset_index()

# Crear y mostrar el gráfico de barras con el filtro de tiempo
fig_interactive, ax_interactive = plt.subplots(figsize=(10, 6))
sns.barplot(x='Vehicle Class', y='Total Claim Amount', data=claim_by_vehicle, ax=ax_interactive, palette="tab10")
ax_interactive.set_title(f"Reclamaciones por tipo de vehículo hasta el {selected_date.strftime('%Y-%m-%d')}")
ax_interactive.set_ylabel("Total de Reclamaciones")
ax_interactive.set_xlabel("Tipo de Vehículo")
ax_interactive.set_ylim(0, df_clv['Total Claim Amount'].sum() * 1.1)

st.pyplot(fig_interactive)

st.markdown("---")
st.markdown("✅ **Demo de Storytelling en Marketing Analytics con Python + Streamlit**")