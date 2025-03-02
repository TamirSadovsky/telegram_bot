import pyodbc
import logging
from config import DB_CONNECTION_STRING

def query_database(query, params=None):
    """Execute a query and return results"""
    try:
        logging.info(f"🔍 Running query: {query} with params: {params}")
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params if params else ())
            results = cursor.fetchall()
            logging.info(f"✅ Query executed successfully! {len(results)} rows returned.")
            return results
    except Exception as e:
        logging.error(f"❌ Database error: {e}")
        return None

# Checks the connection of the bot to the SQL server
try:
    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        logging.info("✅ SQL Server is ONLINE and connected successfully!")
except Exception as e:
    logging.error(f"❌ Failed to connect to SQL Server: {e}")
