import pytest
import pandas as pd
import plotly.graph_objects as go
from semantic_visualizer import SemanticVisualizer
from unittest.mock import MagicMock, patch

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'Description': [
            'Slipped on wet floor',
            'Tripped over cable',
            'Fell down stairs',
            'Cut finger on paper',
            'Burned hand on stove'
        ]
    })

@pytest.fixture
def visualizer():
    # Mock OpenAI client to avoid needing a real key for unit tests
    with patch('semantic_visualizer.OpenAI') as mock_openai:
        viz = SemanticVisualizer(api_key="fake-key")
        viz.client = MagicMock()
        return viz

def test_augment_dataframe(visualizer, sample_df):
    # Test that columns are added
    augmented_df = visualizer.augment_dataframe(sample_df, 'Description', num_clusters=2)
    
    assert 'Cluster_ID' in augmented_df.columns
    assert 'Generated_Category' in augmented_df.columns
    assert len(augmented_df) == len(sample_df)
    assert augmented_df['Cluster_ID'].nunique() <= 2

def test_augment_dataframe_invalid_column(visualizer, sample_df):
    with pytest.raises(ValueError):
        visualizer.augment_dataframe(sample_df, 'NonExistentColumn')

def test_generate_visualization_mock(visualizer, sample_df):
    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "fig = px.bar(df, x='Generated_Category', title='Test Chart')"
    visualizer.client.chat.completions.create.return_value = mock_response
    
    # Ensure augmented_df has the necessary columns
    augmented_df = visualizer.augment_dataframe(sample_df, 'Description', num_clusters=2)
    
    # Run generation
    fig = visualizer.generate_visualization("Visualize this", augmented_df)
    
    # Check if a figure object is returned (Plotly figures are dict-like or objects)
    assert fig is not None
    # Basic check if it looks like a plotly figure
    assert hasattr(fig, 'show') or isinstance(fig, go.Figure)

def test_generate_visualization_no_client():
    viz = SemanticVisualizer() # No API key
    df = pd.DataFrame({'A': [1, 2]})
    with pytest.raises(ValueError):
        viz.generate_visualization("test", df)
