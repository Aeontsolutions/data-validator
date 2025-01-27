import streamlit as st
import os
from google.cloud import bigquery
from google.oauth2 import service_account
from utils.bigquery_utils import summary_query, fetch_data_all, create_bigquery_client
from dotenv import load_dotenv
import pandas as pd
import pydeck as pdk

# Page configuration
st.set_page_config(
    page_title="Location Dashboard",
    page_icon="🌍",
    layout="wide"
)

if 'authentication_status' not in st.session_state:
    st.error('Please login to continue')
    st.stop()

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric label {
        color: #0f1216;
    }
    .stMetric .metric-value {
        color: #0f1216 !important;
        font-weight: 600 !important;
    }
    .stMetric .metric-delta {
        color: #2c3e50 !important;
        font-weight: 500 !important;
    }
    .st-emotion-cache-1wivap2 {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetricValue"] > div {
        color: #0f1216 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricDelta"] > div {
        color: #2c3e50 !important;
        font-weight: 500 !important;
    }
    </style>
""", unsafe_allow_html=True)

load_dotenv()

# Initialize BigQuery client with project ID
client = create_bigquery_client()

# Header
st.title("📍 Location Intelligence Dashboard")
st.markdown("---")

# Summary Dashboard in columns
col1, col2, col3 = st.columns(3)
summary = summary_query(client)

with col1:
    st.metric(
        "📊 Total Rows",
        f"{summary['total_rows'].iloc[0]:,}",
        delta=None,
        help="Total number of records in the database"
    )

with col2:
    validated_pct = (summary['validated_rows'].iloc[0] / summary['total_rows'].iloc[0]) * 100
    st.metric(
        "✅ Validated Rows",
        f"{summary['validated_rows'].iloc[0]:,}",
        f"{validated_pct:.1f}%",
        help="Number of validated records"
    )

with col3:
    unvalidated_pct = (summary['unvalidated_rows'].iloc[0] / summary['total_rows'].iloc[0]) * 100
    st.metric(
        "⏳ Unvalidated Rows",
        f"{summary['unvalidated_rows'].iloc[0]:,}",
        f"{unvalidated_pct:.1f}%",
        help="Number of records pending validation"
    )

# Map section
st.markdown("---")
st.subheader("📍 Location Distribution")
st.markdown("Interactive map showing the geographical distribution of all points")

# Create map with expanded height
df = fetch_data_all(client)

# Add filters in columns
st.markdown("### 🔍 Filters")
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    # Property type filter
    property_types = ['All'] + sorted(df['property_type'].unique().tolist())
    selected_type = st.selectbox('Property Type', property_types)

with filter_col2:
    # Price range filter
    min_price = int(df['price'].min())
    max_price = int(df['price'].max())
    price_range = st.slider(
        'Price Range',
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price)
    )
    st.write(f"${price_range[0]:,} - ${price_range[1]:,}")

with filter_col3:
    # Rooms filter
    min_rooms = int(df['rooms'].min())
    max_rooms = int(df['rooms'].max())
    rooms_range = st.slider(
        'Number of Rooms',
        min_value=min_rooms,
        max_value=max_rooms,
        value=(min_rooms, max_rooms)
    )

# Apply filters
filtered_df = df.copy()
if selected_type != 'All':
    filtered_df = filtered_df[filtered_df['property_type'] == selected_type]
filtered_df = filtered_df[
    (filtered_df['price'] >= price_range[0]) &
    (filtered_df['price'] <= price_range[1]) &
    (filtered_df['rooms'] >= rooms_range[0]) &
    (filtered_df['rooms'] <= rooms_range[1])
]

# Show number of filtered results
st.markdown(f"### Showing {len(filtered_df):,} properties")

# Calculate the center point for the map view
center_lat = filtered_df['latitude'].mean()
center_lon = filtered_df['longitude'].mean()

# Create tooltip text
filtered_df['tooltip'] = filtered_df.apply(lambda row: f"Type: {row['property_type']}<br>"
                                                     f"Price: ${row['price']:,.2f}<br>"
                                                     f"Rooms: {row['rooms']}<br>"
                                                     f"Bathrooms: {row['bathroom']}<br>"
                                                     f"Sqft: {row['sqft']:,.0f}", axis=1)

# Configure the map view
view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=11,
    pitch=0
)

# Create the scatter plot layer
layer = pdk.Layer(
    'ScatterplotLayer',
    data=filtered_df,
    get_position='[longitude, latitude]',
    get_color='[200, 30, 0, 160]',
    get_radius=100,
    pickable=True,
    opacity=0.8,
    stroked=True,
    filled=True,
    radius_scale=6,
    radius_min_pixels=5,
    radius_max_pixels=15,
)

# Create the deck
deck = pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=view_state,
    layers=[layer],
    tooltip={"html": "{tooltip}"}
)

# Display the map
st.pydeck_chart(deck)

# Add footer with timestamp
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: #666;'>Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)