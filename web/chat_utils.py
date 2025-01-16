import json
import os
import sys

import duckdb
import google.generativeai as genai
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
        results = duckdb_conn.sql(query).fetchdf().to_json(orient="values")
    except duckdb.duckdb.DatabaseError as db_error:
        logger.exception(f"Unable to query DB, check connection details{db_error}")
    return results


def get_column_value(
    duckdb_conn: duckdb.duckdb.DuckDBPyConnection,
    col_name: str,
    brand: str,
    model_number,
    product,
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
        query = f"""
            SELECT _airbyte_data.{col_name}
            FROM
            _airbyte_raw_hackathon_manual_sections
            WHERE (_airbyte_data->>'brand')='{brand}'
            AND (_airbyte_data->>'device')='{product}'
            AND (_airbyte_data->>'model_number')='{model_number}'
        """
        # query = f"""
        #     SELECT _airbyte_data.{col_name}
        #     FROM
        #     _airbyte_raw_hackathon_manual_sections
        #     WHERE (_airbyte_data->>'brand')='BEKO'
        #     AND (_airbyte_data->>'device')='Dishwasher'
        #     AND (_airbyte_data->>'model_number')='DIS15010'
        # """
        logger.info(f"Query: {query}")
        results = duckdb_conn.sql(query).fetchdf().to_json(orient="values")
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
    except duckdb.CatalogException:
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
        results = (
            duckdb_conn.sql(f"SELECT 1 FROM {schema_name}.{table_name}")
            .fetchdf()
            .to_json(orient="values")[0]
        )
    except duckdb.CatalogException:
        logger.exception("Schema does not exist")
        return False
    if not results:
        return False
    return True


# Create the model
def create_model(model_name: str = "gemini-2.0-flash-exp", **kwargs):
    """
    Create a generative model using the specified model name and configuration.

    Parameters
    ----------
    model_name : str
        The name of the model to create.
    kwargs : dict
        Additional keyword arguments to configure the model.

    Returns
    -------
    GenerativeModel
        The created generative model.
    """
    generation_config = kwargs

    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
    )
    return model


def does_user_need_asssitance(gemini_model, user_prompt) -> bool:
    """
    Tells if the user is asking a question

    Returns
    -------
    bool
        True if a question else, alse
    """

    resp = gemini_model.start_chat(
        history=[
            {
                "role": "user",
                "parts": f"""
                **Task**
                You are meant to determine, if the user is asking for something related to maintaining or troubleshooting a device or needs technical help,
                if so, Answer by giving True or False, True of the sentiment is related to fixing something or an issue else False

                **Result**
                The expected output format you should return is {{user_needs_assistance: bool}}

                **User prompt**
                Here is the user prompt {user_prompt}

                """,
            },
        ]
    )
    json_response = json.loads(resp.text)
    return json_response.get("user_needs_asssitance", False)


def determine_relevant_section_for_help(
    gemini_model, table_of_content: list, user_prompt: str
) -> list:
    chat_session = gemini_model.start_chat(
        history=[
            {
                "role": "user",
                "parts": f"""
                **Task**
                You are an Expert Technician in electrical appliances and devices. You can quickly look at the table of contents of User manuals
                and service manuals to highlight relevant sections that can help anyone troubleshoot or use a device.

                Given this Table of contents list containing section names, can you give the top 1 section name where a user might
                find the answer to this question. If you don't think there is any return an empty list.

                {table_of_content}

                **Result**
                The expected output format you should return is a list of strings
                It should follow this pattern [string]

                example output
                ['troubleshooting_section'], []

                **User prompt**
                Here is the user's question {user_prompt}
                """,
            },
        ]
    )
    resp = chat_session.send_message("pathob\n")
    json_response = json.loads(resp.text)
    return json_response


def get_relevant_markdown_content(
    motherduck_conn,
    helper_sections: list,
    brand: str,
    device: str,
    model_number: str,
) -> list:
    # user_counter = 0
    # is user asking a question (satisfied or not)?
    # Get content from motherduck
    result = []
    if helper_sections:
        top_content_name = helper_sections[0]
        query = f"""
            SELECT _airbyte_data.markdown_text
            FROM
            _airbyte_raw_hackathon_manual_sections
            WHERE (_airbyte_data->>'brand')='{brand}'
            AND (_airbyte_data->>'device')='{device}'
            AND (_airbyte_data->>'model_number')='{model_number}'
            AND (_airbyte_data->>'section_name')='{top_content_name}'
        """
        result = get_query_results(motherduck_conn, query)
    return result
