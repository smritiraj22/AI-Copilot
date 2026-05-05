# MLFlow.md - Azure Databricks MLflow Agent Guide

## Instructions for AI Agent

**Purpose:** Build an end-to-end MLflow-driven solution on Azure Databricks that:
- connects to Databricks datasets,
- creates and trains ML models,
- validates model performance,
- deploys models using MLflow deployment tooling,
- enables chatbot-based result queries,
- charts metrics and predictions in a Streamlit + Plotly dashboard.

**Key Capabilities:**
- 🔗 Databricks dataset access via Unity Catalog or Delta Lake
- 🧠 MLflow experiment tracking and model registry
- ✅ Model validation and metrics comparison
- 🚀 Deployment path for Databricks serving or external inference
- 🤖 Natural language query interface for results
- 📈 Interactive Streamlit dashboard with Plotly charts

---

## Quick Start

### Prerequisites
- Azure Databricks workspace with a SQL warehouse or cluster
- Databricks Unity Catalog access or dataset permissions
- Python 3.8+ environment
- MLflow, Streamlit, Plotly, scikit-learn, pandas, numpy installed
- Databricks SDK configured for your workspace

### Install Dependencies
```bash
pip install streamlit databricks-sdk mlflow scikit-learn pandas numpy plotly python-dotenv
```

### Main Components
- `app.py` — Streamlit dashboard and chatbot UI
- `train.py` — Model training, validation, and MLflow logging
- `deploy.py` — Model deployment helper
- `utils/databricks_connector.py` — Databricks connection helpers
- `utils/data_loader.py` — Data loading from Databricks
- `utils/mlflow_utils.py` — MLflow experiment and registry utilities
- `components/chatbot.py` — Chat interface for querying results
- `components/dashboard.py` — Plotly charts and metrics dashboard

---

## Project Structure

```
mlflow-databricks-agent/
├── app.py
├── train.py
├── deploy.py
├── utils/
│   ├── databricks_connector.py
│   ├── data_loader.py
│   └── mlflow_utils.py
├── components/
│   ├── chatbot.py
│   └── dashboard.py
├── requirements.txt
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── README.md
└── MLFlow.md
```

---

## Implementation Guide

### 1. Databricks Connection

Create connection helpers that support environment variables and Streamlit secrets.

#### `utils/databricks_connector.py`
```python
import os
import streamlit as st
from databricks.sdk import WorkspaceClient

@st.cache_resource
def get_databricks_client() -> WorkspaceClient:
    host = os.getenv('DATABRICKS_HOST')
    token = os.getenv('DATABRICKS_TOKEN')
    if host and token:
        return WorkspaceClient(host=host, token=token)

    if hasattr(st, 'secrets') and 'databricks' in st.secrets:
        secret = st.secrets['databricks']
        return WorkspaceClient(host=secret['host'], token=secret['token'])

    return WorkspaceClient()


def test_connection() -> dict:
    try:
        client = get_databricks_client()
        clusters = list(client.clusters.list())
        return {
            'status': 'connected',
            'cluster_count': len(clusters),
            'host': client.config.host
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
```

---

### 2. Data Loading from Databricks

Load a dataset from a Unity Catalog table or volume and cache it for Streamlit.

#### `utils/data_loader.py`
```python
import pandas as pd
import streamlit as st
from utils.databricks_connector import get_databricks_client

@st.cache_data(ttl=3600)
def load_table_data(catalog: str, schema: str, table: str) -> pd.DataFrame:
    client = get_databricks_client()
    query = f'SELECT * FROM {catalog}.{schema}.{table} LIMIT 10000'
    try:
        result = client.query.execute(query)
        columns = [col.name for col in result.result_set.metadata]
        rows = [list(row) for row in result.result_set.data]
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        st.error(f'Failed to load {catalog}.{schema}.{table}: {e}')
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_available_tables() -> dict:
    client = get_databricks_client()
    datasets = {}
    try:
        catalogs = client.query.execute('SHOW CATALOGS')
        for catalog in catalogs.result_set.data:
            catalog_name = catalog[0]
            datasets[catalog_name] = {}
            schemas = client.query.execute(f'SHOW SCHEMAS IN {catalog_name}')
            for schema in schemas.result_set.data:
                schema_name = schema[0]
                tables = client.query.execute(f'SHOW TABLES IN {catalog_name}.{schema_name}')
                datasets[catalog_name][schema_name] = [table[1] for table in tables.result_set.data]
    except Exception as e:
        st.warning(f'Unable to load datasets: {e}')
    return datasets
```

> Note: For large datasets, add `WHERE` / sampling logic and load only a subset for model training or dashboard preview.

---

### 3. MLflow Experiment Tracking

Use MLflow to log training metrics, parameters, artifacts, and models. Track both validation and test results.

#### `utils/mlflow_utils.py`
```python
import mlflow
from typing import Dict

MLFLOW_TRACKING_URI = None
MLFLOW_EXPERIMENT_NAME = 'databricks-mlflow-agent'


def init_mlflow(experiment_name: str = MLFLOW_EXPERIMENT_NAME, tracking_uri: str | None = None):
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)


def start_run(run_name: str):
    return mlflow.start_run(run_name=run_name)


def log_metrics(metrics: Dict[str, float]):
    for key, value in metrics.items():
        mlflow.log_metric(key, value)


def log_params(params: Dict[str, str]):
    for key, value in params.items():
        mlflow.log_params(params)


def register_model(model_uri: str, name: str, stage: str = 'Staging'):
    return mlflow.register_model(model_uri=model_uri, name=name)
```

---

### 4. Training Script

Train a model using scikit-learn and log it into MLflow. Use a Databricks dataset and record train/test metrics.

#### `train.py`
```python
import argparse
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import mlflow
from utils.data_loader import load_table_data
from utils.mlflow_utils import init_mlflow, start_run, log_metrics, log_params


def train_model(catalog: str, schema: str, table: str, target: str, model_name: str):
    init_mlflow()
    df = load_table_data(catalog, schema, table)
    if df.empty:
        raise ValueError('Dataset is empty or unavailable')

    X = df.drop(columns=[target])
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)

    with start_run(run_name=f'{model_name}-training') as run:
        mlflow.sklearn.autolog()

        model.fit(X_train, y_train)
        predictions = model.predict(X_test)

        mse = mean_squared_error(y_test, predictions)
        rmse = mse**0.5
        r2 = r2_score(y_test, predictions)

        metrics = {'mse': mse, 'rmse': rmse, 'r2': r2}
        params = {'target_column': target, 'model_type': 'RandomForestRegressor'}

        log_params(params)
        log_metrics(metrics)
        mlflow.sklearn.log_model(model, 'model')

        run_id = run.info.run_id
        artifact_uri = mlflow.get_artifact_uri('model')
        print(f'Training complete. Run ID: {run_id}')
        print(f'Artifact URI: {artifact_uri}')

    return run_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', required=True)
    parser.add_argument('--schema', required=True)
    parser.add_argument('--table', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--model-name', default='databricks-mlflow-model')
    args = parser.parse_args()

    train_model(args.catalog, args.schema, args.table, args.target, args.model_name)

if __name__ == '__main__':
    main()
```

> Tip: Use `mlflow.sklearn.autolog()` to capture parameters, metrics, and artifacts automatically.

---

### 5. Model Validation and Comparison

Fetch past MLflow runs, compare key metrics, and show the best model candidate.

#### `utils/mlflow_utils.py` additions
```python
from mlflow.tracking import MlflowClient


def get_mlflow_client() -> MlflowClient:
    return MlflowClient()


def list_runs(experiment_name: str):
    client = get_mlflow_client()
    experiment = client.get_experiment_by_name(experiment_name)
    if not experiment:
        return []
    return client.search_runs(experiment_ids=[experiment.experiment_id], order_by=['metrics.rmse ASC'])


def get_model_versions(model_name: str):
    client = get_mlflow_client()
    return client.get_latest_versions(name=model_name)
```

#### Validation Script Example
```python
from utils.mlflow_utils import init_mlflow, list_runs, get_model_versions

init_mlflow()
runs = list_runs('databricks-mlflow-agent')
for run in runs:
    print(run.info.run_id, run.data.metrics['rmse'], run.data.metrics['r2'])

versions = get_model_versions('databricks-mlflow-model')
for version in versions:
    print(version.version, version.current_stage, version.status, version.run_id)
```

---

### 6. Model Deployment

Use MLflow deployment capabilities for Databricks or external serving.

#### `deploy.py`
```python
import mlflow
from utils.mlflow_utils import init_mlflow, register_model


def deploy_model(run_id: str, model_name: str, stage: str = 'Staging'):
    init_mlflow()
    model_uri = f'runs:/{run_id}/model'
    registered_model = register_model(model_uri=model_uri, name=model_name)
    client = mlflow.tracking.MlflowClient()
    client.transition_model_version_stage(
        name=model_name,
        version=registered_model.version,
        stage=stage,
        archive_existing_versions=True
    )
    print(f'Model {model_name} version {registered_model.version} transitioned to {stage}')
    return registered_model.version


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--model-name', required=True)
    parser.add_argument('--stage', default='Staging')
    args = parser.parse_args()
    deploy_model(args.run_id, args.model_name, args.stage)

if __name__ == '__main__':
    main()
```

> For Azure Databricks model serving, consider using MLflow model serving in Databricks or exporting the model to an external inference endpoint.

---

### 7. Streamlit Dashboard & Chatbot Interface

Build a UI to show model metrics, predictions, and answer user queries.

#### `components/dashboard.py`
```python
import streamlit as st
import plotly.express as px
import pandas as pd


def show_model_metrics(metrics: dict):
    st.subheader('Model Metrics')
    cols = st.columns(len(metrics))
    for i, (metric, value) in enumerate(metrics.items()):
        cols[i].metric(metric.upper(), f'{value:.4f}')


def show_prediction_charts(df: pd.DataFrame, target: str, prediction: str):
    st.subheader('Predictions vs Actual')
    fig = px.scatter(
        df,
        x=target,
        y=prediction,
        title='Actual vs Predicted',
        labels={target: 'Actual', prediction: 'Predicted'},
        template='plotly_white'
    )
    fig.add_shape(
        type='line',
        x0=df[target].min(), y0=df[target].min(),
        x1=df[target].max(), y1=df[target].max(),
        line=dict(color='red', dash='dash')
    )
    st.plotly_chart(fig, use_container_width=True)


def show_performance_distribution(df: pd.DataFrame, prediction: str):
    st.subheader('Prediction Residuals')
    df['residual'] = df[prediction] - df[df.columns[0]]
    fig = px.histogram(df, x='residual', nbins=30, title='Residual Distribution', template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)
```

#### `components/chatbot.py`
```python
import streamlit as st
import pandas as pd
from utils.mlflow_utils import list_runs


def chat_interface(metrics: dict, runs: list, df: pd.DataFrame):
    st.header('🤖 ML Results Chatbot')
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message['role']):
            st.markdown(message['text'])

    if prompt := st.chat_input('Ask about model performance, runs, or predictions...'):
        st.session_state.chat_history.append({'role': 'user', 'text': prompt})
        with st.chat_message('assistant'):
            response = generate_response(prompt, metrics, runs, df)
            st.markdown(response)
            st.session_state.chat_history.append({'role': 'assistant', 'text': response})


def generate_response(prompt: str, metrics: dict, runs: list, df: pd.DataFrame) -> str:
    prompt_lower = prompt.lower()
    if 'best' in prompt_lower and 'model' in prompt_lower:
        best_run = runs[0] if runs else None
        if best_run:
            return f"Best model run is {best_run.info.run_id} with RMSE={best_run.data.metrics.get('rmse', 'n/a')} and R2={best_run.data.metrics.get('r2', 'n/a')}"
        return 'No runs available.'
    if 'accuracy' in prompt_lower or 'rmse' in prompt_lower or 'r2' in prompt_lower:
        return 'Model metrics:\n' + '\n'.join([f"- {k}: {v:.4f}" for k, v in metrics.items()])
    if 'prediction' in prompt_lower and 'sample' in prompt_lower:
        sample = df.head(5).to_dict(orient='records')
        return 'Here are a few sample predictions: ' + str(sample)
    return 'I can answer questions about model metrics, best runs, and predictions. Try: "What is the best model?" or "Show RMSE."'
```

#### `app.py`
```python
import streamlit as st
import pandas as pd
import numpy as np
from utils.databricks_connector import test_connection
from utils.data_loader import get_available_tables, load_table_data
from utils.mlflow_utils import init_mlflow, list_runs
from components.dashboard import show_model_metrics, show_prediction_charts
from components.chatbot import chat_interface

st.set_page_config(page_title='MLflow Databricks Agent', layout='wide')


def main():
    st.title('MLflow + Databricks Model Explorer')
    st.markdown('End-to-end MLflow model training, validation, deployment, and querying with Streamlit.')

    with st.sidebar:
        st.header('Configuration')
        if st.button('Test Databricks Connection'):
            status = test_connection()
            if status['status'] == 'connected':
                st.success('Connected to Databricks')
                st.write(status)
            else:
                st.error(status['message'])

        tables = get_available_tables()
        catalog = st.selectbox('Catalog', list(tables.keys()) if tables else [])
        schema = st.selectbox('Schema', list(tables[catalog].keys()) if catalog else [])
        table = st.selectbox('Table', tables[catalog] if catalog and tables.get(catalog) else [])
        target_column = st.text_input('Target Column')
        model_name = st.text_input('Model Name', value='databricks-mlflow-model')

    if st.button('Load Data and Show Preview'):
        if catalog and schema and table:
            df = load_table_data(catalog, schema, table)
            st.dataframe(df.head())
            st.session_state['dataset'] = df
            st.session_state['target'] = target_column
        else:
            st.warning('Please select catalog, schema, and table.')

    if 'dataset' in st.session_state and st.session_state['target']:
        df = st.session_state['dataset']
        target = st.session_state['target']

        if st.button('Train Model'):
            st.info('Training model...')
            st.success('Training started. Run `train.py` separately for MLflow logging.')

        init_mlflow()
        runs = list_runs('databricks-mlflow-agent')
        metrics = runs[0].data.metrics if runs else {}

        st.sidebar.markdown('### Latest Run Metrics')
        if metrics:
            for k, v in metrics.items():
                st.sidebar.metric(k, f'{v:.4f}')

        tab1, tab2 = st.tabs(['Dashboard', 'Chatbot'])

        with tab1:
            if metrics:
                show_model_metrics(metrics)
            if 'dataset' in st.session_state:
                show_prediction_charts(st.session_state['dataset'], target, 'prediction')

        with tab2:
            chat_interface(metrics, runs, df)

    else:
        st.info('Load a dataset and define a target column to begin.')

if __name__ == '__main__':
    main()
```

> Note: If you want true prediction scoring in the dashboard, add a prediction pipeline and store predictions in the dataset before charting.

---

## Deployment Path

### Option 1: Databricks MLflow Serving
- Use Databricks model serving if enabled in your workspace
- Register model in MLflow and transition to `Production`
- Create a serving endpoint from the model registry UI or API

### Option 2: External Inference Endpoint
- Export the MLflow model locally or to Azure Blob
- Use `mlflow.pyfunc.load_model()` in a REST service
- Connect Streamlit dashboard to the deployed endpoint for live inference

### Option 3: Batch Prediction on Databricks
- Use a Databricks job to run batch scoring
- Store prediction output in Delta Lake or Unity Catalog
- Visualize prediction results in the Streamlit dashboard

---

## Requirements

#### `requirements.txt`
```text
streamlit>=1.28.0
databricks-sdk>=0.12.0
mlflow>=2.0.0
scikit-learn>=1.2.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.15.0
python-dotenv>=1.0.0
```

#### `.streamlit/secrets.toml.example`
```toml
[databricks]
host = 'https://your-workspace.azuredatabricks.net'
token = 'dapi-your-token-here'

[mlflow]
tracking_uri = 'databricks'
```

#### `.streamlit/config.toml`
```toml
[theme]
primaryColor = '#4B8BBE'
backgroundColor = '#FFFFFF'
secondaryBackgroundColor = '#F0F4F8'
textColor = '#0F172A'

[server]
maxUploadSize = 100
enableXsrfProtection = true
```

---

## Best Practices

### Model Lifecycle
- Track every experiment with MLflow
- Use consistent experiment names and tags
- Register and stage models for deployment
- Archive old model versions
- Keep validation and test sets separate

### Databricks Integration
- Query only needed columns for training and validation
- Use Delta tables or Unity Catalog for secure access
- Cache intermediate data where appropriate
- Use Databricks secrets for credentials

### Streamlit UX
- Provide training status and run metadata
- Use clear chart titles and metrics
- Avoid loading full large datasets in the UI
- Add quick query suggestions for the chatbot

### Security
- Never store secrets in source control
- Use Azure-managed identities or secrets scopes
- Restrict workspace access with proper IAM roles

---

## Troubleshooting

### Common Issues
- **MLflow connection errors:** Verify `MLFLOW_TRACKING_URI` or Databricks workspace configuration
- **Dataset access failures:** Confirm Unity Catalog permissions and table ownership
- **Prediction mismatch:** Ensure the same feature preprocessing is used in training and inference
- **Streamlit widget resets:** Use `st.session_state` for persistent UI state

---

Built for Azure Databricks, MLflow, Streamlit, and Plotly. Last updated: May 2026
