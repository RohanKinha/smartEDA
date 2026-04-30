"""
SQL Query Module for SmartEDA
Enables SQL-based querying of uploaded DataFrames via pandasql.
"""

import pandas as pd
from typing import Tuple, Optional


def run_sql_query(df: pd.DataFrame, query: str, table_name: str = "df") -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Execute a SQL query on the given DataFrame.
    
    Args:
        df: The uploaded dataset as a pandas DataFrame.
        query: SQL query string. Use the table name 'df' (or the provided table_name).
        table_name: The alias for the DataFrame in the query (default: 'df').
    
    Returns:
        (result_df, error_message): One of them will be None.
    """
    try:
        import pandasql as psql
        # Make a local variable with the correct name so pandasql can find it
        local_vars = {table_name: df}
        result = psql.sqldf(query, local_vars)
        return result, None
    except ImportError:
        return None, "pandasql is not installed. Run: pip install pandasql"
    except Exception as e:
        return None, f"SQL Error: {str(e)}"


def get_sql_examples(columns: list, table_name: str = "df") -> list:
    """Return example SQL queries tailored to the dataset's column names."""
    examples = [
        f"SELECT * FROM {table_name} LIMIT 10",
        f"SELECT COUNT(*) as total_rows FROM {table_name}",
    ]
    if columns:
        col = columns[0]
        examples.append(f"SELECT {col}, COUNT(*) as count FROM {table_name} GROUP BY {col} ORDER BY count DESC LIMIT 10")
    if len(columns) >= 2:
        col1, col2 = columns[0], columns[1]
        examples.append(f"SELECT {col1}, {col2} FROM {table_name} WHERE {col1} IS NOT NULL LIMIT 20")
    return examples
