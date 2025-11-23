# Bayer HSE - Visualizer Demo

A two-stage LLM-powered analytics tool for generating visualizations from data. This application uses AI to automatically categorize observations and generate intelligent visualizations based on natural language queries.

## Features

- **Simple API**: Single method `visualize(prompt, dataframe)` returns a Plotly figure
- **LLM-Driven**: Automatically analyzes and categorizes data using AI
- **Interactive Charts**: Generates Plotly visualizations ready for Streamlit
- **Configurable**: Adjust LLM behavior through `config.py`

## Architecture

```
prompt + DataFrame → LLM Analysis → LLM Code Generation → Plotly Figure
```

The system uses a two-stage LLM pipeline:
1. **Stage 1**: Analyzes data and creates relevant categories
2. **Stage 2**: Generates Python/Plotly code for visualization
3. **Output**: Returns an interactive Plotly figure

## Requirements
- **uv**
- **Python 3.13** (uv will automatically install this version if you don't have it installed)
- **OpenRouter API key** (for LLM access)

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast dependency management and automatic Python version handling.

1. **Install uv** (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone the repository**

Using HTTPS:
```bash
git clone https://github.com/vinaysanga/bayer-visualiser.git
```

Or using SSH:
```bash
git clone git@github.com:vinaysanga/bayer-visualiser.git
```

3. **Change directory**

```bash
cd bayer-visualiser
```

4. **Install dependencies** (uv will automatically use Python 3.13 from .python-version)

```bash
uv sync
```

## Configuration

1. **Rename `.env.example` to `.env`** in the project root, and fill in your OpenRouter API key:

```bash
OPENROUTER_API_KEY=your_api_key_here
MODEL_NAME=google/gemini-3-pro-preview
```

2. **Adjust LLM behavior** (optional) in `config.py`:

```python
LLM_TEMPERATURE_CATEGORIZATION = 0.3  # Lower = more consistent categories
LLM_TEMPERATURE_VISUALIZATION = 0.0   # 0 = deterministic code generation
```

## Usage

### Quick Start

```python
from semantic_visualizer import SemanticVisualizer
import pandas as pd

# Initialize
viz = SemanticVisualizer(
    openrouter_api_key="your_api_key",
    llm_model="google/gemini-2.5-pro"
)

# Load your data
df = pd.read_excel("your_data.xlsx")

# Generate visualization from natural language prompt
fig = viz.visualize("Show trends over time", df)

# Display in Streamlit
import streamlit as st
st.plotly_chart(fig)

# Or display standalone
fig.show()
```

### Running the Demo Application

```bash
uv run streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Demo Workflow

1. **Select Scenario**: Choose a sheet from the sidebar
2. **Review Question**: See the pre-configured analysis question
3. **Run Analysis**: Click "Suorita Analyysi"
4. **View Results**: Explore the generated visualization

## Project Structure

```
bayer-visualiser/
├── app.py                      # Main Streamlit application
├── semantic_visualizer.py      # Core LLM logic
├── config.py                   # Configuration settings
├── pyproject.toml              # Project metadata and dependencies
├── .python-version             # Python version (3.13)
├── .env                        # Environment variables (create this)
├── .venv/                      # Virtual environment (created by uv)
├── data/
│   ├── bayer_data.xlsx        # Your Excel data
│   └── prompts.json           # Scenario questions
└── README.md                  # This file
```

## Customization

### Change LLM Model

Edit `.env`:
```bash
MODEL_NAME=anthropic/claude-3.5-sonnet
# or
MODEL_NAME=google/gemini-2.5-pro
# or any other model from OpenRouter
```

### Adjust Temperature

Edit `config.py`:
```python
LLM_TEMPERATURE_CATEGORIZATION = 0.5  # More creative categories
LLM_TEMPERATURE_VISUALIZATION = 0.1   # Slightly varied visualizations
```

## Troubleshooting

### "Module not found" errors
```bash
# Reinstall dependencies
uv sync
```

### "API key not found"
- Ensure `.env` file exists in project root
- Check that `OPENROUTER_API_KEY` is set correctly

### Slow performance
- Consider using a faster model from OpenRouter

### Python version issues
```bash
# uv automatically uses the version from .python-version
# If needed, you can install a specific version:
uv python install 3.13
```

## Notes

- The app sends observation data to OpenRouter's LLM API
- First run may be slower as it loads the streamlit app
- Generated visualizations are deterministic (temperature=0.0)
- All data processing happens locally except LLM API calls