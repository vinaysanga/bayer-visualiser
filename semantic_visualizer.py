import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
import config

class SemanticVisualizer:
    def __init__(self, openrouter_api_key, llm_model):
        self.llm_model = llm_model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
    
    def visualize(self, prompt: str, df: pd.DataFrame):
        """
        Main API method - Returns a Plotly figure given a prompt and dataframe.
        
        Args:
            prompt: Natural language query describing what to visualize
            df: Pandas DataFrame containing the data to visualize
            
        Returns:
            plotly.graph_objects.Figure: Interactive visualization
            
        Raises:
            Exception: If visualization generation or execution fails
            
        Example:
            >>> viz = SemanticVisualizer(api_key, model)
            >>> fig = viz.visualize("Show trends over time", my_dataframe)
            >>> fig.show()  # or st.plotly_chart(fig) in Streamlit
        """
        # Stage 1: Enrich data with LLM-generated categories
        enriched_df = self.llm_cluster_dataframe(df, prompt)
        
        # Stage 2: Generate visualization code
        code = self.generate_visualization_code(prompt, enriched_df)
        
        # Stage 3: Execute and return figure
        result = self.execute_code(code, enriched_df)
        
        if result["success"]:
            return result["fig"]
        else:
            raise Exception(f"Visualization failed: {result['error']}")
    

    def llm_cluster_dataframe(self, df, user_query):
        """
        Phase 1: LLM-based Data Transformation
        The LLM analyzes the observations and transforms the data as needed to answer the question.
        """
        print(f"   -> LLM analyzing and transforming data...")
        
        # Send all observations to LLM for analysis
        all_observations = df['Havainto'].tolist()
        
        system_prompt = """
        You are a Safety Data Analyst. Your task is to analyze safety observations and transform the data to best answer the user's question.
        
        I will provide you with safety observations in Finnish and a specific analysis question. Your job is to:
        1. Understand what the question is asking
        2. Decide what data transformations/categorizations would help answer it
        3. Create appropriate categories, groupings, or derived fields as needed
        
        You have complete freedom to:
        - Create as many or as few categories as makes sense
        - Define categories based on keywords, patterns, themes, or any other logic
        - Add multiple derived columns if needed
        - Use any categorization scheme that helps answer the question
        
        Return a JSON object with:
        1. "transformations": A list of transformations to apply, where each transformation has:
           - "column_name": Name of the new column to create
           - "description": What this column represents
           - "classification_logic": How to classify each observation (as a dictionary mapping category names to keyword lists or logic)
        
        Example output:
        {
            "transformations": [
                {
                    "column_name": "Safety_Theme",
                    "description": "Main safety theme of the observation",
                    "classification_logic": {
                        "Liukastumiset": ["liukast", "kaatu", "märkä", "lattia"],
                        "Kemikaalit": ["kemikaali", "roiske", "aine"],
                        "Sähköturvallisuus": ["sähkö", "johto", "pistorasia"],
                        "Muut": []
                    }
                }
            ]
        }
        
        Note: For the "Muut" or default category, use an empty list []. It will catch everything not matched by other categories.
        """
        
        user_message = f"""
        User's Analysis Question: "{user_query}"
        
        All Observations ({len(df)} total):
        {chr(10).join([f"{i+1}. {obs}" for i, obs in enumerate(all_observations)])}
        
        Analyze these observations and decide how to transform the data to best answer the question.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=config.LLM_TEMPERATURE_CATEGORIZATION,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            transformations = result.get("transformations", [])
            
            if not transformations:
                print("   -> No transformations suggested by LLM")
                return df.copy()
            
            df_copy = df.copy()
            
            # Apply each transformation
            for trans in transformations:
                column_name = trans.get("column_name", "LLM_Category")
                classification_logic = trans.get("classification_logic", {})
                
                print(f"   -> Creating column '{column_name}' with {len(classification_logic)} categories")
                
                # Create a classification function
                def classify_observation(text):
                    text_lower = str(text).lower()
                    for category, keywords in classification_logic.items():
                        if not keywords:  # Empty list means default/catch-all category
                            continue
                        if any(keyword in text_lower for keyword in keywords):
                            return category
                    # Return the first category with empty keywords list, or "Luokittelematon"
                    for category, keywords in classification_logic.items():
                        if not keywords:
                            return category
                    return "Luokittelematon"
                
                df_copy[column_name] = df_copy['Havainto'].apply(classify_observation)
            
            return df_copy
            
        except Exception as e:
            print(f"   [ERROR] LLM transformation failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: return original dataframe
            return df.copy()

    def generate_visualization_code(self, user_query, df):
        """
        Phase 2: The Visualizer Architect
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
        - Otsikko: Title/Name of the observation
        - Havainto: Detailed Finnish text description of the safety observation
        - havainto_pvm: Observation date (timestamp)
        - havainto_käsitelty_pvm: Date when observation was handled (timestamp)

        INSTRUCTIONS:
        1. Analyze the User's Request and the available data columns.
        2. Choose the Best Visualization type (bar, line, pie, scatter, etc.) based on the question.
        3. **Data Processing:** You MUST derive 'plot_data' by aggregating `df` using pandas operations.
           - For categorization/grouping needs, you can analyze the 'Havainto' text directly using string operations, keyword matching, or create categories on-the-fly.
           - For time-based analysis, use 'havainto_pvm' or 'havainto_käsitelty_pvm'.
           - You can calculate derived metrics like processing time: (havainto_käsitelty_pvm - havainto_pvm).
        4. **CRITICAL - Date Handling:**
           - ALWAYS use pd.to_datetime() when working with date columns
           - For time-based grouping, use .dt accessor (e.g., df['date'].dt.month, df['date'].dt.year)
           - Ensure dates are properly parsed before any operations
        5. **CRITICAL - Number Handling:**
           - ALWAYS verify numeric columns with pd.to_numeric() if needed
           - Handle NaN values explicitly before aggregations
           - Use proper aggregation functions (count, sum, mean) - never assume data types
        6. OUTPUT FORMAT: Return ONLY valid Python code defining exactly these 3 variables:
           - `chart_type` (string): e.g., "bar", "line", "pie".
           - `plot_data` (pandas DataFrame): The aggregated data used for the plot.
           - `fig` (plotly figure object): The final visualization.
        7. LANGUAGE: All chart titles, axis labels, and tooltips MUST be in Finnish.
        8. Do not use formatting like ** or markdown blocks.

        Example Logic:
        # User asks: "Categorize observations by safety theme"
        chart_type = "bar"
        # Create categories by analyzing the text
        df['Theme'] = df['Havainto'].apply(lambda x: 'Liukastumiset' if 'liukast' in x.lower() else 'Muu')
        plot_data = df.groupby('Theme').size().reset_index(name='Määrä')
        fig = px.bar(plot_data, x='Theme', y='Määrä', title='Havainnot teemoittain')
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
            temperature=config.LLM_TEMPERATURE_VISUALIZATION
        )

        code = response.choices[0].message.content
        code = code.replace("```python", "").replace("```", "").strip()
        print(f"   [DEBUG] Code generated")
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