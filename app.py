import os
import warnings
import streamlit as st
import pandas as pd
from semantic_visualizer import SemanticVisualizer

from dotenv import load_dotenv
import json

# Suppress tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

warnings.filterwarnings('ignore')


load_dotenv()

# CONFIG
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "anthropic/claude-3.5-sonnet")

st.set_page_config(page_title="Bayer HSE Visualizer", layout="wide")

if 'visualizer' not in st.session_state:
    st.session_state.visualizer = SemanticVisualizer(OPENROUTER_API_KEY, MODEL_NAME)

st.title("Bayer HSE - Visualizer Demo")

# 1. LOAD DEMO DATA
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
        
        if selected_sheet:
            sheet_changed = 'current_sheet' not in st.session_state or st.session_state.current_sheet != selected_sheet
            
            st.session_state.df = pd.read_excel(xl, sheet_name=selected_sheet)
            st.success(f"Ladattu '{selected_sheet}': {len(st.session_state.df)} riviä.")
            
            if sheet_changed:
                st.session_state.current_sheet = selected_sheet
                for key in ['processed_df', 'last_result', 'last_code', 'last_proc_df', 'is_processing']:
                    if key in st.session_state:
                        del st.session_state[key]

if 'df' not in st.session_state:
    st.stop()

if st.session_state.df is not None:
    pass


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

# 2. PROCESS (runs when is_processing is True)
if st.session_state.get('is_processing', False):
    st.empty()
    
    df = st.session_state.df
    current_sheet = st.session_state.get('current_sheet', '')
    default_prompt = prompts_map.get(current_sheet, "Valitse analyysi...")
    
    with st.spinner("Luodaan visuaalisointia..."):
        try:
            fig = st.session_state.visualizer.visualize(default_prompt, df)
            
            st.session_state.last_result = {
                "success": True,
                "fig": fig,
                "chart_type": "visualization"
            }
        except Exception as e:
            st.error(f"Virhe: {str(e)}")
            st.session_state.last_result = None
    
    st.session_state.is_processing = False
    st.rerun()


# 3. SHOW UI (only if not processing)
if 'df' in st.session_state and st.session_state.df is not None and not st.session_state.get('is_processing', False):
    df = st.session_state.df
    
    st.divider()
    col_chat, col_viz = st.columns([1, 2])
    
    with col_chat:
        st.subheader("Analyysi")
        
        current_sheet = st.session_state.get('current_sheet', '')
        default_prompt = prompts_map.get(current_sheet, "Valitse analyysi...")
        
        st.info(f"**Skenaarion kysymys:**\n\n{default_prompt}")
        
        if st.button("Suorita Analyysi"):
            st.session_state.is_processing = True
            st.rerun()

    with col_viz:
        if 'last_result' in st.session_state and st.session_state.last_result:
            res = st.session_state.last_result
            
            st.plotly_chart(res['fig'], width='content')