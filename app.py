import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

from fiscal_api import FiscalAIClient
from dcf_engine import DCFCalculator

# Cargar variables de entorno
load_dotenv()

# Configuración de página
st.set_page_config(
    page_title="DCF Investment Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main {padding: 0rem 1rem;}
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #0066cc;
        color: white;
        border-radius: 8px;
        padding: 0.5rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar sesión
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = None

# Sidebar
st.sidebar.title("🔍 Configuración")

# API Key input
api_key = st.sidebar.text_input(
    "Fiscal.AI API Key",
    value=os.getenv("FISCAL_API_KEY", ""),
    type="password"
)

min_upside = st.sidebar.slider("Upside Mínimo (%)", 0, 100, 20, 5)
risk_free_rate = st.sidebar.number_input("Tasa Libre de Riesgo (%)", value=4.0, step=0.1) / 100
market_return = st.sidebar.number_input("Retorno del Mercado (%)", value=10.0, step=0.1) / 100
terminal_growth = st.sidebar.number_input("Crecimiento Terminal (%)", value=2.5, step=0.1) / 100

# Título
st.title("📈 DCF Investment Opportunity Screener")
st.markdown("Análisis automatizado con Fiscal.AI API")

# Tabs
tab1, tab2 = st.tabs(["🎯 Screening", "📊 Análisis Individual"])

with tab1:
    if st.button("🚀 Ejecutar Screening", key="run"):
        if not api_key:
            st.error("⚠️ Por favor ingresa tu API Key de Fiscal.AI")
        else:
            with st.spinner("Analizando empresas..."):
                try:
                    # Inicializar cliente y calculadora
                    client = FiscalAIClient(api_key)
                    calculator = DCFCalculator(client)
                    
                    # Ejecutar screening
                    opportunities = calculator.screen_opportunities(
                        min_upside=min_upside/100,
                        max_companies=30
                    )
                    
                    st.session_state.opportunities = opportunities
                    st.success(f"✅ Análisis completado: {len(opportunities)} oportunidades encontradas")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Mostrar resultados
    if st.session_state.opportunities is not None and not st.session_state.opportunities.empty:
        df = st.session_state.opportunities
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Oportunidades", len(df))
        with col2:
            st.metric("Upside Promedio", f"{df['upside_pct'].mean():.1f}%")
        with col3:
            st.metric("Max Upside", f"{df['upside_pct'].max():.1f}%")
        
        # Tabla
        st.dataframe(df, use_container_width=True)
        
        # Gráfico
        fig = px.bar(df, x='ticker', y='upside_pct', 
                     title='Upside por Empresa',
                     color='upside_pct',
                     color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    ticker = st.text_input("Ticker", value="AAPL")
    if st.button("Analizar"):
        st.info("Funcionalidad próximamente...")
