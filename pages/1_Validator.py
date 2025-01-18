import streamlit as st
import os
import streamlit.components.v1 as components
from utils.bigquery_utils import fetch_data, update_validation, create_bigquery_client
import pandas as pd
import pydeck as pdk
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config for wider layout
st.set_page_config(layout="wide")

# Custom CSS for better styling
st.markdown("""
    <style>
    .stButton button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
    }
    .stButton button:hover {
        background-color: #FF6B6B;
    }
    .validator-header {
        margin-bottom: 2rem;
    }
    iframe {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Header section
st.markdown("<div class='validator-header'>", unsafe_allow_html=True)
st.title("Human-in-the-Loop Data Validation")
st.markdown("</div>", unsafe_allow_html=True)
user = st.text_input("Validator Name:", placeholder="Enter your name")

# Create BigQuery client
client = create_bigquery_client()

# Display rows
df = fetch_data(client)
if not df.empty:
    # Create three columns with custom ratios
    col1, col2 = st.columns([2, 3])  # Adjust ratio for better space usage
    
    with col1:
        st.markdown("### Properties to Validate")
        selected_property = st.selectbox(
            "Select property to validate:",
            df["property_id"],
            help="Choose a property to validate",
            index=None,
            placeholder="Choose a property..."
        )
        
        # Display individual inputs for the selected property
        if selected_property:
            st.markdown("### Property Details")
            selected_row = df[df['property_id'] == selected_property].iloc[0]
            
            # Create inputs for each column (except property_id)            
            price = st.number_input(
                "Price",
                value=float(selected_row['price']) if 'price' in selected_row else 0.0,
                key="price"
            )
            
            sqft = st.number_input(
                "Square Feet",
                value=float(selected_row['sqft']) if 'sqft' in selected_row else 0.0,
                key="sqft"
            )
            
            rooms = st.number_input(
                "Rooms",
                value=int(selected_row['rooms']) if 'rooms' in selected_row and not pd.isna(selected_row['rooms']) else 0,
                key="rooms"
            )
            
            bathroom = st.number_input(
                "Bathrooms",
                value=float(selected_row['bathroom']) if 'bathroom' in selected_row and not pd.isna(selected_row['bathroom']) else 0.0,
                key="bathroom"
            )
            
            property_type = st.text_input(
                "Property Type",
                value=selected_row['property_type'] if 'property_type' in selected_row else "",
                key="property_type"
            )
            
            latitude = st.number_input(
                "Latitude",
                value=float(selected_row['latitude']) if 'latitude' in selected_row else 0.0,
                format="%.6f",
                key="latitude"
            )
            
            longitude = st.number_input(
                "Longitude",
                value=float(selected_row['longitude']) if 'longitude' in selected_row else 0.0,
                format="%.6f",
                key="longitude"
            )
            
            aes_score = st.number_input(
                "Aes Score",
                value=float(selected_row['aes_score']) if 'aes_score' in selected_row else 0.0,
                key="aes_score"
            )
            
            if not pd.isna(selected_row['latitude']) and not pd.isna(selected_row['longitude']):
                st.markdown("### Property Location")
                map_data = pd.DataFrame({
                    'lat': [selected_row['latitude']],
                    'lon': [selected_row['longitude']],
                    'property': [f"{selected_row['property_id']} {selected_row['property_type']} {selected_row['rooms']} {selected_row['bathroom']} {selected_row['sqft']} {selected_row['aes_score']} - ${selected_row['price']:,.2f}"]
                })
                
                view_state = pdk.ViewState(
                    latitude=selected_row['latitude'],
                    longitude=selected_row['longitude'],
                    zoom=15,
                    pitch=0
                )

                # Create the deck
                deck = pdk.Deck(
                    map_style='mapbox://styles/mapbox/satellite-streets-v12',
                    initial_view_state=view_state,
                    api_keys={'mapbox': st.secrets["MAPBOX_TOKEN"] or os.getenv("MAPBOX_TOKEN")},
                    layers=[
                        pdk.Layer(
                            'ScatterplotLayer',
                            data=map_data,
                            get_position='[lon, lat]',
                            get_color='[255, 0, 0, 160]',
                            get_radius=50,
                            pickable=True,
                            auto_highlight=True,
                            get_tooltip='property'
                        )
                    ],
                    tooltip={"text": "{property}"}
                )

                st.pydeck_chart(deck)
        
        # Add some spacing
        st.markdown("<br>", unsafe_allow_html=True)
    
    with col2:
        # Property Viewer Section
        st.markdown("### Property Viewer")
        if selected_property:
            selected_url = df[df['property_id'] == selected_property]['listing_urls'].iloc[0]
            if selected_url:
                iframe_html = f'<iframe src="{selected_url}" width="100%" height="800" frameborder="0"></iframe>'
                st.components.v1.html(iframe_html, height=800)
        else:
            # Placeholder when no property is selected
            st.info("👈 Select a property from the list to view details")
    
    # Validation controls
        with st.container():
            st.markdown("### Validation Controls")
            
            # Only show validate button if property is selected and name is entered
            if selected_property and user:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Validate Property", type="primary"):
                        update_validation(client, [selected_property], user)
                        st.success("Property validated!")
                with col2:
                    if st.button("Skip Property", type="secondary"):
                        st.info("Property skipped")
        
        # Show validation stats
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Validation Progress")
    total = len(df)
    validated = len(df[df['validated'] == True]) if 'validated' in df.columns else 0
    st.progress(validated/total if total > 0 else 0)
    st.text(f"{validated}/{total} properties validated")

else:
    st.info("🎉 No properties left to validate!")
