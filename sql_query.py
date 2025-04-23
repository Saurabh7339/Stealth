from typing import List, Dict, Any
import logging
import psycopg2
from psycopg2 import ProgrammingError
import json

def get_schemas_and_tables(
    hostname: str,
    database: str,
    user: str,
    password: str,
    port: str,
    config: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Fetches all user-defined schemas, their tables, and column counts in a single query.
    Returns a list of dictionaries with schema details, table counts, and column counts
    for tables and columns where the user has SELECT privileges.

    Args:
        hostname: Database server hostname.
        database: Database name.
        user: Database user.
        password: User password.
        port: Database port.
        config: Optional configuration dictionary with keys:
            - schema_filter: List of schema names to include (default: None, all schemas).
            - exclude_schemas: Additional schemas to exclude (default: None).

    Returns:
        List of dictionaries, each containing:
            - schema_name: Name of the schema.
            - table_count: Number of tables in the schema.
            - tables: List of dicts with table name and column count.
            - failed_tables: List of tables that failed (empty in this implementation).
    """

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
		WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
			AND c.relkind = 'r'
			AND has_schema_privilege(n.nspname, 'USAGE')
			AND has_table_privilege(c.oid, 'SELECT')
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
    conn = None
    cur = None
    try:
        # Establish connection
        conn = psycopg2.connect(
            host=hostname,
            dbname=database,
            user=user,
            password=password,
            port=port
        )
        cur = conn.cursor()

        # Execute query with parameters
        cur.execute(query)

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
    except (ProgrammingError, psycopg2.OperationalError) as e:
        logging.error(f"Error executing schema and table query: {str(e)}")
        return []
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
