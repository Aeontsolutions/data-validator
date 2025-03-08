import streamlit as st
import os
from PIL import Image
from io import BytesIO
import json
from utils.scraper_utils import search_properties, capture_screenshots_async
import asyncio
from zipfile import ZipFile
import tempfile

def main():
    # Add a button in the sidebar to reset session state
    if st.sidebar.button("Reset Session State"):
        st.session_state.pop("properties")
        st.session_state.pop("selected_links")
        st.rerun()  # Rerun the app to reflect changes

    # Add authentication check at the start
    if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
        st.error('Please login to continue')
        st.stop()
    
    st.title("Webpage Screenshot Capture Tool")

    # Set up credentials from Streamlit secrets
    if not os.path.exists("credentials.json"):
        with open("credentials.json", "w") as f:
            json.dump(json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]), f)

    # Set the environment variable to point to the credentials file
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("credentials.json")

    # Input method selection
    location = st.text_input("Enter location:")
    if st.button("Search Properties"):
        try:
            properties = search_properties(location, st.secrets.get("GOOGLE_SEARCH_API_KEY"), st.secrets.get("GOOGLE_CUSTOM_SEARCH_ENGINE_ID"))
            if properties:
                # Store the entire list of properties in session state
                st.session_state.properties = [{"Title": prop['title'], "Link": prop['link'], "Select": False} for prop in properties]
            else:
                st.warning("No properties found.")
        except Exception as e:
            st.error(f"Error searching properties: {str(e)}")

    # Check if properties are stored in session state
    if 'properties' in st.session_state:
        st.subheader("Search Results")
        
        # Initialize session state for selected links if not already done
        if 'selected_links' not in st.session_state:
            st.session_state.selected_links = []

        # Display the search results with clickable links
        for i, prop in enumerate(st.session_state.properties):
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.markdown(f"**[{prop['Title']}]({prop['Link']})**", unsafe_allow_html=True)
            with col2:
                # Use session state to manage checkbox state
                selected = st.checkbox(
                    "Select", 
                    key=f"select_{i}", 
                    value=prop['Link'] in st.session_state.selected_links
                )
                if selected:
                    if prop['Link'] not in st.session_state.selected_links:
                        st.session_state.selected_links.append(prop['Link'])
                else:
                    if prop['Link'] in st.session_state.selected_links:
                        st.session_state.selected_links.remove(prop['Link'])

        if st.session_state.selected_links:
            st.subheader("Selected Links")
            for link in st.session_state.selected_links:
                st.write(f"Selected Link: {link}")
                
            if st.button("Capture Screenshots"):
                if st.session_state.selected_links:
                    
                    if "screenshot_results" not in st.session_state:
                        st.session_state.screenshot_results = []
                        
                    try:
                        with st.spinner("Capturing screenshots and processing AI responses..."):
                            screenshots = asyncio.run(capture_screenshots_async(st.session_state.selected_links, location))
                            
                            # Use a temporary file for the ZIP
                            with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
                                zip_filename = tmp_zip.name

                            with ZipFile(zip_filename, 'w') as zipf:
                                # Display results
                                for result in screenshots:
                                    st.subheader(f"📸 Screenshot for: {result['url']}")
                                    
                                    if "error" in result:
                                        st.error(f"❌ Error: {result['error']}")
                                    else:
                                        # Show Screenshot
                                        image = Image.open(BytesIO(result["screenshot"]))
                                        st.image(image, caption=f"Captured Screenshot - {result['url']}", use_container_width=True)

                                        # Show AI-Generated Data
                                        st.subheader("🧠 AI-Generated Data")
                                        if "error" in result["ai_response"]:
                                            st.error(f"AI Error: {result['ai_response']['error']}")
                                        else:
                                            st.json(result["ai_response"])  # Display JSON response
                                            
                                            # Add to session state
                                            st.session_state.screenshot_results.append(result)
                                            
                                            # Add files to the ZIP
                                            if os.path.exists(result["screenshot_path"]):
                                                zipf.write(result["screenshot_path"], os.path.basename(result["screenshot_path"]))
                                            if os.path.exists(result["ai_json_path"]):
                                                zipf.write(result["ai_json_path"], os.path.basename(result["ai_json_path"]))

                            with open(zip_filename, "rb") as file:
                                st.download_button(
                                    label="⬇️ Download All",
                                    data=file,
                                    file_name=f"{location.replace(' ', '_')}.zip",
                                    mime="application/zip"
                                )

                    except Exception as e:
                        st.error(f"Error capturing screenshots: {str(e)}")
                else:
                    st.warning("No links selected for capture.")

if __name__ == "__main__":
    main()
    