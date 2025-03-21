import os
from workflows.logs.log import setup_logger
import json
import sqlalchemy
from sqlalchemy import text
import pandas as pd

logging = setup_logger()

def execute_query(engine, query):
    try:
        with engine.connect() as connection:
        # Modify table name as needed
            response = text(query)
            df = pd.read_sql(response, connection)
        return df
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        raise


def generate_query(type_query, **kwargs) :   

    queries = None

    try:
        with open(f'{os.getcwd()}/workflows/configs/query.json', 'r') as f:
            queries = json.load(f)
    except FileNotFoundError as e:
        logging.error(f"Json config file not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Error loading  JSON file: {e}")
        raise


    # Check if the query type exists
    if type_query not in queries:
        logging.warning(f"Query type '{type_query}' not supported")
        raise ValueError(f"Query type '{type_query}' not supported")

    query_template = queries[type_query]

    # Safely format the query with kwargs (no eval)
    try:
        return query_template.format(**kwargs)
    except KeyError as e:
        logging.error(f"Missing kwarg for query template: {e}")
        raise ValueError(f"Query template requires missing parameter: {e}")
    








