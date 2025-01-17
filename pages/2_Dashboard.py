import streamlit as st
import os
from google.cloud import bigquery
from utils.bigquery_utils import summary_query
from dotenv import load_dotenv

load_dotenv()

# Initialize BigQuery client
client = bigquery.Client(credentials=os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))

# Summary Dashboard
summary = summary_query(client)
st.write("Summary Dashboard:")
st.metric("Total Rows", summary["total_rows"].iloc[0])
st.metric("Validated Rows", summary["validated_rows"].iloc[0])
st.metric("Unvalidated Rows", summary["unvalidated_rows"].iloc[0])