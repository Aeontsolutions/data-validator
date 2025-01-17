import streamlit as st
import os
from google.cloud import bigquery
from datetime import datetime
import pytz
from dotenv import load_dotenv
from google.oauth2 import service_account

load_dotenv()

def create_bigquery_client():
    # Get the path to the credentials file from environment variables
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Load credentials from the JSON file
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    
    # Create and return the client
    return bigquery.Client(credentials=credentials, project=os.getenv('PROJECT_ID'))

# Fetch rows to validate
def fetch_data(client):
    query = f"""
        SELECT * FROM `{os.getenv('PROJECT_ID')}.{os.getenv('DATASET_ID')}.{os.getenv('TABLE_ID')}`
        WHERE is_validated = FALSE
        LIMIT 100
    """
    return client.query(query).to_dataframe(create_bqstorage_client=True)

# Update validation status
def update_validation(client, row_ids, user):
    if not row_ids:
        return
    
    # Get Jamaica timezone
    jamaica_tz = pytz.timezone('America/Jamaica')
    current_time = datetime.now(jamaica_tz)
    
    # Format row_ids as quoted strings for SQL
    formatted_ids = [f"'{str(r)}'" for r in row_ids]
    
    query = f"""
        UPDATE `{os.getenv('PROJECT_ID')}.{os.getenv('DATASET_ID')}.{os.getenv('TABLE_ID')}`
        SET is_validated = TRUE,
            validated_by = '{user}',
            validation_timestamp = '{current_time}'
        WHERE property_id IN ({','.join(formatted_ids)})
    """
    client.query(query).result()
    
# Summary query

def summary_query(client):
    query = f"""
        SELECT 
            COUNT(*) AS total_rows,
        SUM(CASE WHEN is_validated THEN 1 ELSE 0 END) AS validated_rows,
            SUM(CASE WHEN NOT is_validated THEN 1 ELSE 0 END) AS unvalidated_rows
        FROM `{os.getenv('PROJECT_ID')}.{os.getenv('DATASET_ID')}.{os.getenv('TABLE_ID')}`
    """
    return client.query(query).to_dataframe()
