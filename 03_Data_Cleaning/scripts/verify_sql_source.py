"""Optional read-only SQL reconciliation. Does not export or modify source data."""
from pathlib import Path
import hashlib
import json
import pandas as pd
import pyodbc

BASE = Path(__file__).resolve().parent      # 03_Data_Cleaning/scripts
REPORTS = BASE.parent / 'reports'
ROOT = BASE.parent.parent              # project root


def verify():
    specs = json.loads((BASE / 'cleaning_schema.json').read_text())['datasets']
    drivers = pyodbc.drivers()
    driver = next((d for d in ['ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server'] if d in drivers), None)
    if driver is None:
        raise RuntimeError('No supported SQL Server ODBC driver is installed')
    connection = pyodbc.connect(
        'DRIVER={' + driver + r'};SERVER=OMAR\SQLEXPRESS;DATABASE=WideWorldImporters;'
        'Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;ApplicationIntent=ReadOnly',
        autocommit=True, timeout=20)
    connection.timeout = 120
    cursor = connection.cursor()
    server, database = cursor.execute('SELECT @@SERVERNAME, DB_NAME()').fetchone()
    if database != 'WideWorldImporters':
        raise RuntimeError('Wrong database')
    results, external = [], []
    try:
        for name, spec in specs.items():
            file = ROOT / '00_Source_Data/CSV_Exports' / (name + '.csv')
            fingerprint = hashlib.sha256(file.read_bytes()).hexdigest()
            raw = pd.read_csv(file, encoding='utf-8-sig', dtype='string', keep_default_na=False, na_values=[r'\N'])
            schema, table = spec['table'].split('.')
            table_sql = f'[{schema}].[{table}]'
            key = spec['primary_key']
            expressions = []
            for col in spec['columns']:
                field, kind = col['name'], col['sql_type']
                style = ',23' if kind == 'date' else ',126' if kind in ('datetime2','datetime') else ''
                expressions.append(f'CONVERT(nvarchar(max),[{field}]{style}) AS [{field}]')
            query = 'SELECT ' + ','.join(expressions) + f' FROM {table_sql} ORDER BY [{key}]'
            count_before = cursor.execute(f'SELECT COUNT_BIG(*) FROM {table_sql}').fetchval()
            data = cursor.execute(query).fetchall()
            source = pd.DataFrame.from_records([tuple(r) for r in data], columns=raw.columns).astype('string')
            count_after = cursor.execute(f'SELECT COUNT_BIG(*) FROM {table_sql}').fetchval()
            if not raw[key].is_unique or not source[key].is_unique or raw[key].isna().any():
                raise ValueError(f'{name}: invalid key')
            left, right = raw.set_index(key).sort_index(), source.set_index(key).sort_index()
            if not left.index.equals(right.index):
                raise ValueError(f'{name}: SQL/CSV key sets differ')
            differences = int((~(left.eq(right) | (left.isna() & right.isna()))).fillna(True).sum().sum())
            passed = differences == 0 and count_before == count_after == len(raw) == len(source)
            results.append({'dataset': name, 'rows': len(raw), 'columns': len(raw.columns),
                            'compared_cells': int(raw.size), 'differences': differences,
                            'source_sha256': fingerprint, 'SQL_count_before': count_before,
                            'SQL_count_after': count_after, 'status': 'PASS' if passed else 'FAIL', 'query': query})
            for fk in spec['foreign_keys']:
                if fk['parent'] in specs:
                    continue
                ps, pt = fk['parent'].split('_', 1)
                field, pk = fk['column'], fk['parent_key']
                sql = (f'SELECT COUNT_BIG(*) FROM {table_sql} c LEFT JOIN [{ps}].[{pt}] p '
                       f'ON c.[{field}]=p.[{pk}] WHERE c.[{field}] IS NOT NULL AND p.[{pk}] IS NULL')
                count = cursor.execute(sql).fetchval()
                external.append({'dataset': name, 'column': field, 'parent': fk['parent'],
                                 'orphans': count, 'status': 'PASS' if count == 0 else 'FAIL', 'query': sql})
            print(name, 'PASS' if passed else 'FAIL', flush=True)
    finally:
        connection.close()
    evidence = {'server': server, 'database': database,
                'scope': 'Read-only SELECTs, selected current columns, matched by primary key. Separate reads are not an atomic snapshot.',
                'results': results, 'external_relationships': external}
    (REPORTS/'sql_source_verification.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    if any(x['status'] != 'PASS' for x in results + external):
        raise RuntimeError('SQL reconciliation failed; see saved evidence')
    return evidence


if __name__ == '__main__':
    verify()
