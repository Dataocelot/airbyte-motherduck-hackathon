import os
import sys

import duckdb
from dotenv import load_dotenv

from helper.logger import Logger

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

load_dotenv()

logger_instance = Logger()
logger = logger_instance.get_logger()


def get_duckdb_conn(db_name: str, api_key: str) -> duckdb.duckdb.DuckDBPyConnection:
    """
    Connects to Duckdb

    Parameters
    ----------
    db_name : str
        the name of the db
    api_key : str
        your api_key for Duckdb

    Returns
    -------
    duckdb.duckdb.DuckDBPyConnection
        if successful, your Duckdb connection
    """
    try:
        conn = duckdb.connect(f"md:{db_name}?motherduck_token={api_key}")
    except duckdb.duckdb.DatabaseError as db_error:
        logger.exception(
            f"Unable to connect to DB, check connection details {db_error}"
        )
        conn = None
    return conn


def get_query_results(
    duckdb_conn: duckdb.duckdb.DuckDBPyConnection, query: str
) -> list:
    """
    Query the Duckdb Database

    Parameters
    ----------
    duckdb_conn : duckdb.duckdb.DuckDBPyConnection
        The connection to duckdb
    query : str
        The SQL quuery

    Returns
    -------
    list
        A list of the results
    """
    results = []
    try:
        results = duckdb_conn.sql(query).fetchall()
    except duckdb.duckdb.DatabaseError as db_error:
        logger.exception(f"Unable to query DB, check connection details{db_error}")
    return results


def is_schema_exists(duckdb_conn, schema_name: str) -> bool:
    """
    Checks if a schema exists in the Motherduck Warehouse

    Parameters
    ----------
    duckdb_conn : duckdb.duckdb.DuckDBPyConnection
        The Duckdb connection
    schema_name : str
        the name of the db

    Returns
    -------
    bool
        True if the db exists else False
    """
    try:
        results = duckdb_conn.sql(
            f"SELECT * FROM information_schema.tables where table_schema='{schema_name}'"
        ).fetchall()
    except duckdb.duckdb.CatalogException:
        logger.exception("Schema does not exist")
        return False
    if not results:
        return False
    return True


def is_table_exists(duckdb_conn, schema_name: str, table_name: str) -> bool:
    """
    Checks if a table exists in the Motherduck Warehouse

    Parameters
    ----------
    duckdb_conn : duckdb.duckdb.DuckDBPyConnection
        The Duckdb connection
    schema_name : str
        the name of the db
    table_name: str
        the name of the table

    Returns
    -------
    bool
        True if the table exists else False
    """
    try:
        results = duckdb_conn.sql(
            f"SELECT 1 FROM {schema_name}.{table_name}"
        ).fetchall()
    except duckdb.duckdb.CatalogException:
        logger.exception("Schema does not exist")
        return False
    if not results:
        return False
    return True
