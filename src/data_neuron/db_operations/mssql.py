from .base import DatabaseOperations


class MSSQLOperations(DatabaseOperations):
    def __init__(self, server: str, database: str, username: str, password: str):
        self.conn_params = {
            "server": server,
            "database": database,
            "username": username,
            "password": password
        }
        self.conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

    def _get_connection(self):
        try:
            import pyodbc
            return pyodbc.connect(self.conn_str)
        except ImportError:
            raise ImportError(
                "MSSQL support is not installed. Please install it with 'pip install your_cli_tool[mssql]'")

    def get_table_list(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
                    return [table[0] for table in cursor.fetchall()]
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def get_table_info(self, table_name):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT 
                            c.COLUMN_NAME, 
                            c.DATA_TYPE,
                            c.IS_NULLABLE,
                            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END AS IS_PRIMARY_KEY
                        FROM 
                            INFORMATION_SCHEMA.COLUMNS c
                            LEFT JOIN (
                                SELECT ku.COLUMN_NAME
                                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                                    ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                                WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                                AND ku.TABLE_NAME = ?
                            ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
                        WHERE 
                            c.TABLE_NAME = ?
                    """, (table_name, table_name))
                    columns = cursor.fetchall()
                    return {
                        'table_name': table_name,
                        'columns': [
                            {
                                'name': col[0],
                                'type': col[1],
                                'nullable': col[2] == 'YES',
                                'primary_key': col[3] == 1
                            } for col in columns
                        ]
                    }
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def execute_query(self, query: str) -> str:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    return "\n".join([str(row) for row in results])
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def get_schema_info(self) -> str:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        ORDER BY TABLE_NAME, ORDINAL_POSITION
                    """)
                    results = cursor.fetchall()
                    schema_info = []
                    current_table = ""
                    for row in results:
                        if row[0] != current_table:
                            current_table = row[0]
                            schema_info.append(f"\nTable: {current_table}")
                        schema_info.append(f"  {row[1]} ({row[2]})")
                    return "\n".join(schema_info)
        except Exception as e:
            return f"An error occurred: {str(e)}"
