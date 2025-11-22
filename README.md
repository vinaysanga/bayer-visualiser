# Bayer HSE - Visualizer Demo

A two-stage LLM-powered analytics tool for safety observation data. This application uses AI to automatically categorize observations and generate intelligent visualizations based on natural language queries.

## Features

- **LLM-Driven Categorization**: Automatically analyzes and categorizes safety observations using AI
- **Intelligent Visualization**: Generates Python code for charts based on your questions
- **Multi-Scenario Support**: Load different Excel sheets for different analysis scenarios
- **Interactive UI**: Built with Streamlit for easy exploration
- **Configurable**: Adjust LLM behavior through `config.py`

## Architecture

```
Raw Data → LLM Categorization → LLM Visualization → Interactive Charts
```

1. **Stage 1**: LLM analyzes observations and creates relevant categories
2. **Stage 2**: LLM generates Python/Plotly code to visualize the data
3. **Execution**: Code runs and displays interactive charts with verification data

## Requirements

- Python 3.13
- OpenRouter API key (for LLM access)

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast dependency management and automatic Python version handling.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <your-repo-url>
cd sinceai

# Install dependencies (uv will automatically use Python 3.13 from .python-version)
uv sync
```

## Configuration

1. **Rename `.env.example` to `.env`** in the project root:

```bash
OPENROUTER_API_KEY=your_api_key_here
MODEL_NAME=google/gemini-2.5-pro  # or anthropic/claude-3.5-sonnet
```

2. **Adjust LLM behavior** (optional) in `config.py`:

```python
LLM_TEMPERATURE_CATEGORIZATION = 0.3  # Lower = more consistent categories
LLM_TEMPERATURE_VISUALIZATION = 0.0   # 0 = deterministic code generation
```

## Data Setup

1. Place your Excel file at `data/bayer_data.xlsx`
2. Ensure it has these columns:
   - `Otsikko`: Observation title
   - `Havainto`: Detailed description (Finnish text)
   - `havainto_pvm`: Observation date
   - `havainto_käsitelty_pvm`: Handling date

3. Create `data/prompts.json` with scenario-specific questions:

```json
{
  "Sheet1": "Mikä on yleisin turvallisuushavainto?",
  "Sheet2": "Näytä havainnot sijainnin mukaan"
}
```

## Usage

### Start the Application

```bash
uv run streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Workflow

1. **Select Scenario**: Choose a sheet from the sidebar
2. **Review Question**: See the pre-configured analysis question
3. **Run Analysis**: Click "Suorita Analyysi"
4. **View Results**: Explore the generated visualization
5. **Inspect Code**: Expand "Näytä Python-koodi" to see the generated code

## Project Structure

```
sinceai/
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
# or
MODEL_NAME=x-ai/grok-2-1212
```

### Adjust Temperature

Edit `config.py`:
```python
LLM_TEMPERATURE_CATEGORIZATION = 0.5  # More creative categories
LLM_TEMPERATURE_VISUALIZATION = 0.1   # Slightly varied visualizations
```

### Add New Scenarios

Add entries to `data/prompts.json`:
```json
{
  "NewSheet": "Your analysis question here"
}
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
- Check your internet connection (LLM calls require API access)
- Consider using a faster model (e.g., `grok-2-1212`)

### Python version issues
```bash
# uv automatically uses the version from .python-version
# If needed, you can install a specific version:
uv python install 3.13
```

## Notes

- The app sends observation data to OpenRouter's LLM API
- First run may be slower as it loads the embedding model
- Generated visualizations are deterministic (temperature=0.0)
- All data processing happens locally except LLM API calls

## Security

- Never commit `.env` file to version control
- Keep your OpenRouter API key secure
- Review generated code before trusting visualizations in production

## License

[Your License Here]

## Contributing

[Your contribution guidelines here]

## Contact

[Your contact information here]
