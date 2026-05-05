# Azure Databricks: Complete Guide to Connect, Run Code, and Deploy

> **TL;DR:** This guide covers connecting to Azure Databricks, running code via notebooks and jobs, and deploying applications using Databricks Asset Bundles and CI/CD pipelines.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Authentication Methods](#authentication-methods)
- [CLI Usage](#cli-usage)
- [Python SDK & API Calls](#python-sdk--api-calls)
- [Running Code](#running-code)
- [Deployment](#deployment)
- [Best Practices](#best-practices)
- [Quick Reference](#quick-reference-common-workflows)

---

## Prerequisites

### System Requirements
- Python 3.8 or higher (3.10+ recommended for consistency with Databricks Runtime 13.3+)
- Virtual environment (venv or Poetry recommended)
- Azure subscription with Databricks workspace provisioned
- Network connectivity to Databricks workspace URL (HTTPS)
- For CI/CD: Git repository (GitHub, GitLab, Bitbucket, or Azure DevOps)

### Essential Installations
```bash
# Install Databricks CLI (v0.218.0 or above for bundles)
pip install databricks-cli

# Install Databricks SDK for Python
pip install databricks-sdk

# Install build tools for asset bundles
# CLI includes all necessary bundle functionality
databricks --version
```

### Workspace Configuration
- Workspace files enabled (default in Databricks Runtime 11.3 LTS+)
- User has appropriate permissions (CAN_USE for workspace/account features)
- For bundles: Workspace-level or account-level API access

---

## Authentication Methods

### A. Databricks Native Authentication (Recommended)

#### 1. Personal Access Token (PAT)
```bash
# Configure CLI
databricks configure --token
# Enter: workspace URL and personal access token

# Configuration file: ~/.databrickscfg
[DEFAULT]
host = https://<workspace-url>.azuredatabricks.net
token = dapi<token-string>
```

```python
# Python SDK
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(
    host='https://<workspace-url>.azuredatabricks.net',
    token='<pat>'
)
```

#### 2. OAuth Machine-to-Machine (M2M) - Recommended for Service Principals
```bash
# Via environment variables
export DATABRICKS_HOST=https://<workspace-url>.azuredatabricks.net
export DATABRICKS_CLIENT_ID=<client-id>
export DATABRICKS_CLIENT_SECRET=<client-secret>

# Via .databrickscfg
[DEFAULT]
host = https://<workspace-url>.azuredatabricks.net
client_id = <client-id>
client_secret = <client-secret>
```

#### 3. OAuth User-to-Machine (U2M) - Interactive
```bash
# Environment variables (browser-based auth)
export DATABRICKS_HOST=https://<workspace-url>.azuredatabricks.net

databricks workspace list  # Opens browser for authentication
```

### B. Azure Native Authentication

#### 1. Azure Managed Identity (for Azure resources like VMs)
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(
    host='https://<workspace-url>.azuredatabricks.net',
    azure_workspace_resource_id='/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Databricks/workspaces/<ws-name>',
    azure_use_msi=True
)
```

#### 2. Azure Service Principal (Entra ID)
```bash
# .databrickscfg
[DEFAULT]
host = https://<workspace-url>.azuredatabricks.net
azure_workspace_resource_id = /subscriptions/.../providers/Microsoft.Databricks/workspaces/<name>
azure_tenant_id = <tenant-id>
azure_client_id = <client-id>
azure_client_secret = <client-secret>
```

#### 3. Azure CLI Authentication
```bash
# Requires: az login
az login

# SDK automatically uses Azure CLI credentials
# .databrickscfg
[DEFAULT]
host = https://<workspace-url>.azuredatabricks.net
auth_type = azure-cli
```

### C. Configuration Profiles
```bash
# Create multiple profiles
databricks configure --profile production --token
databricks configure --profile development --token

# Use profile in commands
databricks workspace ls --profile production

# In Python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient(profile='production')
```

### D. Environment Variables (Unified Authentication)
```bash
export DATABRICKS_HOST=https://<workspace-url>.azuredatabricks.net
export DATABRICKS_ACCOUNT_ID=<account-id>           # For account APIs
export DATABRICKS_TOKEN=<pat>                        # Or OAuth below
export DATABRICKS_CLIENT_ID=<client-id>             # OAuth M2M
export DATABRICKS_CLIENT_SECRET=<client-secret>     # OAuth M2M
export DATABRICKS_CONFIG_PROFILE=<profile-name>
```

---

## CLI Usage

### Installation & Configuration
```bash
# Install latest CLI
pip install --upgrade databricks-cli

# Verify installation
databricks --version

# Configure default profile (interactive)
databricks configure --token
# Follow prompts for workspace URL and token

# Configure with service principal
databricks configure --profile sp --token
```

### Common CLI Commands

#### Workspace Management
```bash
# List workspace contents
databricks workspace ls /

# Create directory
databricks workspace mkdirs /Users/myproject

# Upload notebook
databricks workspace import /path/to/notebook.py /Users/myproject/notebook --language PYTHON

# Export notebook
databricks workspace export /Users/myproject/notebook ~/exported_notebook.py
```

#### Cluster Management
```bash
# List clusters
databricks clusters list

# Get cluster details
databricks clusters get --cluster-id <cluster-id>

# Start cluster
databricks clusters start --cluster-id <cluster-id>

# Terminate cluster
databricks clusters terminate --cluster-id <cluster-id>
```

#### Jobs Management
```bash
# List jobs
databricks jobs list

# Get job details
databricks jobs get --job-id <job-id>

# Create job (with JSON config)
databricks jobs create --json-file job-config.json

# Run job now
databricks jobs run-now --job-id <job-id>

# List job runs
databricks jobs runs list --job-id <job-id>
```

#### Secrets Management
```bash
# Create secret scope
databricks secrets create-scope --scope my-scope

# Store secret
databricks secrets put --scope my-scope --key api-key --string-value <secret-value>

# List secrets in scope
databricks secrets list --scope my-scope
```

#### Bundle Commands (Declarative Automation Bundles)
```bash
# Initialize new bundle from template
databricks bundle init

# Validate bundle configuration
databricks bundle validate

# Deploy bundle to workspace
databricks bundle deploy

# Run bundle workflow
databricks bundle run job_name

# Delete deployed bundle
databricks bundle destroy
```

---

## Python SDK & API Calls

### A. Installation & Basic Setup
```bash
pip install databricks-sdk==0.106.0  # Pin version during beta

# Or in notebook
%pip install databricks-sdk --upgrade
```

### B. Client Initialization

#### Default Authentication (Recommended)
```python
from databricks.sdk import WorkspaceClient, AccountClient

# Workspace-level operations
w = WorkspaceClient()

# Account-level operations (admin only)
a = AccountClient()
```

#### Explicit Authentication
```python
# With PAT
w = WorkspaceClient(
    host='https://<workspace-url>.azuredatabricks.net',
    token='<pat>'
)

# With OAuth M2M
w = WorkspaceClient(
    host='https://<workspace-url>.azuredatabricks.net',
    client_id='<client-id>',
    client_secret='<client-secret>'
)

# With Azure Service Principal
w = WorkspaceClient(
    host='https://<workspace-url>.azuredatabricks.net',
    azure_workspace_resource_id='/subscriptions/.../workspaces/<name>',
    azure_tenant_id='<tenant-id>',
    azure_client_id='<client-id>',
    azure_client_secret='<client-secret>'
)
```

### C. Workspace API Examples

#### Cluster Operations
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import ClusterDetails

w = WorkspaceClient()

# List clusters
for cluster in w.clusters.list():
    print(f"{cluster.cluster_name}: {cluster.state}")

# Create cluster
cluster = w.clusters.create_and_wait(
    cluster_name='my-cluster',
    spark_version='12.2.x-scala2.12',
    node_type_id='Standard_DS3_v2',
    autotermination_minutes=15,
    num_workers=2
)
print(f"Cluster created: {cluster.cluster_id}")

# Get cluster info
cluster = w.clusters.get(cluster_id='<cluster-id>')

# Permanently delete cluster
w.clusters.permanent_delete(cluster_id='<cluster-id>')
```

#### Notebook Operations
```python
# List workspace objects
for obj in w.workspace.list('/Users'):
    print(f"{obj.path} - {obj.object_type}")

# Create notebook
w.workspace.upload(
    path='/Users/my_notebook',
    format='SOURCE',
    language='PYTHON',
    content=b'# Python notebook content'
)

# Export notebook
response = w.workspace.get_status(path='/Users/my_notebook')
exported = w.workspace.download(path='/Users/my_notebook')
with open('exported.py', 'wb') as f:
    f.write(exported.contents.read())

# Delete notebook
w.workspace.delete(path='/Users/my_notebook')
```

#### Job Management
```python
from databricks.sdk.service.jobs import Task, NotebookTask, Source

# Create job
job = w.jobs.create(
    name='my-job',
    tasks=[
        Task(
            task_key='extract',
            notebook_task=NotebookTask(
                notebook_path='/Users/my_notebook',
                base_parameters={'param1': 'value1'}
            ),
            existing_cluster_id='<cluster-id>'
        )
    ]
)
print(f"Job created: {job.job_id}")

# Run job immediately
run = w.jobs.submit(
    run_name='manual-run-1',
    tasks=[{
        'task_key': 'task1',
        'notebook_task': {'notebook_path': '/Users/notebook'},
        'new_cluster': {...}
    }]
)

# Wait for job completion
run_result = w.jobs.wait_get_run_job_terminated_or_skipped(run.run_id)
print(f"Job state: {run_result.state.result_state}")

# List job runs
for run in w.jobs.list_runs(job_id=job.job_id):
    print(f"Run {run.run_id}: {run.state.life_cycle_state}")
```

#### File Management (Unity Catalog Volumes)
```python
import io

w = WorkspaceClient()

volume_path = '/Volumes/main/default/my-volume'

# Create directory
w.files.create_directory(f'{volume_path}/data')

# Upload file from local path
w.files.upload_from(
    f'{volume_path}/data/file.csv',
    'local_file.csv',
    overwrite=True
)

# Upload from in-memory
w.files.upload(
    f'{volume_path}/data/output.txt',
    io.BytesIO(b'file contents'),
    overwrite=True
)

# List files
for item in w.files.list_directory_contents(volume_path):
    print(item.path)

# Download file
w.files.download_to(
    f'{volume_path}/data/file.csv',
    'downloaded_file.csv'
)

# Delete file
w.files.delete(f'{volume_path}/data/file.csv')
```

#### Secrets Management
```python
# Create secret scope
w.secrets.create_scope(scope='my-scope')

# Store secret
w.secrets.put_secret(
    scope='my-scope',
    key='api-key',
    string_value='secret-value'
)

# Retrieve secret
secret = w.secrets.get_secret(scope='my-scope', key='api-key')
print(secret.value)  # In notebooks: dbutils.secrets.get()

# List secrets
for secret_metadata in w.secrets.list_secrets(scope='my-scope'):
    print(secret_metadata.key)
```

### D. Direct REST API Calls

#### Using Databricks SDK
```python
# The SDK abstracts REST calls, but you can also use requests
import requests

workspace_url = 'https://<workspace-url>.azuredatabricks.net'
token = '<pat>'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# API: Get workspace info
response = requests.get(
    f'{workspace_url}/api/2.0/workspace/get-status?path=/',
    headers=headers
)
print(response.json())

# API: Create cluster
cluster_config = {
    'cluster_name': 'api-cluster',
    'spark_version': '12.2.x-scala2.12',
    'node_type_id': 'Standard_DS3_v2',
    'num_workers': 2
}
response = requests.post(
    f'{workspace_url}/api/2.0/clusters/create',
    headers=headers,
    json=cluster_config
)
print(response.json())
```

---

## Running Code

### A. Running Notebooks

#### From CLI
```bash
# Run notebook on existing cluster
databricks jobs create --json-file job.json  # Create job first

# Where job.json contains:
{
  "name": "notebook-job",
  "tasks": [{
    "task_key": "run_notebook",
    "notebook_task": {
      "notebook_path": "/Users/my_notebook",
      "base_parameters": {"param1": "value"}
    },
    "existing_cluster_id": "cluster-id"
  }]
}

databricks jobs run-now --job-id <job-id>
```

#### From Python SDK
```python
from databricks.sdk.service.jobs import Task, NotebookTask

# Execute notebook immediately
waiter = w.jobs.submit(
    run_name='notebook-run-1',
    tasks=[
        Task(
            task_key='notebook',
            notebook_task=NotebookTask(
                notebook_path='/Users/my_notebook',
                base_parameters={'env': 'prod', 'date': '2024-05-04'}
            ),
            new_cluster={
                'spark_version': '12.2.x-scala2.12',
                'node_type_id': 'Standard_DS3_v2',
                'num_workers': 2
            }
        )
    ]
)

# Wait for completion
import datetime
result = waiter.result(timeout=datetime.timedelta(minutes=30))
print(f"Job state: {result.state.result_state}")
```

### B. Running Jobs

#### Create One-Time Run
```python
from databricks.sdk.service.jobs import RunSubmitTaskSettings, SparkPythonTask

# Submit one-time job
run = w.jobs.submit(
    run_name='python-script-run',
    tasks=[
        RunSubmitTaskSettings(
            task_key='python_task',
            spark_python_task=SparkPythonTask(
                python_file='dbfs:/scripts/my_script.py',
                parameters=['arg1', 'arg2']
            ),
            new_cluster={
                'spark_version': '12.2.x-scala2.12',
                'node_type_id': 'Standard_DS3_v2',
                'num_workers': 1
            }
        )
    ]
)

print(f"Run ID: {run.run_id}")
```

#### Create Scheduled Job
```python
from databricks.sdk.service.jobs import Task, CronSchedule

job = w.jobs.create(
    name='daily-etl',
    tasks=[
        Task(
            task_key='etl',
            notebook_task=NotebookTask(
                notebook_path='/Workspace/etl_notebook'
            ),
            existing_cluster_id='<cluster-id>'
        )
    ],
    schedule=CronSchedule(
        quartz_cron_expression='0 0 8 ? * MON-FRI',
        timezone_id='America/New_York'
    )
)
```

#### Multi-Task Workflow
```python
from databricks.sdk.service.jobs import Task, NotebookTask

job = w.jobs.create(
    name='multi-step-pipeline',
    tasks=[
        Task(
            task_key='extract',
            notebook_task=NotebookTask(notebook_path='/extract'),
            existing_cluster_id='<cluster-id>'
        ),
        Task(
            task_key='transform',
            notebook_task=NotebookTask(notebook_path='/transform'),
            depends_on=[{'task_key': 'extract'}],
            existing_cluster_id='<cluster-id>'
        ),
        Task(
            task_key='load',
            notebook_task=NotebookTask(notebook_path='/load'),
            depends_on=[{'task_key': 'transform'}],
            existing_cluster_id='<cluster-id>'
        )
    ]
)
```

### C. Running SQL Queries
```python
# Via Databricks SQL warehouse
response = w.query.create(
    query='SELECT COUNT(*) as count FROM my_table',
    warehouse_id='<warehouse-id>'
).result()

print(response.query_result)
```

---

## Deployment

### A. Declarative Automation Bundles (DAB)

#### Initialize Bundle
```bash
# Create new bundle
databricks bundle init

# Follow prompts:
# - Choose template (default_python, default_sql, dbt_sql, etc.)
# - Enter project name
# - Configure variables
```

#### Bundle Structure
```
my-bundle/
├── databricks.yml           # Main config
├── resources/
│   ├── jobs.yml            # Job definitions
│   ├── pipelines.yml       # Pipeline definitions
│   └── models.yml          # Model registrations
├── src/
│   ├── notebooks/
│   │   └── my_notebook.py
│   ├── python/
│   │   └── my_module.py
│   └── sql/
│       └── query.sql
├── tests/
│   └── test_notebook.py
└── .gitignore
```

#### databricks.yml Example
```yaml
bundle:
  name: my-analytics-bundle
  version: 0.1.0

variables:
  environment:
    description: Deployment environment
    default: dev
  spark_version:
    default: 12.2.x-scala2.12

targets:
  dev:
    variables:
      environment: dev
  prod:
    variables:
      environment: prod

resources:
  jobs:
    etl_job:
      name: daily-etl-${var.environment}
      tasks:
        - task_key: extract
          notebook_task:
            notebook_path: ./src/notebooks/extract
          existing_cluster_id: ${resources.clusters.main.id}
        
        - task_key: load
          depends_on:
            - task_key: extract
          notebook_task:
            notebook_path: ./src/notebooks/load
          existing_cluster_id: ${resources.clusters.main.id}
      
      schedule:
        quartz_cron_expression: '0 0 8 ? * MON-FRI'

  clusters:
    main:
      cluster_name: bundle-cluster-${var.environment}
      spark_version: ${var.spark_version}
      node_type_id: Standard_DS3_v2
      num_workers: 2
      autotermination_minutes: 15
```

#### Deploy Bundle
```bash
# Validate configuration
databricks bundle validate

# Deploy to workspace
databricks bundle deploy

# Deploy to specific target
databricks bundle deploy -t prod

# Run job from bundle
databricks bundle run etl_job

# Destroy resources
databricks bundle destroy
```

### B. CI/CD Pipelines with GitHub Actions

#### .github/workflows/deploy.yml
```yaml
name: Deploy Databricks Bundle

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Databricks CLI
        run: pip install databricks-cli
      
      - name: Validate Bundle
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: databricks bundle validate
      
      - name: Deploy Bundle
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: databricks bundle deploy -t prod
```

### C. Manual Deployment via Python

```python
import subprocess
import os

# Set environment
os.environ['DATABRICKS_HOST'] = 'https://workspace.azuredatabricks.net'
os.environ['DATABRICKS_TOKEN'] = 'dapi...'

# Validate
result = subprocess.run(['databricks', 'bundle', 'validate'], cwd='./bundle')
if result.returncode != 0:
    raise Exception("Validation failed")

# Deploy
result = subprocess.run(['databricks', 'bundle', 'deploy', '-t', 'prod'], cwd='./bundle')
if result.returncode == 0:
    print("Deployment successful")
```

---

## Best Practices

### Authentication & Security
1. **Use service principals for CI/CD**, not personal credentials
2. **Store secrets in Azure Key Vault**, not in code or `.databrickscfg`
3. **Rotate credentials regularly** (especially OAuth M2M tokens)
4. **Use environment variables** over hardcoding credentials
5. **Restrict PAT scopes** to minimum necessary permissions
6. **Enable IP access lists** for workspace security
7. **Never commit `.databrickscfg`** to version control

### Configuration Management
```bash
# Example: Different configs per environment
~/.databrickscfg

[DEFAULT]
host = https://dev.azuredatabricks.net
token = dapi...

[PROD]
host = https://prod.azuredatabricks.net
token = dapi...
```

```python
# Use profiles in code
dev = WorkspaceClient(profile='DEFAULT')
prod = WorkspaceClient(profile='PROD')
```

### Code Organization
1. **Separate notebooks by function** (extract, transform, load)
2. **Use shared Python libraries** for reusable code
3. **Version control all code** (Git)
4. **Package code as wheels** for production deployments
5. **Use bundles for complex projects** with multiple contributors
6. **Test locally** before deploying to production

### Job & Cluster Management
1. **Use job clusters** for isolated workloads (preferred over all-purpose)
2. **Enable auto-termination** to reduce costs
3. **Pin Spark versions** for reproducibility
4. **Use existing clusters only** for development/testing
5. **Set appropriate timeouts** to catch hanging jobs
6. **Configure retries** for resilient jobs
7. **Monitor job runs** via workspace metrics

### Performance Optimization
```python
# Use caching for SDK operations
@property
def workspace_client(self):
    # Reuse client connections
    if not hasattr(self, '_client'):
        self._client = WorkspaceClient()
    return self._client

# Batch operations where possible
clusters = list(w.clusters.list())  # Get all at once

# Use generator for large result sets
for run in w.jobs.list_runs(job_id='123'):
    process(run)  # Lazy evaluation
```

### Error Handling
```python
from databricks.sdk.errors import ResourceDoesNotExist, DeadlineExceeded
import datetime

try:
    cluster = w.clusters.get(cluster_id='invalid-id')
except ResourceDoesNotExist:
    print("Cluster not found")
except Exception as e:
    print(f"Error: {e}")

# Handle job timeouts
try:
    result = waiter.result(timeout=datetime.timedelta(minutes=60))
except DeadlineExceeded:
    print("Job timed out")
```

### Testing & Validation
```python
# Mock SDK for testing
from unittest.mock import create_autospec

mock_client = create_autospec(WorkspaceClient)
mock_client.clusters.list.return_value = [...]

# Test without hitting real API
result = your_function(w=mock_client)
assert result is not None
```

### Logging & Monitoring
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable debug logging for SDK
logging.getLogger('databricks.sdk').setLevel(logging.DEBUG)

# Log job runs
for run in w.jobs.list_runs(job_id='123'):
    logger.info(f"Run {run.run_id}: {run.state.result_state}")
```

---

## Quick Reference: Common Workflows

### Authenticate & List Clusters
```bash
# CLI
databricks configure --token
databricks clusters list

# Python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
for c in w.clusters.list():
    print(c.cluster_name)
```

### Upload & Run Notebook
```bash
# CLI
databricks workspace import my_notebook.py /Users/my_notebook
databricks jobs create --json-file job.json
databricks jobs run-now --job-id <job-id>
```

### Deploy with Bundles
```bash
databricks bundle init
# Edit databricks.yml
databricks bundle validate
databricks bundle deploy -t prod
```

---

Built with Azure Databricks SDK and CLI. Last updated: May 2026