import pandas as pd
import psycopg2
from psycopg2 import sql
import sys
import os
import logging
from datetime import datetime

def setup_logging():
    """Set up logging to file and console"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('linksData_import.log', mode='a'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger()

def import_links_data(csv_file_path, schema_name, db_params, logger):
    """Import data from CSV to PostgreSQL"""
    try:
        # Verify CSV file exists
        if not os.path.isfile(csv_file_path):
            logger.error(f"CSV file not found: {csv_file_path}")
            return False
            
        # Read CSV file
        logger.info(f"Reading data from {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        
        # Connect to PostgreSQL
        logger.info("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(
            host=db_params['host'],
            port=db_params['port'],
            database=db_params['database'],
            user=db_params['user'],
            password=db_params['password']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if table exists and drop if it does
        table_name = "linksdata"
        full_table_name = sql.Identifier(schema_name, table_name)
        
        logger.info(f"Checking if table {schema_name}.{table_name} exists...")
        cursor.execute(
            sql.SQL("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = %s AND table_name = %s)"),
            [schema_name, table_name]
        )
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            logger.info(f"Table {schema_name}.{table_name} exists - dropping it")
            cursor.execute(
                sql.SQL("DROP TABLE IF EXISTS {}").format(full_table_name)
            )
        
        # Create new table
        logger.info(f"Creating table {schema_name}.{table_name}")
        create_table_query = sql.SQL("""
            CREATE TABLE {} (
                activity VARCHAR(255),
                type VARCHAR(255),
                pgmid VARCHAR(255)
            )
        """).format(full_table_name)
        cursor.execute(create_table_query)
        
        # Insert data
        logger.info(f"Inserting {len(df)} records into {schema_name}.{table_name}")
        for _, row in df.iterrows():
            cursor.execute(
                sql.SQL("INSERT INTO {} (activity, type, pgmid) VALUES (%s, %s, %s)").format(full_table_name),
                (row['ACTIVITY'], row['TYPE'], row['PGMID'])
            )
        
        logger.info("Data import completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during data import: {str(e)}", exc_info=True)
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python import_links_data.py <csv_file_path> <schema_name> <host> <port> <username> <password>")
        print("Example: python import_links_data.py /path/to/linksdata.csv public localhost 5432 postgres mypassword")
        sys.exit(1)
    
    logger = setup_logging()
    
    # Get all parameters from command line
    csv_file_path = sys.argv[1]
    schema_name = sys.argv[2]
    
    db_params = {
        'host': sys.argv[3],
        'port': sys.argv[4],
        'database': 'postgres',  # Default database, can be parameterized if needed
        'user': sys.argv[5],
        'password': sys.argv[6]
    }
    
    success = import_links_data(csv_file_path, schema_name, db_params, logger)
    sys.exit(0 if success else 1)