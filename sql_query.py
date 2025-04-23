from typing import List, Dict, Any, Union
import logging
import psycopg2
from psycopg2.extensions import connection, cursor

def get_schemas_and_tables(
    conn_or_cursor: Union[connection, cursor],
    config: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Fetches all user-defined schemas, their tables, and column counts in a single query.
    Returns a list of dictionaries with schema details, table counts, and column counts
    for tables and columns where the user has SELECT privileges.

    Args:
        conn_or_cursor: A psycopg2 connection or cursor object.
        config: Optional configuration dictionary with keys:
            - schema_filter: List of schema names to include (default: None, all schemas).
            - exclude_schemas: Additional schemas to exclude (default: None).
            - connection_params: Dict for psycopg2.connect (ignored if conn_or_cursor is provided).

    Returns:
        List of dictionaries, each containing:
            - schema_name: Name of the schema.
            - table_count: Number of tables in the schema.
            - tables: List of dicts with table name and column count.
            - failed_tables: List of tables that failed (empty in this implementation).
    """
    if config is None:
        config = {}

    # Base excluded schemas
    exclude_schemas = ["pg_catalog", "information_schema", "pg_toast"]
    if config.get("exclude_schemas"):
        exclude_schemas.extend(config.get("exclude_schemas"))

    # Build schema filter condition
    schema_filter = config.get("schema_filter")
    schema_condition = ""
    if schema_filter:
        schema_filter = [s for s in schema_filter if s not in exclude_schemas]
        if schema_filter:
            schema_condition = f"AND n.nspname = ANY(%s)"
            query_params = [schema_filter]
        else:
            query_params = []
    else:
        query_params = []

    query = f"""
        WITH schema_tables AS (
            SELECT
                n.nspname AS schema_name,
                c.relname AS table_name,
                COUNT(a.attnum) FILTER (WHERE has_column_privilege(c.oid, a.attname, 'SELECT')) AS col_count
            FROM pg_catalog.pg_namespace n
            JOIN pg_catalog.pg_class c ON n.oid = c.relnamespace
            LEFT JOIN pg_catalog.pg_attribute a ON c.oid = a.attrelid
                AND a.attnum > 0
                AND NOT a.attisdropped
            WHERE n.nspname NOT IN %s
                AND c.relkind = 'r'
                AND has_schema_privilege(n.nspname, 'USAGE')
                AND has_table_privilege(c.oid, 'SELECT')
                {schema_condition}
            GROUP BY n.nspname, c.relname
            HAVING COUNT(a.attnum) FILTER (WHERE has_column_privilege(c.oid, a.attname, 'SELECT')) > 0
        )
        SELECT
            schema_name,
            array_agg(
                jsonb_build_object(
                    'name', table_name,
                    'col_count', col_count
                )
            ) AS tables,
            COUNT(*) AS table_count
        FROM schema_tables
        GROUP BY schema_name
        ORDER BY schema_name;
    """

    results = []
    own_cursor = False
    try:
        # Determine if we need to create a cursor
        if isinstance(conn_or_cursor, psycopg2.extensions.connection):
            cur = conn_or_cursor.cursor()
            own_cursor = True
        else:
            cur = conn_or_cursor

        # Execute query with parameters
        cur.execute(query, (tuple(exclude_schemas), *query_params))

        # Process results
        for row in cur.fetchall():
            schema_name, tables, table_count = row
            results.append({
                "schema_name": schema_name,
                "table_count": table_count,
                "tables": tables,
                "failed_tables": []
            })

        return results
    except psycopg2.ProgrammingError as e:
        logging.error(f"Error executing schema and table query: {str(e)}")
        return []
    finally:
        if own_cursor and isinstance(conn_or_cursor, psycopg2.extensions.connection):
            cur.close()
