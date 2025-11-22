import os
# Suppress tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import streamlit as st
import pandas as pd
from semantic_visualizer import SemanticVisualizer

from dotenv import load_dotenv

load_dotenv()

# CONFIG
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "anthropic/claude-3.5-sonnet")

st.set_page_config(page_title="Bayer HSE Visualizer", layout="wide")

if 'visualizer' not in st.session_state:
    st.session_state.visualizer = SemanticVisualizer(OPENROUTER_API_KEY, MODEL_NAME)

st.title("🛡️ Bayer HSE - Verified Analytics")
st.markdown("LLM-powered visualization: Raw Data → Intelligent Analysis → Aggregated Table → Visualization.")

# 1. LOAD
@st.cache_resource
def load_excel_file():
    try:
        return pd.ExcelFile("data/bayer_data.xlsx")
    except FileNotFoundError:
        st.error("File 'data/bayer_data.xlsx' not found.")
        return None

xl = load_excel_file()

if xl:
    with st.sidebar:
        st.header("Skenaario (Data)")
        sheet_names = xl.sheet_names
        selected_sheet = st.selectbox("Valitse aineisto:", sheet_names)
        
        # Load the selected sheet
        if selected_sheet:
            # Check if sheet changed BEFORE loading new data
            sheet_changed = 'current_sheet' not in st.session_state or st.session_state.current_sheet != selected_sheet
            
            st.session_state.df = pd.read_excel(xl, sheet_name=selected_sheet)
            st.success(f"Ladattu '{selected_sheet}': {len(st.session_state.df)} riviä.")
            
            # Reset processed state when sheet changes
            if sheet_changed:
                st.session_state.current_sheet = selected_sheet
                # Clear all analysis-related session state
                for key in ['processed_df', 'last_result', 'last_code', 'last_proc_df']:
                    if key in st.session_state:
                        del st.session_state[key]

if 'df' not in st.session_state:
    # Fallback if something goes wrong
    st.stop()

if st.session_state.df is not None:
    # st.success(f"Loaded {len(st.session_state.df)} rows from bayer_data.xlsx") # Moved to sidebar
    pass

import json

# Load Prompts
@st.cache_data
def load_prompts():
    try:
        with open("data/prompts.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("File 'data/prompts.json' not found.")
        return {}

prompts_map = load_prompts()

# 2. SHOW UI
if 'df' in st.session_state and st.session_state.df is not None:
    df = st.session_state.df
    
    st.divider()
    col_chat, col_viz = st.columns([1, 2])
    
    with col_chat:
        st.subheader("Analyysi")
        
        # Get prompt for current sheet
        current_sheet = st.session_state.get('current_sheet', '')
        default_prompt = prompts_map.get(current_sheet, "Valitse analyysi...")
        
        st.info(f"**Skenaarion kysymys:**\n\n{default_prompt}")
        
        if st.button("Suorita Analyysi"):
            with st.spinner("Analysoidaan ja visualisoidaan..."):
                # A. Get Code (LLM handles everything including clustering/categorization)
                code = st.session_state.visualizer.generate_visualization_code(default_prompt, df)
                
                # B. Execute and get DICT response
                result = st.session_state.visualizer.execute_code(code, df)
                
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