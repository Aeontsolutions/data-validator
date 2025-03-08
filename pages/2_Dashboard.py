import streamlit as st
import os
from google.cloud import bigquery
from google.oauth2 import service_account
from utils.bigquery_utils import summary_query, fetch_data_all, create_bigquery_client
from dotenv import load_dotenv
import pandas as pd
import pydeck as pdk
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="Location Dashboard",
    page_icon="🌍",
    layout="wide"
)

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
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
st.title("📍 Training Data Dashboard")
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
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

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

with filter_col4:
    # Square footage filter
    min_sqft = int(df['sqft'].min())
    max_sqft = int(df['sqft'].max())
    sqft_range = st.slider(
        'Square Footage',
        min_value=min_sqft,
        max_value=max_sqft,
        value=(min_sqft, max_sqft)
    )
    
# Filter out None values and then sort
communities = ['All'] + sorted([x for x in df['community'].unique() if x is not None])
selected_community = st.selectbox('Community', communities)

# Apply filters
filtered_df = df.copy()
if selected_type != 'All':
    filtered_df = filtered_df[filtered_df['property_type'] == selected_type]
if selected_community != 'All':
    filtered_df = filtered_df[filtered_df['community'] == selected_community]
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
    zoom=7,
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
st.pydeck_chart(deck, use_container_width=True)

# Data Distribution Analysis
st.markdown("---")
st.subheader("📊 Data Distribution Analysis")

# Create tabs for each predictor
tabs = st.tabs(["Communities", "Rooms", "Bathrooms", "Square Footage", "Property Type", "Correlations"])

# Communities Tab
with tabs[0]:
    st.markdown("### Community Analysis")
    # Replace CSV reading with a BigQuery query
    query = """
        SELECT * FROM `price-aggregator-f9e4b.aggregated_prices.communities`
    """
    communities_df = client.query(query).to_dataframe()
    communities_df.columns = communities_df.columns.str.lower()
    col1, col2 = st.columns(2)
    with col1:
        # table of communities in training data
        communities = filtered_df['community'].value_counts().reset_index()
        communities.columns = communities.columns.str.lower()
        st.dataframe(communities, use_container_width=True, hide_index=True)
        
        property_types_by_community = filtered_df.groupby(['community', 'property_type']).size().reset_index(name='count')
        st.dataframe(property_types_by_community.pivot(index='community', columns='property_type', values='count').fillna(0).reset_index(), use_container_width=True)
        
        # Find communities that are in the authoritative list but missing from training data
        # Normalize strings by converting to lowercase and stripping whitespace
        auth_communities = {str(x).lower().strip() for x in communities_df['community'].unique() if pd.notna(x)}
        training_communities = {str(x).lower().strip() for x in filtered_df['community'].unique() if pd.notna(x)}
        missing_from_training = auth_communities - training_communities
        
        st.markdown("### Communities missing from training data")
        st.markdown(f"Found {len(missing_from_training)} communities in the authoritative list that are not in the training data:")
        missing_df = pd.DataFrame(sorted(missing_from_training), columns=['Missing Communities'])
        st.dataframe(missing_df, use_container_width=True, hide_index=True)
        
    with col2:
        # column chart of communities   
        fig_communities = px.bar(
            communities,
            x='community',
            y='count',
            title='Community Distribution',
            template='plotly_white'
        )
        st.plotly_chart(fig_communities, use_container_width=True, key='communities_chart')
        
        # Bar chart of Number of property types by community
        property_types_by_community = filtered_df.groupby(['community', 'property_type']).size().reset_index(name='count')
        fig_property_types = px.bar(
            property_types_by_community,
            x='community',
            y='count',
            color='property_type',
            title='Number of Property Types by Community',
            template='plotly_white',
            barmode='stack'
        )
        st.plotly_chart(fig_property_types, use_container_width=True, key='property_types_chart')

# Rooms Tab
with tabs[1]:
    st.markdown("### Room Analysis")
    room_col1, room_col2 = st.columns(2)
    
    with room_col1:
        # Univariate distribution of rooms
        fig_rooms_hist = px.histogram(
            filtered_df,
            x='rooms',
            title='Distribution of Rooms',
            template='plotly_white'
        )
        fig_rooms_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_rooms_hist, use_container_width=True, key='rooms_hist')
        
    with room_col2:
        # Box plot of rooms
        fig_rooms_box = px.box(
            filtered_df,
            y='rooms',
            title='Box Plot of Rooms',
            template='plotly_white'
        )
        st.plotly_chart(fig_rooms_box, use_container_width=True, key='rooms_box')
    
    # Rooms vs Price
    st.markdown("### Rooms vs Price")
    room_price_col1, room_price_col2 = st.columns(2)
    
    with room_price_col1:
        # Scatter plot
        fig_rooms_price = px.scatter(
            filtered_df,
            x='rooms',
            y='price',
            title='Price vs Rooms',
            template='plotly_white',
            trendline="ols"
        )
        st.plotly_chart(fig_rooms_price, use_container_width=True, key='rooms_price_scatter')
    
    with room_price_col2:
        # Box plot of price by rooms
        fig_price_by_rooms = px.box(
            filtered_df,
            x='rooms',
            y='price',
            title='Price Distribution by Number of Rooms',
            template='plotly_white'
        )
        st.plotly_chart(fig_price_by_rooms, use_container_width=True, key='rooms_price_box')

# Bathrooms Tab
with tabs[2]:
    st.markdown("### Bathroom Analysis")
    bath_col1, bath_col2 = st.columns(2)
    
    with bath_col1:
        # Univariate distribution of bathrooms
        fig_bath_hist = px.histogram(
            filtered_df,
            x='bathroom',
            title='Distribution of Bathrooms',
            template='plotly_white'
        )
        fig_bath_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_bath_hist, use_container_width=True, key='bath_hist')
        
    with bath_col2:
        # Box plot of bathrooms
        fig_bath_box = px.box(
            filtered_df,
            y='bathroom',
            title='Box Plot of Bathrooms',
            template='plotly_white'
        )
        st.plotly_chart(fig_bath_box, use_container_width=True, key='bath_box')
    
    # Bathrooms vs Price
    st.markdown("### Bathrooms vs Price")
    bath_price_col1, bath_price_col2 = st.columns(2)
    
    with bath_price_col1:
        # Scatter plot
        fig_bath_price = px.scatter(
            filtered_df,
            x='bathroom',
            y='price',
            title='Price vs Bathrooms',
            template='plotly_white',
            trendline="ols"
        )
        st.plotly_chart(fig_bath_price, use_container_width=True, key='bath_price_scatter')
    
    with bath_price_col2:
        # Box plot of price by bathrooms
        fig_price_by_bath = px.box(
            filtered_df,
            x='bathroom',
            y='price',
            title='Price Distribution by Number of Bathrooms',
            template='plotly_white'
        )
        st.plotly_chart(fig_price_by_bath, use_container_width=True, key='bath_price_box')

# Square Footage Tab
with tabs[3]:
    st.markdown("### Square Footage Analysis")
    sqft_col1, sqft_col2 = st.columns(2)
    
    with sqft_col1:
        # Univariate distribution of sqft
        fig_sqft_hist = px.histogram(
            filtered_df,
            x='sqft',
            title='Distribution of Square Footage',
            template='plotly_white'
        )
        fig_sqft_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_sqft_hist, use_container_width=True, key='sqft_hist')
        
    with sqft_col2:
        # Box plot of sqft
        fig_sqft_box = px.box(
            filtered_df,
            y='sqft',
            title='Box Plot of Square Footage',
            template='plotly_white'
        )
        st.plotly_chart(fig_sqft_box, use_container_width=True, key='sqft_box')
    
    # Square Footage vs Price
    st.markdown("### Square Footage vs Price")
    sqft_price_col1, sqft_price_col2 = st.columns(2)
    
    with sqft_price_col1:
        # Scatter plot
        fig_sqft_price = px.scatter(
            filtered_df,
            x='sqft',
            y='price',
            title='Price vs Square Footage',
            template='plotly_white',
            trendline="ols"
        )
        st.plotly_chart(fig_sqft_price, use_container_width=True, key='sqft_price_scatter')
    
    with sqft_price_col2:
        # Box plot of price by property type
        fig_price_by_type = px.box(
            filtered_df,
            x='property_type',
            y='price',
            title='Price Distribution by Property Type',
            template='plotly_white'
        )
        fig_price_by_type.update_xaxes(tickangle=45)
        st.plotly_chart(fig_price_by_type, use_container_width=True, key='sqft_price_box')

# Property Type Tab
with tabs[4]:
    st.markdown("### Property Type Analysis")
    prop_col1, prop_col2 = st.columns(2)
    
    with prop_col1:
        # Count of properties by type
        fig_prop_count = px.bar(
            filtered_df['property_type'].value_counts().reset_index(),
            x='property_type',
            y='count',
            title='Distribution of Property Types',
            template='plotly_white',
            labels={'property_type': 'Property Type', 'count': 'Count'}
        )
        fig_prop_count.update_xaxes(tickangle=45)
        st.plotly_chart(fig_prop_count, use_container_width=True, key='prop_count')
        
    with prop_col2:
        # Percentage distribution
        fig_prop_pie = px.pie(
            filtered_df['property_type'].value_counts().reset_index(),
            values='count',
            names='property_type',
            title='Property Type Distribution (%)',
            template='plotly_white'
        )
        st.plotly_chart(fig_prop_pie, use_container_width=True, key="property_type_pie")
    
    # Property Type vs Price
    st.markdown("### Property Type vs Price")
    prop_price_col1, prop_price_col2 = st.columns(2)
    
    with prop_price_col1:
        # Box plot of price by property type
        fig_price_by_type = px.box(
            filtered_df,
            x='property_type',
            y='price',
            title='Price Distribution by Property Type',
            template='plotly_white'
        )
        fig_price_by_type.update_xaxes(tickangle=45)
        st.plotly_chart(fig_price_by_type, use_container_width=True, key='prop_price_box')
    
    with prop_price_col2:
        # Average price by property type
        avg_price_by_type = filtered_df.groupby('property_type')['price'].mean().reset_index()
        fig_avg_price = px.bar(
            avg_price_by_type,
            x='property_type',
            y='price',
            title='Average Price by Property Type',
            template='plotly_white',
            labels={'property_type': 'Property Type', 'price': 'Average Price'}
        )
        fig_avg_price.update_xaxes(tickangle=45)
        st.plotly_chart(fig_avg_price, use_container_width=True, key='prop_avg_price')
    
    # Additional property type relationships
    st.markdown("### Property Type Relationships")
    prop_rel_col1, prop_rel_col2 = st.columns(2)
    
    with prop_rel_col1:
        # Average square footage by property type
        avg_sqft_by_type = filtered_df.groupby('property_type')['sqft'].mean().reset_index()
        fig_avg_sqft = px.bar(
            avg_sqft_by_type,
            x='property_type',
            y='sqft',
            title='Average Square Footage by Property Type',
            template='plotly_white',
            labels={'property_type': 'Property Type', 'sqft': 'Average Square Footage'}
        )
        fig_avg_sqft.update_xaxes(tickangle=45)
        st.plotly_chart(fig_avg_sqft, use_container_width=True, key='prop_avg_sqft')
    
    with prop_rel_col2:
        # Average rooms by property type
        avg_rooms_by_type = filtered_df.groupby('property_type')['rooms'].mean().reset_index()
        fig_avg_rooms = px.bar(
            avg_rooms_by_type,
            x='property_type',
            y='rooms',
            title='Average Number of Rooms by Property Type',
            template='plotly_white',
            labels={'property_type': 'Property Type', 'rooms': 'Average Rooms'}
        )
        fig_avg_rooms.update_xaxes(tickangle=45)
        st.plotly_chart(fig_avg_rooms, use_container_width=True, key='prop_avg_rooms')

# Correlations Tab
with tabs[5]:
    st.markdown("### Feature Correlations")
    numeric_columns = ['price', 'rooms', 'bathroom', 'sqft']
    correlation_matrix = filtered_df[numeric_columns].corr()
    fig_corr = px.imshow(
        correlation_matrix,
        title='Correlation Heatmap',
        template='plotly_white',
        color_continuous_scale='RdBu',
        aspect='auto'
    )
    st.plotly_chart(fig_corr, use_container_width=True, key='correlation_heatmap')

# Function to insert a new row into the BigQuery table
def insert_community_row(client, community, parish, city, latitude, longitude):
    query = f"""
    INSERT INTO `price-aggregator-f9e4b.aggregated_prices.communities` (Community, Parish, City, Latitude, Longitude)
    VALUES ('{community}', '{parish}', '{city}', {latitude}, {longitude})
    """
    client.query(query).result()

# Add a form for inserting a new community in the sidebar within an expander
st.sidebar.markdown("### Add a New Community")
with st.sidebar.expander("Add Community", expanded=False):
    with st.form("add_community_form"):
        community = st.text_input("Community")
        parish = st.text_input("Parish")
        city = st.text_input("City")
        latitude = st.number_input("Latitude", format="%.6f")
        longitude = st.number_input("Longitude", format="%.6f")
        
        submitted = st.form_submit_button("Add Community")
        if submitted:
            if community and parish and city:
                insert_community_row(client, community, parish, city, latitude, longitude)
                st.sidebar.success("Community added successfully!")
            else:
                st.sidebar.error("Please fill in all fields.")

# Add a download button for the DataFrame in the sidebar
st.sidebar.markdown("### Download Data")
csv = df.to_csv(index=False)
st.sidebar.download_button(
    label="Download data as CSV",
    data=csv,
    file_name='data.csv',
    mime='text/csv'
)

# Footer
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: #666;'>Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)