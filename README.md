# AI-Copilot: Databricks Chatbot with Mock Data

> **TLDR:** An interactive Streamlit chatbot for simulating Databricks operations with mock data, including cluster management, SQL queries, data retrieval, and table comparisons. Includes comprehensive guides for Azure Databricks, MLflow, and Streamlit agent patterns.

## Features

- **Interactive Chatbot UI**: Built with Streamlit for real-time command processing
- **Mock Databricks Client**: Simulates clusters, tables, and queries without requiring actual Databricks setup
- **Command Support**:
  - `show tables` - List available tables
  - `run query <SQL>` - Execute SQL queries (SELECT * FROM supported)
  - `manage cluster <list|start|terminate>` - Cluster operations
  - `retrieve data <table>` - Fetch table data
  - `compare tables <table1> <table2>` - Column-wise data comparison
- **Session State Persistence**: Maintains chat history across interactions
- **Comprehensive Documentation**: Guides for Azure Databricks, MLflow, and Streamlit development

## Project Structure

```
AI-Copilot/
├── app.py                          # Main Streamlit chatbot application
├── test_mock.py                    # Test harness for chatbot commands
├── requirements-chatbot.txt        # Lightweight dependencies for the app
├── Requirements.txt                # Original comprehensive requirements list
├── Agents.md                       # Streamlit agent patterns and best practices
├── Azure-Databricks-Guide.md       # Complete Azure Databricks setup and usage
├── MLFlow.md                       # End-to-end MLflow lifecycle guide
├── StreamlitAgent.md               # Databricks dataset exploration patterns
├── index.html                      # Basic HTML landing page
├── install-uv.ps1                  # PowerShell script for uv installation
└── README.md                       # This file
```

## Installation

### Prerequisites

- Python 3.8+ (recommended: Python 3.10 or 3.11)
- Git (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone https://github.com/smritiraj22/AI-Copilot.git
cd AI-Copilot
```

### Step 2: Install Dependencies

Using pip:
```bash
pip install -r requirements-chatbot.txt
```

Or using uv (faster package manager):
```bash
# Install uv first (if not already installed)
# On Windows:
./install-uv.ps1

# Then install dependencies
uv pip install -r requirements-chatbot.txt
```

### Step 3: Run the Application

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`.

## Usage

### Running the Chatbot

1. Open the Streamlit app in your browser
2. Use the sample commands provided in the expandable section, or enter custom commands
3. The chatbot processes commands and displays results in real-time
4. Command history is maintained across the session

### Sample Commands

- `show tables` - Display all available mock tables
- `run query SELECT * FROM sample_catalog.sample_schema.table1` - Query a specific table
- `manage cluster list` - Show cluster status
- `manage cluster start mock-2` - Start a cluster
- `retrieve data sample_catalog.sample_schema.table2` - Fetch table data
- `compare tables sample_catalog.sample_schema.table1 sample_catalog.sample_schema.table2` - Compare two tables

### Testing

Run the test harness to verify functionality:

```bash
python test_mock.py
```

This will execute sample commands and display results.

## Mock Data Structure

The app includes sample tables with realistic data:

- **table1**: Customer data (customer_id, amount, status)
- **table2**: Transaction data (id, total, state)
- **orders**: Order data (order_id, customer_id, quantity, order_amount)

All tables are under the `sample_catalog.sample_schema` namespace.

## Development

### Adding New Commands

1. Extend the `execute_command()` function in `app.py`
2. Add command parsing logic
3. Update the `MockDatabricksClient` class if needed
4. Add tests to `test_mock.py`

### Environment Setup

For development with uv:

```bash
# Create virtual environment
uv venv

# Activate (Windows)
.venv\Scripts\activate

# Install in editable mode
uv pip install -e .
```

## Deployment

### Local Development

```bash
streamlit run app.py --server.port 8501 --server.headless false
```

### Streamlit Community Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Deploy (no secrets needed for mock version)

### Production with Real Databricks

To connect to actual Databricks:

1. Install `databricks-sdk`
2. Update `MockDatabricksClient` to use real Databricks API
3. Add secrets for authentication (host, token)
4. See `Azure-Databricks-Guide.md` for setup details

## Documentation

- **[Agents.md](Agents.md)**: Streamlit agent patterns and best practices
- **[Azure-Databricks-Guide.md](Azure-Databricks-Guide.md)**: Complete Azure Databricks setup
- **[MLFlow.md](MLFlow.md)**: MLflow model lifecycle management
- **[StreamlitAgent.md](StreamlitAgent.md)**: Databricks dataset exploration

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Built With

- [Streamlit](https://streamlit.io) - Web app framework
- [Pandas](https://pandas.pydata.org) - Data manipulation
- [NumPy](https://numpy.org) - Numerical computing
- [Databricks SDK](https://docs.databricks.com/dev-tools/sdk-python.html) - Databricks integration

---

**Repository:** [https://github.com/smritiraj22/AI-Copilot](https://github.com/smritiraj22/AI-Copilot)

Built for demonstrating Databricks chatbot interactions with mock data.</content>
<parameter name="filePath">c:\Users\mails\OneDrive\AI\README.md