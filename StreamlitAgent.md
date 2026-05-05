# StreamlitAgent.md - Databricks Data Chatbot & Dashboard

## Instructions for AI Agent

**Purpose:** Build a Streamlit application that connects to Azure Databricks, reads datasets, provides chatbot-based data querying, and displays interactive Plotly visualizations.

**Key Features:**
- 🔗 **Databricks Connection**: Secure connection to Azure Databricks workspace
- 📊 **Dataset Reading**: Load and cache datasets from Databricks tables/volumes
- 🤖 **Chatbot Interface**: Natural language queries to explore and analyze data
- 📈 **Interactive Dashboard**: Plotly charts with filtering and drill-down capabilities
- ⚡ **Performance Optimized**: Caching, session state management, and efficient data handling

---

## Quick Start

### Prerequisites
- Azure Databricks workspace with data
- Python 3.8+ environment
- Databricks SDK and Streamlit installed
- Access to Databricks tables or volumes

### Installation
```bash
pip install streamlit databricks-sdk plotly pandas numpy openai
```

### Basic App Structure
```python
import streamlit as st
from databricks.sdk import WorkspaceClient
import plotly.express as px
import pandas as pd

# Initialize Databricks connection
@st.cache_resource
def get_databricks_client():
    return WorkspaceClient()

# Load data from Databricks
@st.cache_data
def load_dataset(table_name: str) -> pd.DataFrame:
    client = get_databricks_client()
    # Implementation here
    pass

# Main app
def main():
    st.title("📊 Databricks Data Explorer")

    # Sidebar for dataset selection
    with st.sidebar:
        dataset = st.selectbox("Select Dataset", ["sales", "customers", "products"])

    # Load data
    df = load_dataset(dataset)

    # Chatbot interface
    chat_interface(df)

    # Dashboard
    create_dashboard(df)

if __name__ == "__main__":
    main()
```

---

## Project Structure

```
databricks-chatbot-app/
├── app.py                    # Main Streamlit application
├── utils/
│   ├── databricks_connector.py  # Databricks connection utilities
│   ├── data_loader.py          # Dataset loading functions
│   └── query_processor.py      # Natural language query processing
├── components/
│   ├── chatbot.py             # Chat interface component
│   ├── dashboard.py           # Dashboard component
│   └── filters.py             # Data filtering components
├── requirements.txt           # Python dependencies
├── .streamlit/
│   ├── config.toml           # Streamlit configuration
│   └── secrets.toml.example  # Secrets template
├── README.md                 # Documentation
└── StreamlitAgent.md         # This guide
```

---

## Implementation Guide

### 1. Databricks Connection Setup

#### Environment Variables
```bash
# .env file or environment variables
DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
DATABRICKS_TOKEN=dapi-your-token-here
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
```

#### Connection Module (`utils/databricks_connector.py`)
```python
import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
import streamlit as st

@st.cache_resource
def get_databricks_client() -> WorkspaceClient:
    """Create and cache Databricks workspace client."""
    try:
        # Try environment variables first
        host = os.getenv('DATABRICKS_HOST')
        token = os.getenv('DATABRICKS_TOKEN')

        if host and token:
            return WorkspaceClient(host=host, token=token)

        # Try Streamlit secrets
        if hasattr(st, 'secrets') and 'databricks' in st.secrets:
            config = st.secrets['databricks']
            return WorkspaceClient(
                host=config['host'],
                token=config['token']
            )

        # Try default authentication (for Databricks environments)
        return WorkspaceClient()

    except Exception as e:
        st.error(f"Failed to connect to Databricks: {str(e)}")
        st.stop()

@st.cache_resource
def get_sql_warehouse():
    """Get SQL warehouse connection for direct SQL queries."""
    client = get_databricks_client()
    # Return warehouse connection
    return client

def test_connection():
    """Test Databricks connection and return workspace info."""
    try:
        client = get_databricks_client()
        # Test by listing clusters
        clusters = list(client.clusters.list())
        return {
            'status': 'connected',
            'clusters_count': len(clusters),
            'workspace_url': client.config.host
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }
```

### 2. Data Loading Module (`utils/data_loader.py`)

#### Load from Unity Catalog Tables
```python
import pandas as pd
from databricks.sdk import WorkspaceClient
import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_table_data(catalog: str, schema: str, table: str) -> pd.DataFrame:
    """Load data from Unity Catalog table."""
    client = get_databricks_client()

    try:
        # Use SQL warehouse for queries
        warehouse = get_sql_warehouse()

        query = f"SELECT * FROM {catalog}.{schema}.{table}"
        result = warehouse.query.execute(query)

        # Convert to DataFrame
        df = pd.DataFrame(result.result.data, columns=result.result.columns)
        return df

    except Exception as e:
        st.error(f"Failed to load table {catalog}.{schema}.{table}: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_volume_file(volume_path: str, file_name: str) -> pd.DataFrame:
    """Load data from Unity Catalog volume file."""
    client = get_databricks_client()

    try:
        # Download file from volume
        file_content = client.files.download(f"{volume_path}/{file_name}")

        # Parse based on file extension
        if file_name.endswith('.csv'):
            df = pd.read_csv(file_content.contents)
        elif file_name.endswith('.json'):
            df = pd.read_json(file_content.contents)
        elif file_name.endswith('.parquet'):
            df = pd.read_parquet(file_content.contents)
        else:
            raise ValueError(f"Unsupported file format: {file_name}")

        return df

    except Exception as e:
        st.error(f"Failed to load file {volume_path}/{file_name}: {str(e)}")
        return pd.DataFrame()

def get_available_datasets() -> dict:
    """Get list of available datasets from Databricks."""
    client = get_databricks_client()

    datasets = {}

    try:
        # Get catalogs
        catalogs = client.query.execute("SHOW CATALOGS")
        for catalog in catalogs.result.data:
            catalog_name = catalog[0]
            datasets[catalog_name] = {}

            # Get schemas for each catalog
            schemas = client.query.execute(f"SHOW SCHEMAS IN {catalog_name}")
            for schema in schemas.result.data:
                schema_name = schema[0]
                datasets[catalog_name][schema_name] = []

                # Get tables for each schema
                tables = client.query.execute(f"SHOW TABLES IN {catalog_name}.{schema_name}")
                for table in tables.result.data:
                    table_name = table[1]  # Table name is in second column
                    datasets[catalog_name][schema_name].append(table_name)

    except Exception as e:
        st.warning(f"Could not fetch dataset list: {str(e)}")

    return datasets
```

### 3. Query Processing Module (`utils/query_processor.py`)

#### Natural Language to SQL Conversion
```python
import re
import pandas as pd
from typing import Tuple, Optional
import streamlit as st

class DataQueryProcessor:
    """Process natural language queries and convert to data operations."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.column_info = self._analyze_columns()

    def _analyze_columns(self) -> dict:
        """Analyze DataFrame columns for query processing."""
        info = {}
        for col in self.df.columns:
            dtype = self.df[col].dtype
            if pd.api.types.is_numeric_dtype(dtype):
                info[col] = {
                    'type': 'numeric',
                    'min': float(self.df[col].min()),
                    'max': float(self.df[col].max()),
                    'unique_count': self.df[col].nunique()
                }
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                info[col] = {
                    'type': 'datetime',
                    'min': str(self.df[col].min()),
                    'max': str(self.df[col].max())
                }
            else:
                info[col] = {
                    'type': 'categorical',
                    'unique_values': self.df[col].unique()[:10].tolist(),  # Top 10 unique values
                    'unique_count': self.df[col].nunique()
                }
        return info

    def process_query(self, query: str) -> Tuple[str, pd.DataFrame]:
        """Process natural language query and return response."""
        query_lower = query.lower().strip()

        # Basic query patterns
        if self._is_aggregation_query(query_lower):
            return self._handle_aggregation_query(query_lower)
        elif self._is_filter_query(query_lower):
            return self._handle_filter_query(query_lower)
        elif self._is_sort_query(query_lower):
            return self._handle_sort_query(query_lower)
        elif self._is_info_query(query_lower):
            return self._handle_info_query(query_lower)
        else:
            return self._handle_general_query(query_lower)

    def _is_aggregation_query(self, query: str) -> bool:
        """Check if query is asking for aggregations."""
        agg_keywords = ['count', 'sum', 'average', 'avg', 'mean', 'total', 'maximum', 'minimum', 'max', 'min']
        return any(keyword in query for keyword in agg_keywords)

    def _is_filter_query(self, query: str) -> bool:
        """Check if query is asking for filtering."""
        filter_keywords = ['where', 'filter', 'show only', 'find', 'get']
        return any(keyword in query for keyword in filter_keywords)

    def _is_sort_query(self, query: str) -> bool:
        """Check if query is asking for sorting."""
        sort_keywords = ['sort', 'order', 'arrange', 'rank']
        return any(keyword in query for keyword in sort_keywords)

    def _is_info_query(self, query: str) -> bool:
        """Check if query is asking for dataset information."""
        info_keywords = ['describe', 'info', 'summary', 'columns', 'fields', 'structure']
        return any(keyword in query for keyword in info_keywords)

    def _handle_aggregation_query(self, query: str) -> Tuple[str, pd.DataFrame]:
        """Handle aggregation queries like 'count records', 'average price'."""
        response = ""
        result_df = self.df.copy()

        if 'count' in query:
            total_count = len(self.df)
            response = f"The dataset contains {total_count:,} records."

        elif any(word in query for word in ['average', 'avg', 'mean']):
            numeric_cols = [col for col, info in self.column_info.items() if info['type'] == 'numeric']
            if numeric_cols:
                col = self._find_column_in_query(query, numeric_cols)
                if col:
                    avg_val = self.df[col].mean()
                    response = f"The average {col} is {avg_val:.2f}."
                    result_df = self.df[[col]].describe()
                else:
                    response = f"Please specify which numeric column to average. Available: {', '.join(numeric_cols)}"
            else:
                response = "No numeric columns found for averaging."

        elif 'sum' in query or 'total' in query:
            numeric_cols = [col for col, info in self.column_info.items() if info['type'] == 'numeric']
            if numeric_cols:
                col = self._find_column_in_query(query, numeric_cols)
                if col:
                    sum_val = self.df[col].sum()
                    response = f"The total {col} is {sum_val:,.2f}."
                else:
                    response = f"Please specify which numeric column to sum. Available: {', '.join(numeric_cols)}"
            else:
                response = "No numeric columns found for summing."

        return response, result_df

    def _handle_filter_query(self, query: str) -> Tuple[str, pd.DataFrame]:
        """Handle filter queries."""
        # Simple filtering logic - can be enhanced with NLP
        result_df = self.df.copy()
        response = "Here's the filtered data:"

        # Look for numeric filters
        for col, info in self.column_info.items():
            if info['type'] == 'numeric':
                # Simple pattern matching for > < = conditions
                patterns = [
                    (r'greater than (\d+)', '>', lambda x: float(x)),
                    (r'more than (\d+)', '>', lambda x: float(x)),
                    (r'less than (\d+)', '<', lambda x: float(x)),
                    (r'equals? (\d+)', '==', lambda x: float(x)),
                ]

                for pattern, op, converter in patterns:
                    match = re.search(pattern, query)
                    if match and col.lower() in query:
                        try:
                            value = converter(match.group(1))
                            if op == '>':
                                result_df = result_df[result_df[col] > value]
                            elif op == '<':
                                result_df = result_df[result_df[col] < value]
                            elif op == '==':
                                result_df = result_df[result_df[col] == value]
                            response = f"Filtered {col} {op} {value}. Found {len(result_df)} records."
                            break
                        except ValueError:
                            continue

        return response, result_df

    def _handle_sort_query(self, query: str) -> Tuple[str, pd.DataFrame]:
        """Handle sorting queries."""
        result_df = self.df.copy()
        response = "Data sorted as requested."

        if 'descending' in query or 'highest' in query:
            ascending = False
        else:
            ascending = True

        # Find column to sort by
        all_cols = list(self.column_info.keys())
        sort_col = self._find_column_in_query(query, all_cols)

        if sort_col:
            result_df = result_df.sort_values(sort_col, ascending=ascending)
            response = f"Data sorted by {sort_col} ({'ascending' if ascending else 'descending'})."
        else:
            response = f"Please specify which column to sort by. Available: {', '.join(all_cols)}"

        return response, result_df

    def _handle_info_query(self, query: str) -> Tuple[str, pd.DataFrame]:
        """Handle information queries about the dataset."""
        if 'columns' in query or 'fields' in query:
            cols_info = []
            for col, info in self.column_info.items():
                if info['type'] == 'numeric':
                    cols_info.append(f"{col} (numeric, range: {info['min']:.1f} - {info['max']:.1f})")
                elif info['type'] == 'datetime':
                    cols_info.append(f"{col} (datetime, {info['min']} to {info['max']})")
                else:
                    cols_info.append(f"{col} (categorical, {info['unique_count']} unique values)")

            response = f"Dataset has {len(self.df)} rows and {len(self.df.columns)} columns:\n" + "\n".join(f"• {info}" for info in cols_info)
        else:
            response = f"This dataset contains {len(self.df):,} rows and {len(self.df.columns)} columns. Column types: {', '.join([f'{col} ({info[\"type\"]})' for col, info in self.column_info.items()])}"

        return response, self.df.head(10)

    def _handle_general_query(self, query: str) -> Tuple[str, pd.DataFrame]:
        """Handle general queries."""
        if len(query) < 3:
            return "Please ask a more specific question about the data.", self.df.head()

        # Look for column mentions
        mentioned_cols = []
        for col in self.df.columns:
            if col.lower() in query:
                mentioned_cols.append(col)

        if mentioned_cols:
            response = f"I found these columns in your query: {', '.join(mentioned_cols)}. Here are the first few rows:"
        else:
            response = "I can help you analyze this data. Try asking about counts, averages, filtering, or sorting."

        return response, self.df.head(10)

    def _find_column_in_query(self, query: str, candidates: list) -> Optional[str]:
        """Find which column is mentioned in the query."""
        for col in candidates:
            if col.lower() in query:
                return col
        return None
```

### 4. Chatbot Component (`components/chatbot.py`)

#### Chat Interface Implementation
```python
import streamlit as st
import pandas as pd
from utils.query_processor import DataQueryProcessor
from datetime import datetime

def chat_interface(df: pd.DataFrame):
    """Create an interactive chat interface for data queries."""

    st.header("🤖 Data Chatbot")

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Initialize query processor
    if "query_processor" not in st.session_state or st.session_state.get("current_df_shape") != df.shape:
        st.session_state.query_processor = DataQueryProcessor(df)
        st.session_state.current_df_shape = df.shape

    # Display chat history
    chat_container = st.container(height=400)

    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "dataframe" in message and message["dataframe"] is not None:
                    st.dataframe(message["dataframe"], use_container_width=True)

    # Chat input
    if prompt := st.chat_input("Ask me anything about your data..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Process query
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your data..."):
                try:
                    response_text, result_df = st.session_state.query_processor.process_query(prompt)

                    st.markdown(response_text)

                    if result_df is not None and len(result_df) > 0:
                        # Show results
                        if len(result_df) <= 100:  # Show full data for small results
                            st.dataframe(result_df, use_container_width=True)
                        else:  # Show summary for large results
                            st.dataframe(result_df.head(50), use_container_width=True)
                            st.info(f"Showing first 50 of {len(result_df)} results")

                        # Store result in message
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": response_text,
                            "dataframe": result_df
                        })
                    else:
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": response_text
                        })

                except Exception as e:
                    error_msg = f"Sorry, I encountered an error processing your query: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

    # Clear chat button
    if st.button("🗑️ Clear Chat", key="clear_chat"):
        st.session_state.chat_messages = []
        st.rerun()

def get_quick_suggestions(df: pd.DataFrame) -> list:
    """Generate quick query suggestions based on data."""
    suggestions = []

    # Basic info
    suggestions.append("What columns are in this dataset?")
    suggestions.append(f"How many records are there? (Total: {len(df):,})")

    # Numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if numeric_cols:
        suggestions.append(f"What's the average {numeric_cols[0]}?")
        if len(numeric_cols) > 1:
            suggestions.append(f"Show me {numeric_cols[0]} vs {numeric_cols[1]}")

    # Categorical columns
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_cols:
        suggestions.append(f"What are the unique values in {cat_cols[0]}?")

    return suggestions[:5]  # Return top 5 suggestions
```

### 5. Dashboard Component (`components/dashboard.py`)

#### Interactive Dashboard with Plotly
```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any

def create_dashboard(df: pd.DataFrame):
    """Create an interactive dashboard with multiple visualizations."""

    st.header("📊 Interactive Dashboard")

    if df.empty:
        st.warning("No data available for visualization.")
        return

    # Filters sidebar
    with st.sidebar:
        st.subheader("🎛️ Filters")

        # Get column types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()

        # Numeric filters
        if numeric_cols:
            st.subheader("Numeric Filters")
            for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                min_val, max_val = float(df[col].min()), float(df[col].max())
                filter_range = st.slider(
                    f"{col} range",
                    min_val, max_val,
                    (min_val, max_val),
                    key=f"filter_{col}"
                )
                df = df[(df[col] >= filter_range[0]) & (df[col] <= filter_range[1])]

        # Categorical filters
        if categorical_cols:
            st.subheader("Category Filters")
            for col in categorical_cols[:2]:  # Limit to first 2 categorical columns
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) <= 20:  # Only show filter if not too many values
                    selected_vals = st.multiselect(
                        f"Filter {col}",
                        options=unique_vals,
                        default=list(unique_vals),
                        key=f"cat_filter_{col}"
                    )
                    if selected_vals:
                        df = df[df[col].isin(selected_vals)]

    # Main dashboard area
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📊 Distributions", "🔗 Correlations", "📋 Raw Data"])

    with tab1:
        create_overview_tab(df, numeric_cols, categorical_cols)

    with tab2:
        create_distributions_tab(df, numeric_cols, categorical_cols)

    with tab3:
        create_correlations_tab(df, numeric_cols)

    with tab4:
        create_raw_data_tab(df)

def create_overview_tab(df: pd.DataFrame, numeric_cols: list, categorical_cols: list):
    """Create overview dashboard with key metrics and charts."""

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Records", f"{len(df):,}")

    with col2:
        st.metric("Columns", len(df.columns))

    if numeric_cols:
        with col3:
            st.metric("Numeric Columns", len(numeric_cols))

    if categorical_cols:
        with col4:
            st.metric("Categories", len(categorical_cols))

    # Quick visualizations
    if len(df) > 0:
        col1, col2 = st.columns(2)

        with col1:
            if numeric_cols and len(numeric_cols) >= 2:
                # Scatter plot
                x_col = st.selectbox("X-axis", numeric_cols, key="scatter_x")
                y_col = st.selectbox("Y-axis", [c for c in numeric_cols if c != x_col], key="scatter_y")

                fig = px.scatter(
                    df, x=x_col, y=y_col,
                    title=f"{x_col} vs {y_col}",
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Need at least 2 numeric columns for scatter plot")

        with col2:
            if categorical_cols:
                # Bar chart for categorical data
                cat_col = st.selectbox("Category Column", categorical_cols, key="bar_cat")
                top_n = st.slider("Top N categories", 5, 20, 10, key="top_n")

                # Get top categories
                value_counts = df[cat_col].value_counts().head(top_n)

                fig = px.bar(
                    x=value_counts.index,
                    y=value_counts.values,
                    title=f"Top {top_n} {cat_col}",
                    labels={'x': cat_col, 'y': 'Count'},
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No categorical columns for bar chart")

def create_distributions_tab(df: pd.DataFrame, numeric_cols: list, categorical_cols: list):
    """Create distributions tab with histograms and box plots."""

    if not numeric_cols:
        st.warning("No numeric columns available for distribution analysis.")
        return

    col1, col2 = st.columns(2)

    with col1:
        # Histogram
        hist_col = st.selectbox("Histogram Column", numeric_cols, key="hist_col")
        nbins = st.slider("Number of bins", 10, 100, 30, key="nbins")

        fig = px.histogram(
            df, x=hist_col,
            nbins=nbins,
            title=f"Distribution of {hist_col}",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Box plot
        box_col = st.selectbox("Box Plot Column", numeric_cols, key="box_col")

        if categorical_cols:
            color_col = st.selectbox("Color by", ["None"] + categorical_cols, key="box_color")
            if color_col != "None":
                fig = px.box(
                    df, y=box_col, color=color_col,
                    title=f"{box_col} by {color_col}",
                    template="plotly_white"
                )
            else:
                fig = px.box(
                    df, y=box_col,
                    title=f"Box Plot of {box_col}",
                    template="plotly_white"
                )
        else:
            fig = px.box(
                df, y=box_col,
                title=f"Box Plot of {box_col}",
                template="plotly_white"
            )

        st.plotly_chart(fig, use_container_width=True)

    # Additional distribution plots
    if len(numeric_cols) >= 2:
        st.subheader("Multiple Distributions")

        selected_cols = st.multiselect(
            "Select columns to compare",
            numeric_cols,
            default=numeric_cols[:3] if len(numeric_cols) >= 3 else numeric_cols,
            key="multi_dist_cols"
        )

        if selected_cols:
            # Create subplots for multiple histograms
            fig = make_subplots(
                rows=len(selected_cols),
                cols=1,
                subplot_titles=[f"Distribution of {col}" for col in selected_cols]
            )

            for i, col in enumerate(selected_cols):
                fig.add_trace(
                    go.Histogram(x=df[col], name=col),
                    row=i+1, col=1
                )

            fig.update_layout(
                height=300 * len(selected_cols),
                title_text="Multiple Column Distributions",
                template="plotly_white"
            )

            st.plotly_chart(fig, use_container_width=True)

def create_correlations_tab(df: pd.DataFrame, numeric_cols: list):
    """Create correlations tab with heatmap and scatter plots."""

    if len(numeric_cols) < 2:
        st.warning("Need at least 2 numeric columns for correlation analysis.")
        return

    # Correlation matrix
    st.subheader("Correlation Matrix")

    corr_matrix = df[numeric_cols].corr()

    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        title="Correlation Matrix",
        template="plotly_white",
        color_continuous_scale="RdBu_r"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Scatter plot matrix for selected columns
    st.subheader("Scatter Plot Matrix")

    selected_cols = st.multiselect(
        "Select columns for scatter matrix",
        numeric_cols,
        default=numeric_cols[:4] if len(numeric_cols) >= 4 else numeric_cols,
        key="scatter_matrix_cols"
    )

    if len(selected_cols) >= 2:
        # Create pairwise scatter plots
        fig = px.scatter_matrix(
            df[selected_cols],
            title="Scatter Plot Matrix",
            template="plotly_white"
        )
        fig.update_layout(height=800)
        st.plotly_chart(fig, use_container_width=True)

    # Detailed correlation analysis
    st.subheader("Strongest Correlations")

    # Get upper triangle of correlation matrix
    corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_val = corr_matrix.iloc[i, j]
            corr_pairs.append((
                corr_matrix.columns[i],
                corr_matrix.columns[j],
                abs(corr_val),
                corr_val
            ))

    # Sort by absolute correlation strength
    corr_pairs.sort(key=lambda x: x[2], reverse=True)

    # Display top correlations
    for col1, col2, abs_corr, corr in corr_pairs[:10]:  # Top 10
        strength = "Strong" if abs_corr > 0.7 else "Moderate" if abs_corr > 0.3 else "Weak"
        direction = "positive" if corr > 0 else "negative"

        st.write(f"**{col1} ↔ {col2}**: {strength} {direction} correlation ({corr:.3f})")

        # Show scatter plot for top correlation
        if abs_corr == corr_pairs[0][2]:  # Only for the strongest
            fig = px.scatter(
                df, x=col1, y=col2,
                trendline="ols",
                title=f"{col1} vs {col2} (r = {corr:.3f})",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

def create_raw_data_tab(df: pd.DataFrame):
    """Create raw data tab with table and export options."""

    st.subheader("Raw Data Explorer")

    # Data info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", f"{len(df):,}")
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        memory_usage = df.memory_usage(deep=True).sum()
        st.metric("Memory Usage", f"{memory_usage / 1024 / 1024:.1f} MB")

    # Column selector
    all_columns = df.columns.tolist()
    selected_columns = st.multiselect(
        "Select columns to display",
        all_columns,
        default=all_columns[:10] if len(all_columns) > 10 else all_columns,
        key="raw_data_columns"
    )

    if selected_columns:
        display_df = df[selected_columns].copy()

        # Data type info
        if st.checkbox("Show data types", key="show_dtypes"):
            dtypes_df = pd.DataFrame({
                'Column': display_df.columns,
                'Data Type': display_df.dtypes.astype(str),
                'Non-Null Count': display_df.notna().sum(),
                'Null Count': display_df.isna().sum()
            })
            st.dataframe(dtypes_df, use_container_width=True)

        # Data preview
        st.subheader("Data Preview")
        n_rows = st.slider("Number of rows to display", 5, min(1000, len(display_df)), 50, key="preview_rows")
        st.dataframe(display_df.head(n_rows), use_container_width=True)

        # Export options
        st.subheader("Export Data")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download as CSV", key="download_csv"):
                csv_data = display_df.to_csv(index=False)
                st.download_button(
                    label="Click to Download CSV",
                    data=csv_data,
                    file_name="data_export.csv",
                    mime="text/csv",
                    key="csv_download_btn"
                )

        with col2:
            if st.button("📊 Download as Excel", key="download_excel"):
                # Note: Would need openpyxl for Excel export
                st.info("Excel export requires additional dependencies")
```

### 6. Main Application (`app.py`)

#### Complete App Integration
```python
import streamlit as st
import pandas as pd
from utils.databricks_connector import get_databricks_client, test_connection
from utils.data_loader import load_table_data, load_volume_file, get_available_datasets
from components.chatbot import chat_interface, get_quick_suggestions
from components.dashboard import create_dashboard

# Page configuration
st.set_page_config(
    page_title="Databricks Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point."""

    st.title("🔗 Databricks Data Explorer")
    st.markdown("Connect to your Databricks workspace, explore datasets with natural language, and visualize insights.")

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Test connection
        if st.button("🔗 Test Connection", key="test_conn"):
            with st.spinner("Testing connection..."):
                conn_status = test_connection()
                if conn_status['status'] == 'connected':
                    st.success("✅ Connected to Databricks!")
                    st.info(f"Clusters: {conn_status['clusters_count']}")
                else:
                    st.error(f"❌ Connection failed: {conn_status['error']}")

        st.divider()

        # Dataset selection
        st.header("📋 Dataset Selection")

        # Get available datasets
        if st.button("🔍 Discover Datasets", key="discover"):
            with st.spinner("Fetching available datasets..."):
                datasets = get_available_datasets()
                st.session_state.available_datasets = datasets

        # Dataset selection interface
        if 'available_datasets' in st.session_state:
            datasets = st.session_state.available_datasets

            if datasets:
                # Catalog selection
                catalogs = list(datasets.keys())
                selected_catalog = st.selectbox(
                    "Select Catalog",
                    catalogs,
                    key="catalog_select"
                )

                if selected_catalog and selected_catalog in datasets:
                    # Schema selection
                    schemas = list(datasets[selected_catalog].keys())
                    selected_schema = st.selectbox(
                        "Select Schema",
                        schemas,
                        key="schema_select"
                    )

                    if selected_schema and selected_schema in datasets[selected_catalog]:
                        # Table selection
                        tables = datasets[selected_catalog][selected_schema]
                        selected_table = st.selectbox(
                            "Select Table",
                            tables,
                            key="table_select"
                        )

                        # Load data button
                        if st.button("📥 Load Dataset", key="load_data"):
                            with st.spinner("Loading data from Databricks..."):
                                try:
                                    df = load_table_data(selected_catalog, selected_schema, selected_table)
                                    if not df.empty:
                                        st.session_state.current_df = df
                                        st.session_state.dataset_info = {
                                            'catalog': selected_catalog,
                                            'schema': selected_schema,
                                            'table': selected_table,
                                            'row_count': len(df),
                                            'column_count': len(df.columns)
                                        }
                                        st.success(f"✅ Loaded {len(df):,} rows, {len(df.columns)} columns")
                                        st.rerun()
                                    else:
                                        st.error("No data found in the selected table")
                                except Exception as e:
                                    st.error(f"Failed to load data: {str(e)}")
            else:
                st.info("No datasets found. Make sure you have access to Databricks tables.")

        # Manual table input
        st.divider()
        st.header("🔧 Manual Input")

        with st.expander("Enter table details manually"):
            catalog = st.text_input("Catalog", value="main", key="manual_catalog")
            schema = st.text_input("Schema", value="default", key="manual_schema")
            table = st.text_input("Table", key="manual_table")

            if st.button("Load Manual Table", key="load_manual"):
                if catalog and schema and table:
                    with st.spinner("Loading data..."):
                        try:
                            df = load_table_data(catalog, schema, table)
                            if not df.empty:
                                st.session_state.current_df = df
                                st.session_state.dataset_info = {
                                    'catalog': catalog,
                                    'schema': schema,
                                    'table': table,
                                    'row_count': len(df),
                                    'column_count': len(df.columns)
                                }
                                st.success(f"✅ Loaded {len(df):,} rows, {len(df.columns)} columns")
                                st.rerun()
                            else:
                                st.warning("Table exists but contains no data")
                        except Exception as e:
                            st.error(f"Failed to load table: {str(e)}")
                else:
                    st.warning("Please fill in all table details")

    # Main content area
    if 'current_df' in st.session_state:
        df = st.session_state.current_df
        dataset_info = st.session_state.get('dataset_info', {})

        # Dataset info header
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Dataset", f"{dataset_info.get('catalog', 'N/A')}.{dataset_info.get('schema', 'N/A')}.{dataset_info.get('table', 'N/A')}")
        with col2:
            st.metric("Rows", f"{dataset_info.get('row_count', 0):,}")
        with col3:
            st.metric("Columns", dataset_info.get('column_count', 0))
        with col4:
            memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
            st.metric("Memory", f"{memory_mb:.1f} MB")

        # Quick suggestions
        with st.expander("💡 Quick Query Suggestions", expanded=False):
            suggestions = get_quick_suggestions(df)
            cols = st.columns(len(suggestions))
            for i, suggestion in enumerate(suggestions):
                if cols[i].button(suggestion, key=f"suggestion_{i}"):
                    # Add to chat input (this would need to be implemented)
                    st.info(f"Try asking: '{suggestion}'")

        # Tabs for different views
        tab1, tab2 = st.tabs(["🤖 Chat & Query", "📊 Dashboard"])

        with tab1:
            chat_interface(df)

        with tab2:
            create_dashboard(df)

    else:
        # Welcome screen
        st.info("👋 Welcome to Databricks Data Explorer!")
        st.markdown("""
        To get started:

        1. **Test your connection** using the sidebar
        2. **Discover available datasets** or enter table details manually
        3. **Load your data** and start exploring!

        ### Features:
        - 🤖 **Natural Language Queries**: Ask questions about your data in plain English
        - 📊 **Interactive Visualizations**: Explore patterns with Plotly charts
        - 🔍 **Advanced Filtering**: Drill down into specific data segments
        - 📥 **Export Capabilities**: Download filtered results
        - ⚡ **Performance Optimized**: Caching for fast data loading
        """)

        # Sample data option
        st.divider()
        if st.button("🎯 Try with Sample Data", key="sample_data"):
            # Create sample dataset
            np.random.seed(42)
            sample_df = pd.DataFrame({
                'customer_id': range(1, 101),
                'age': np.random.normal(35, 10, 100).astype(int),
                'income': np.random.normal(50000, 15000, 100).astype(int),
                'category': np.random.choice(['A', 'B', 'C'], 100),
                'purchase_amount': np.random.exponential(100, 100),
                'satisfaction': np.random.randint(1, 6, 100)
            })

            st.session_state.current_df = sample_df
            st.session_state.dataset_info = {
                'catalog': 'sample',
                'schema': 'demo',
                'table': 'customers',
                'row_count': len(sample_df),
                'column_count': len(sample_df.columns)
            }
            st.success("✅ Sample data loaded! Explore the tabs above.")
            st.rerun()

if __name__ == "__main__":
    main()
```

### 7. Requirements and Configuration

#### requirements.txt
```txt
streamlit>=1.28.0
databricks-sdk>=0.12.0
pandas>=2.0.0
plotly>=5.15.0
numpy>=1.24.0
openai>=1.0.0
python-dotenv>=1.0.0
```

#### .streamlit/secrets.toml.example
```toml
# Databricks connection
[databricks]
host = "https://your-workspace.azuredatabricks.net"
token = "dapi-your-token-here"

# Optional: OpenAI for enhanced NLP (if using AI-powered query processing)
[openai]
api_key = "sk-your-openai-key-here"
```

#### .streamlit/config.toml
```toml
[theme]
primaryColor = "#FF6B35"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F8F9FA"
textColor = "#262730"

[server]
maxUploadSize = 100
enableCORS = false
enableXsrfProtection = true
```

---

## Deployment Options

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABRICKS_HOST="https://your-workspace.azuredatabricks.net"
export DATABRICKS_TOKEN="dapi-your-token"

# Run the app
streamlit run app.py
```

### Streamlit Community Cloud
1. Push code to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Add Databricks secrets in dashboard
4. Deploy

### Databricks Environment
- Deploy directly in Databricks workspace
- Use Databricks secrets for authentication
- No need for external secrets management

---

## Best Practices

### Security
- Never commit secrets to version control
- Use Databricks secrets for sensitive credentials
- Implement proper access controls in Databricks
- Rotate tokens regularly

### Performance
- Use `@st.cache_data` for expensive operations
- Implement pagination for large datasets
- Optimize queries to fetch only needed data
- Use appropriate data types

### User Experience
- Provide clear loading states
- Include helpful error messages
- Add tooltips and documentation
- Implement responsive design

### Data Handling
- Validate data before visualization
- Handle missing values appropriately
- Implement data type detection
- Provide data export options

---

## Troubleshooting

### Common Issues

**Connection Problems:**
- Verify Databricks credentials
- Check network connectivity
- Ensure proper permissions in Databricks

**Data Loading Issues:**
- Confirm table exists and is accessible
- Check data types and formats
- Verify Unity Catalog permissions

**Performance Issues:**
- Implement caching for repeated operations
- Use sampling for large datasets
- Optimize query patterns

**Visualization Problems:**
- Check data types for chart compatibility
- Handle missing values
- Implement error boundaries

---

Built with Streamlit, Databricks SDK, and Plotly. Last updated: May 2026