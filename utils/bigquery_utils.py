import streamlit as st
import json
import os
from google.cloud import bigquery
from datetime import datetime
import pytz
from dotenv import load_dotenv
from google.oauth2 import service_account

load_dotenv()

if not os.path.exists("credentials.json"):
    with open("credentials.json", "w") as f:
        json.dump(json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]), f)

def create_bigquery_client():
    # Try to get credentials from Streamlit secrets first, then fall back to .env
    try:
        credentials_json = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]
        # Write the credentials to a temporary file
        import json
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(json.loads(credentials_json), f)
            credentials_path = f.name
    except:
        # Fall back to .env file
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Get project ID from either source
    project_id = st.secrets.get("PROJECT_ID") or os.getenv('PROJECT_ID')
    
    # Load credentials from the JSON file
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    
    # Create and return the client
    return bigquery.Client(credentials=credentials, project=project_id)

def create_bigquery_table(client):
    """
    Creates a BigQuery table if it doesn't exist.
    
    Args:
        client (bigquery.Client): The BigQuery client instance.
    """
    dataset_id, table_id = st.secrets.get("DATASET_ID"), st.secrets.get("TABLE_ID")
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)

    schema = [
        bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("screenshot", "STRING", mode="NULLABLE"),  # Store Base64 screenshot (optional)
        bigquery.SchemaField("ai_response", "STRING", mode="NULLABLE"),  # Store AI JSON as a string
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    ]

    try:
        client.get_table(table_ref)  # Check if table exists
        st.info("✅ BigQuery table already exists.")
    except:
        table = bigquery.Table(table_ref, schema=schema)
        client.create_table(table)
        st.success("🚀 BigQuery table created successfully!")

# Fetch rows to validate
def fetch_data(client):
    # Get environment variables from either source
    project_id = st.secrets.get("PROJECT_ID") or os.getenv('PROJECT_ID')
    dataset_id = st.secrets.get("DATASET_ID") or os.getenv('DATASET_ID')
    table_id = st.secrets.get("TABLE_ID") or os.getenv('TABLE_ID')
    
    query = f"""
        SELECT * FROM `{project_id}.{dataset_id}.{table_id}`
        WHERE is_validated = FALSE
        LIMIT 100
    """
    return client.query(query).to_dataframe(create_bqstorage_client=True)

def fetch_data_all(client):
    # Get environment variables from either source
    project_id = st.secrets.get("PROJECT_ID") or os.getenv('PROJECT_ID')
    dataset_id = st.secrets.get("DATASET_ID") or os.getenv('DATASET_ID')
    table_id = st.secrets.get("TABLE_ID") or os.getenv('TABLE_ID')
    geo_table_id = st.secrets.get("GEO_TABLE_ID") or os.getenv('GEO_TABLE_ID')
    query = f"""
        SELECT * FROM `{project_id}.{dataset_id}.{table_id}`
        LEFT JOIN `{project_id}.{dataset_id}.{geo_table_id}` AS geo_coords USING (`property_id`)
    """
    return client.query(query).to_dataframe(create_bqstorage_client=True)

# Update validation status
def update_validation(client, row_ids, user):
    if not row_ids:
        return
    
    # Get environment variables from either source
    project_id = st.secrets.get("PROJECT_ID") or os.getenv('PROJECT_ID')
    dataset_id = st.secrets.get("DATASET_ID") or os.getenv('DATASET_ID')
    table_id = st.secrets.get("TABLE_ID") or os.getenv('TABLE_ID')
    
    # Get Jamaica timezone
    jamaica_tz = pytz.timezone('America/Jamaica')
    current_time = datetime.now(jamaica_tz)
    
    # Format row_ids as quoted strings for SQL
    formatted_ids = [f"'{str(r)}'" for r in row_ids]
    
    query = f"""
        UPDATE `{project_id}.{dataset_id}.{table_id}`
        SET is_validated = TRUE,
            validated_by = '{user}',
            validation_timestamp = '{current_time}'
        WHERE property_id IN ({','.join(formatted_ids)})
    """
    client.query(query).result()
    
# Summary query

def summary_query(client):
    # Get environment variables from either source
    project_id = st.secrets.get("PROJECT_ID") or os.getenv('PROJECT_ID')
    dataset_id = st.secrets.get("DATASET_ID") or os.getenv('DATASET_ID')
    table_id = st.secrets.get("TABLE_ID") or os.getenv('TABLE_ID')
    
    query = f"""
        SELECT 
            COUNT(*) AS total_rows,
            SUM(CASE WHEN is_validated THEN 1 ELSE 0 END) AS validated_rows,
            SUM(CASE WHEN NOT is_validated THEN 1 ELSE 0 END) AS unvalidated_rows
        FROM `{project_id}.{dataset_id}.{table_id}`
    """
    return client.query(query).to_dataframe()

def delete_property(client, property_id):
    """
    Delete a property from the BigQuery table
    """
    project_id = st.secrets.get("PROJECT_ID") or os.getenv('PROJECT_ID')
    dataset_id = st.secrets.get("DATASET_ID") or os.getenv('DATASET_ID')
    table_id = st.secrets.get("TABLE_ID") or os.getenv('TABLE_ID')
    
    query = f"""
    DELETE FROM `{project_id}.{dataset_id}.{table_id}`
    WHERE property_id = '{property_id}'
    """
    try:
        client.query(query)
        return True
    except Exception as e:
        print(f"Error deleting property: {str(e)}")
        return False

def add_property_row(client, property_data, url):
    """
    Add a new property row to the BigQuery table.
    
    Args:
        client: BigQuery client instance
        property_data (dict): Dictionary containing property information
        url (str): The URL of the property listing
    """
    # Get environment variables from either source
    project_id = st.secrets.get("PROJECT_ID") or os.getenv('PROJECT_ID')
    dataset_id = st.secrets.get("DATASET_ID") or os.getenv('DATASET_ID')
    table_id = st.secrets.get("TABLE_ID") or os.getenv('TABLE_ID')
    
    # Generate a unique property_id (you might want to adjust this logic)
    property_id = f"PROP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Convert string values to appropriate types
    try:
        sqft = float(property_data['square_feet']) if property_data['square_feet'] else None
        rooms = float(property_data['bedrooms']) if property_data['bedrooms'] else None
        bathroom = float(property_data['bathrooms']) if property_data['bathrooms'] else None
        price = float(property_data['price']) if property_data['price'] else None
    except ValueError as e:
        print(f"Error converting values: {str(e)}")
        return False
    
    query = f"""
        INSERT INTO `{project_id}.{dataset_id}.{table_id}`
        (property_id, listing_urls, sqft, rooms, bathroom, 
         property_type, price, is_validated)
        VALUES
        ('{property_id}',
         '{url}',
         {sqft if sqft is not None else 'NULL'},
         {rooms if rooms is not None else 'NULL'},
         {bathroom if bathroom is not None else 'NULL'},
         'apartment',
         {price if price is not None else 'NULL'},
         FALSE)
    """
    
    try:
        client.query(query).result()
        return True
    except Exception as e:
        print(f"Error adding property: {str(e)}")
        return False
    
def insert_into_bigquery(client, results):
    """
    Inserts AI-processed screenshot data into BigQuery.

    Args:
        client (bigquery.Client): The BigQuery client instance.
        results (list): A list of dictionaries containing the URL, screenshot, and AI response.
    """
    dataset_id, table_id = st.secrets.get("DATASET_ID"), st.secrets.get("TABLE_ID")
    table_ref = client.dataset(dataset_id).table(table_id)
    rows_to_insert = []

    for result in results:
        if "error" in result:
            continue  # Skip failed captures
        
        rows_to_insert.append({
            "url": result["url"],
            "screenshot": result["screenshot"],  # Store Base64 image (optional)
            "ai_response": json.dumps(result["ai_response"]),  # Convert AI response to JSON string
            "timestamp": datetime.utcnow().isoformat()
        })

    errors = client.insert_rows_json(table_ref, rows_to_insert)

    if errors:
        st.error(f"🚨 BigQuery Insert Errors: {errors}")
    else:
        st.success("✅ Successfully saved results to BigQuery!")
