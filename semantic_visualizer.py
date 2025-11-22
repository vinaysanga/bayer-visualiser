import pandas as pd
import json
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI

class SemanticVisualizer:
    def __init__(self, openrouter_api_key, llm_model):
        print("   -> Loading BAAI/bge-m3 embedding model...")
        self.embedder = SentenceTransformer('BAAI/bge-m3')
        self.llm_model = llm_model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )

    def augment_dataframe(self, df, text_column='Havainto', n_clusters=6):
        """
        Phase 1: Semantic Clustering (Unchanged)
        """
        embeddings = self.embedder.encode(df[text_column].tolist(), show_progress_bar=True)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        df['Cluster_ID'] = kmeans.fit_transform(embeddings).argmax(axis=1)
        df['Semanttinen_Ryhmä'] = df['Cluster_ID'].apply(lambda x: f"Ryhmä {x+1}")
        return df

    def generate_visualization_code(self, user_query, df):
        """
        Phase 2: The Strict Architect
        """
        # Context Construction
        is_time_series = any(col for col in df.columns if 'pvm' in col.lower() or 'date' in col.lower())
        data_sample = df.head(3).to_markdown(index=False)
        columns_dtypes = df.dtypes.to_string()
        
        # STRICT SYSTEM PROMPT
        system_prompt = f"""
        You are a Python Data Expert. Your task is to write Python code to query a dataframe `df` and visualize it.

        INPUT CONTEXT:
        - User Query: "{user_query}"
        - Data Columns: {list(df.columns)}
        - Special Column: 'Semanttinen_Ryhmä' (AI-generated categories).
        - Time Column Available: {is_time_series}

        STRICT OUPUT RULES (NO HALLUCINATIONS):
        1. **Do NOT invent data.** You must derive all data from `df` using pandas operations (groupby, count, etc.).
        2. **Output Variables:** Your code MUST define exactly these three variables:
           - `chart_type`: A string (e.g., "bar", "line", "pie", "scatter").
           - `plot_data`: A pandas DataFrame containing ONLY the aggregated data to be plotted.
           - `fig`: The plotly figure object created from `plot_data`.
        3. **Language:** All labels in the chart must be in FINNISH.
        4. **Safety:** Return ONLY valid Python code. No markdown. No print().

        DECISION LOGIC:
        - If asking for "Trend/Timeline" -> Group by Date -> Chart Type: "line"
        - If asking for "Distribution/Count" -> Group by Semantic Group -> Chart Type: "bar" or "pie"
        
        Example Code Structure:
        # 1. Define Type
        chart_type = "bar"
        # 2. Extract Data (Strictly from df)
        plot_data = df['Semanttinen_Ryhmä'].value_counts().reset_index()
        plot_data.columns = ['Ryhmä', 'Määrä']
        # 3. Create Plot
        fig = px.bar(plot_data, x='Ryhmä', y='Määrä', title="Havainnot ryhmittäin")
        """

        user_message = f"Generate code for query: {user_query}"

        print(f"   -> Asking {self.llm_model} for strict data extraction...")
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0 # ZERO temperature for maximum logic strictness
        )

        code = response.choices[0].message.content
        code = code.replace("```python", "").replace("```", "").strip()
        return code

    def execute_code(self, code, df):
        """
        Phase 3: Execution & Verification
        Returns the Chart, The Type, and The Data.
        """
        local_vars = {'df': df, 'px': px, 'go': go, 'pd': pd}
        try:
            exec(code, globals(), local_vars)
            
            # Extract the required variables
            fig = local_vars.get('fig', None)
            chart_type = local_vars.get('chart_type', "Unknown")
            plot_data = local_vars.get('plot_data', pd.DataFrame())
            
            return {
                "success": True,
                "fig": fig,
                "chart_type": chart_type,
                "plot_data": plot_data
            }
        except Exception as e:
            print(f"Execution Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }