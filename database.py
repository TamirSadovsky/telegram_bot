import pymssql
import logging
import os

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def query_database(query, params=None):
    """Execute a query using pymssql and return results"""
    try:
        logging.info(f"🔍 Running query: {query} with params: {params}")
        with pymssql.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params if params else ())
            results = cursor.fetchall()
            logging.info(f"✅ Query executed successfully! {len(results)} rows returned.")
            return results
    except Exception as e:
        logging.error(f"❌ Database error: {e}")
        return None
