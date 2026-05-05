from app import MockDatabricksClient, execute_command

client = MockDatabricksClient()

commands = [
    'show tables',
    'run query SELECT * FROM sample_catalog.sample_schema.table1',
    'manage cluster list',
    'manage cluster start mock-2',
    'retrieve data sample_catalog.sample_schema.table2',
    'compare tables sample_catalog.sample_schema.table1 sample_catalog.sample_schema.table2'
]

for command in commands:
    print('COMMAND:', command)
    result = execute_command(command, client)
    if 'error' in result:
        print('ERROR:', result['error'])
    if 'text' in result:
        print(result['text'])
    if 'data' in result:
        data = result['data']
        if hasattr(data, 'head'):
            print(data.head())
        else:
            print(data)
    print('-' * 80)
