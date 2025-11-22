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

    def augment_dataframe(self, df, text_column='Description', n_clusters=6):
        """
        Phase 1: Semantic Clustering
        Target column is now 'Description' based on your Athena schema.
        """
        # Fallback: If 'Description' is missing (e.g. raw CSV is 'Havainto'), try to find it
        if text_column not in df.columns:
            # Check for common Finnish alias or default to 2nd column
            text_column = 'Havainto' if 'Havainto' in df.columns else df.columns[1]

        print(f"   -> Embedding column: {text_column}")
        # Force string conversion to avoid errors with mixed types
        embeddings = self.embedder.encode(df[text_column].astype(str).tolist(), show_progress_bar=True)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        df['Cluster_ID'] = kmeans.fit_transform(embeddings).argmax(axis=1)
        
        # Create the Semantic Cluster column used in the Prompt
        # df['Semantic_Cluster'] = df['Cluster_ID'].apply(lambda x: f"Semanttinen Ryhmä {x+1}")
        
        # NEW: Generate descriptive names for clusters
        print("   -> Generating descriptive names for clusters...")
        cluster_names = self._generate_cluster_names(df, text_column, n_clusters)
        df['Semantic_Cluster'] = df['Cluster_ID'].map(cluster_names)
        
        return df

    def _generate_cluster_names(self, df, text_column, n_clusters):
        """
        Generates short, descriptive names for each cluster using the LLM.
        """
        cluster_names = {}
        
        # Prepare samples for the LLM
        samples_text = ""
        for i in range(n_clusters):
            # Get up to 5 random samples from this cluster
            cluster_samples = df[df['Cluster_ID'] == i][text_column].sample(min(5, len(df[df['Cluster_ID'] == i]))).tolist()
            samples_text += f"Cluster {i}:\n" + "\n".join([f"- {s}" for s in cluster_samples]) + "\n\n"
            
        system_prompt = """
        You are a Safety Data Analyst. Your task is to name clusters of safety observations.
        
        I will provide samples of text from different clusters.
        For each cluster, generate a VERY SHORT (2-4 words), descriptive name in FINNISH.
        The name should summarize the common theme (e.g., "Liukastumiset", "Kemikaalit", "Suojavarusteet").
        
        Output format MUST be a JSON object where keys are "Cluster 0", "Cluster 1", etc., and values are the names.
        Example:
        {
            "Cluster 0": "Liukastumiset ja kaatumiset",
            "Cluster 1": "Puutteellinen suojaus"
        }
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here are the samples:\n\n{samples_text}"}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            response_content = response.choices[0].message.content
            names_json = json.loads(response_content)
            
            # Map "Cluster X" keys back to integers
            for key, name in names_json.items():
                try:
                    cluster_id = int(key.split(" ")[1])
                    cluster_names[cluster_id] = name
                except:
                    continue
                    
            # Fill in any missing clusters with generic names
            for i in range(n_clusters):
                if i not in cluster_names:
                    cluster_names[i] = f"Ryhmä {i+1}"
                    
        except Exception as e:
            print(f"Error generating cluster names: {e}")
            # Fallback to generic names
            for i in range(n_clusters):
                cluster_names[i] = f"Ryhmä {i+1}"
                
        return cluster_names

    def generate_visualization_code(self, user_query, df):
        """
        Phase 2: The Visualizer Architect (Updated with Athena Schema & Strict Logic)
        """
        # 1. Context Construction
        print(f"   [DEBUG] Dataframe Columns: {list(df.columns)}")
        has_time = 'Created' in df.columns
        
        # Create a sample for the LLM to see the data format
        data_sample = df.head(3).to_markdown(index=False)
        columns_dtypes = df.dtypes.to_string()
        
        # 2. THE REBUILT SYSTEM PROMPT (Aligned with your Summarizer)
        system_prompt = f"""
        You are a Data Visualization Architect. Your task is to generate Python code using 'plotly.express' to visualize worker safety observations.
        The data you receive is already filtered and processed.
        
        COLUMN DESCRIPTIONS (Context):
        - Id: Unique identifier. Use count(Id) for calculating volume/frequency.
        - Created: Timestamp. Use for Trend Analysis (Line Charts).
        - Name: Name of the record.
        - Description: Detailed Finnish text.
        - Status: Current status (e.g., 'Open', 'Closed'). Useful for Pie Charts.
        - Division: Department associated with the record. Useful for Bar Charts.
        - Observationtype: Type of observation. Useful for Bar Charts.
        - Semantic_Cluster: AI-generated category based on 'Description'. USE THIS if user asks for "Topics", "Themes", or "Groups".

        INSTRUCTIONS:
        1. Analyze the User's Request to determine the Best Chart Type.
           - Trends/Time -> Line Chart (x='Created')
           - Comparison/Counts -> Bar Chart (x='Division' or 'Semantic_Cluster')
           - Proportions -> Pie Chart (names='Observationtype' or 'Status')
        2. STRICTLY NO HALLUCINATIONS. You must derive 'plot_data' by aggregating `df` using pandas operations (groupby, count, resample).
        3. OUTPUT FORMAT: Return ONLY valid Python code defining exactly these 3 variables:
           - `chart_type` (string): e.g., "bar", "line", "pie".
           - `plot_data` (pandas DataFrame): The aggregated data used for the plot.
           - `fig` (plotly figure object): The final visualization.
        4. LANGUAGE: All chart titles, axis labels, and tooltips MUST be in the language of the User Request (likely Finnish).
        5. Do not use formatting like ** or markdown blocks.

        Example Logic:
        # User asks: "Show observations by Division"
        chart_type = "bar"
        plot_data = df.groupby('Division')['Id'].count().reset_index(name='Määrä')
        fig = px.bar(plot_data, x='Division', y='Määrä', title='Havainnot osastoittain')
        """

        user_message = f"""
        User Request: "{user_query}"
        
        Data Structure:
        {columns_dtypes}
        
        Data Sample:
        {data_sample}
        
        Generate the visualization code now:
        """

        print(f"   -> Asking {self.llm_model} to visualize...")
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0 # Zero temp for strict adherence
        )

        code = response.choices[0].message.content
        code = code.replace("```python", "").replace("```", "").strip()
        print(f"   [DEBUG] Generated Code:\n{code}\n   [DEBUG] End Code")
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
            print(f"   [ERROR] Execution Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }