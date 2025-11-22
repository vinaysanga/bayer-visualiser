import streamlit as st
import pandas as pd
from semantic_visualizer import SemanticVisualizer

import os
from dotenv import load_dotenv

load_dotenv()

# CONFIG
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "anthropic/claude-3.5-sonnet")

st.set_page_config(page_title="Bayer HSE Visualizer", layout="wide")

if 'visualizer' not in st.session_state:
    st.session_state.visualizer = SemanticVisualizer(OPENROUTER_API_KEY, MODEL_NAME)

st.title("🛡️ Bayer HSE - Verified Analytics")
st.markdown("Strict 'No-Hallucination' pipeline: Raw Data -> Semantic Cluster -> Aggregated Table -> Visualization.")

# 1. LOAD
@st.cache_data
def load_data():
    try:
        return pd.read_excel("data/bayer_data.xlsx")
    except FileNotFoundError:
        st.error("File 'data/bayer_data.xlsx' not found.")
        return None

if 'df' not in st.session_state:
    st.session_state.df = load_data()

if st.session_state.df is not None:
    st.success(f"Loaded {len(st.session_state.df)} rows from bayer_data.xlsx")

# 2. PROCESS
if 'df' in st.session_state and st.session_state.df is not None:
    df = st.session_state.df
    
    # Auto-Process Data (Semantic Clustering)
    if 'processed_df' not in st.session_state:
        with st.spinner("Klusteroin dataa automaattisesti (BAAI/bge-m3)..."):
            # Auto-detect text column or default to first object column
            text_col = 'Havainto' if 'Havainto' in df.columns else df.select_dtypes(include=['object']).columns[0]
            st.session_state.processed_df = st.session_state.visualizer.augment_dataframe(df, text_col)
            st.success("Data klusteroitu onnistuneesti!")

    # 3. VISUALIZE
    if 'processed_df' in st.session_state:
        proc_df = st.session_state.processed_df
        
        st.divider()
        col_chat, col_viz = st.columns([1, 2])
        
        with col_chat:
            st.subheader("Valitse Analyysi")
            
            # Predefined prompts
            prompts = [
                "Näytä havaintojen määrä semanttisen ryhmän mukaan",
                "Näytä havaintojen kehitys ajan yli (jos päivämäärä)",
                "Mitkä ovat yleisimmät havaintotyypit?",
                "Jaa havainnot piirakkakaavioon ryhmittäin"
            ]
            
            selected_prompt = st.selectbox("Valitse valmis kysely:", prompts)
            
            # Optional: Allow custom prompt
            use_custom = st.checkbox("Kirjoita oma kysely")
            if use_custom:
                query = st.text_area("Kirjoita kysely:", selected_prompt)
            else:
                query = selected_prompt
            
            if st.button("Suorita Analyysi"):
                with st.spinner("Generoidaan visualisointia..."):
                    # A. Get Code
                    code = st.session_state.visualizer.generate_visualization_code(query, proc_df)
                    
                    # B. Execute and get DICT response
                    result = st.session_state.visualizer.execute_code(code, proc_df)
                    
                    if result["success"]:
                        st.session_state.last_result = result
                        st.session_state.last_code = code
                    else:
                        st.error(f"Virhe: {result['error']}")

        with col_viz:
            if 'last_result' in st.session_state:
                res = st.session_state.last_result
                
                # 1. Show Chart Type
                st.caption(f"🤖 Valittu visualisointityyppi: **{res['chart_type'].upper()}**")
                
                # 2. Show the Chart
                st.plotly_chart(res['fig'], width='content')
                
                # 3. VERIFICATION TABLE (The "Anti-Hallucination" Feature)
                with st.expander("📊 Tarkista taustadata (Verification Data)", expanded=True):
                    st.markdown("Tämä taulukko on laskettu suoraan datasta. Kuvaaja perustuu tähän.")
                    st.dataframe(res['plot_data'], width='content')
                    
                # 4. Show Code (Transparency)
                with st.expander("Näytä Python-koodi"):
                    st.code(st.session_state.last_code, language='python')