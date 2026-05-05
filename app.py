import streamlit as st
import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List

st.set_page_config(page_title='Databricks Chatbot', layout='wide')


class MockDatabricksClient:
    def __init__(self):
        self.clusters = [
            {'cluster_id': 'mock-1', 'cluster_name': 'demo-cluster', 'state': 'RUNNING'},
            {'cluster_id': 'mock-2', 'cluster_name': 'test-cluster', 'state': 'TERMINATED'}
        ]
        self.tables = self._build_sample_tables()

    def _build_sample_tables(self) -> Dict[str, pd.DataFrame]:
        sample_a = pd.DataFrame({
            'customer_id': [1, 2, 3, 4],
            'amount': [100.0, 200.123456, 300.0, 400.000001],
            'status': ['Active', 'Inactive', 'Active', 'Active']
        })

        sample_b = pd.DataFrame({
            'id': ['001', '2', '03', '4'],
            'total': [100.0000001, 200.12345, 300.0, 400.0],
            'state': ['active', 'inactive', 'ACTIVE', 'active']
        })

        sample_orders = pd.DataFrame({
            'order_id': [11, 12, 13],
            'customer_id': [1, 2, 4],
            'quantity': [2, 1, 5],
            'order_amount': [20.0, 15.5, 55.0]
        })

        return {
            'sample_catalog.sample_schema.table1': sample_a,
            'sample_catalog.sample_schema.table2': sample_b,
            'sample_catalog.sample_schema.orders': sample_orders,
        }

    def list_clusters(self) -> List[Dict[str, Any]]:
        return self.clusters

    def start_cluster(self, cluster_id: str) -> str:
        for cluster in self.clusters:
            if cluster['cluster_id'] == cluster_id:
                cluster['state'] = 'RUNNING'
                return f"Cluster {cluster_id} is now RUNNING."
        return f"Cluster {cluster_id} not found."

    def terminate_cluster(self, cluster_id: str) -> str:
        for cluster in self.clusters:
            if cluster['cluster_id'] == cluster_id:
                cluster['state'] = 'TERMINATED'
                return f"Cluster {cluster_id} is now TERMINATED."
        return f"Cluster {cluster_id} not found."

    def show_tables(self) -> List[str]:
        return list(self.tables.keys())

    def get_table(self, table_name: str) -> pd.DataFrame:
        key = table_name.strip()
        if key in self.tables:
            return self.tables[key]
        raise ValueError(f'Table {table_name} not found in mock catalog.')

    def run_query(self, query: str) -> Any:
        query = query.strip().lower()
        if query.startswith('select * from'):
            match = re.search(r'select \* from ([\w\.]+)', query)
            if match:
                table_name = match.group(1)
                return self.get_table(table_name)
        if query == 'show tables':
            return pd.DataFrame({'table_name': self.show_tables()})
        if query.startswith('describe table'):
            match = re.search(r'describe table ([\w\.]+)', query)
            if match:
                table_name = match.group(1)
                df = self.get_table(table_name)
                return pd.DataFrame({'column': df.columns, 'dtype': df.dtypes.astype(str).values})
        raise ValueError('Mock query parser currently supports: SELECT * FROM <table>, SHOW TABLES, DESCRIBE TABLE <table>.')


def normalize_value(value: Any) -> str:
    if pd.isna(value):
        return 'nan'
    if isinstance(value, str):
        text = value.strip().lower()
        if text.isdigit():
            text = str(int(text))
        return text
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        return f"{round(float(value), 5):.5f}"
    return str(value).strip().lower()


def compare_tables(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    df1 = df1.copy()
    df2 = df2.copy()
    df1.columns = [str(col).lower() for col in df1.columns]
    df2.columns = [str(col).lower() for col in df2.columns]

    matrix = pd.DataFrame(index=df1.columns, columns=df2.columns, dtype=float)
    max_rows = max(len(df1), len(df2), 1)
    summary = []

    for col1 in df1.columns:
        for col2 in df2.columns:
            values1 = df1[col1].astype(object).apply(normalize_value).tolist()
            values2 = df2[col2].astype(object).apply(normalize_value).tolist()
            row_pairs = min(len(values1), len(values2))
            if row_pairs == 0:
                matrix.loc[col1, col2] = np.nan
                continue
            matches = sum(values1[i] == values2[i] for i in range(row_pairs))
            matrix.loc[col1, col2] = round(matches / row_pairs * 100, 2)
            summary.append(matches / row_pairs)

    return matrix


def execute_command(command: str, client: MockDatabricksClient) -> Dict[str, Any]:
    command = command.strip()
    if not command:
        return {'error': 'No command entered.'}

    if command.lower() == 'show tables':
        return {'data': pd.DataFrame({'available_tables': client.show_tables()})}

    if command.lower().startswith('run query'):
        sql = command[len('run query'):].strip()
        if not sql:
            return {'error': 'Please specify a SQL query after run query.'}
        try:
            result = client.run_query(sql)
            return {'data': result}
        except Exception as exc:
            return {'error': str(exc)}

    if command.lower().startswith('manage cluster'):
        action = command[len('manage cluster'):].strip().lower()
        if action == 'list':
            return {'text': pd.DataFrame(client.list_clusters()).to_string(index=False)}
        if action.startswith('start '):
            cluster_id = action[len('start '):].strip()
            return {'text': client.start_cluster(cluster_id)}
        if action.startswith('terminate ') or action.startswith('stop '):
            cluster_id = action.split(' ', 1)[1].strip()
            return {'text': client.terminate_cluster(cluster_id)}
        return {'error': 'Cluster command must be one of: list, start <id>, terminate <id>.'}

    if command.lower().startswith('retrieve data'):
        table_name = command[len('retrieve data'):].strip()
        if not table_name:
            return {'error': 'Please specify a table name after retrieve data.'}
        try:
            df = client.get_table(table_name)
            return {'data': df}
        except Exception as exc:
            return {'error': str(exc)}

    if command.lower().startswith('compare tables'):
        args = command[len('compare tables'):].strip().split()
        if len(args) != 2:
            return {'error': 'Please provide two full table names: compare tables <table1> <table2>.'}
        try:
            df1 = client.get_table(args[0])
            df2 = client.get_table(args[1])
            matrix = compare_tables(df1, df2)
            overall = matrix.stack().mean()
            return {
                'text': f'Comparison complete. Average column match percentage: {overall:.2f}%.',
                'data': matrix
            }
        except Exception as exc:
            return {'error': str(exc)}

    return {'error': 'Unknown command. Valid commands: show tables, run query <sql>, manage cluster <list|start|terminate>, retrieve data <table>, compare tables <table1> <table2>.'}


def main():
    st.title('Databricks Chatbot Interface')
    st.write('Use natural command styles to run queries, manage clusters, retrieve data, and compare tables.')

    if 'history' not in st.session_state:
        st.session_state.history = []

    if 'client' not in st.session_state:
        st.session_state.client = MockDatabricksClient()

    with st.expander('Sample Commands', expanded=True):
        st.markdown(
            '''
            - `show tables`
            - `run query SELECT * FROM sample_catalog.sample_schema.table1`
            - `manage cluster list`
            - `manage cluster start mock-2`
            - `manage cluster terminate mock-1`
            - `retrieve data sample_catalog.sample_schema.table2`
            - `compare tables sample_catalog.sample_schema.table1 sample_catalog.sample_schema.table2`
            '''
        )

    command = st.text_input('Enter your Databricks command', key='command_input')
    if st.button('Submit Command'):
        result = execute_command(command, st.session_state.client)
        st.session_state.history.append({'command': command, 'result': result})

    if st.session_state.history:
        st.header('Command History')
        for entry in reversed(st.session_state.history[-10:]):
            st.subheader(f'Command: {entry["command"]}')
            if 'error' in entry['result']:
                st.error(entry['result']['error'])
            if 'text' in entry['result']:
                st.write(entry['result']['text'])
            if 'data' in entry['result']:
                data = entry['result']['data']
                if isinstance(data, pd.DataFrame):
                    st.dataframe(data)
                else:
                    st.write(data)

    st.markdown('---')
    st.write('This chatbot runs with mock Databricks data and command responses for local testing.')


if __name__ == '__main__':
    main()
