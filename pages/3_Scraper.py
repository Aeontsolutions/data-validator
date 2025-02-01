import streamlit as st
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from io import BytesIO
import json
from utils.scraper_utils import capture_webpage_screenshot, image_to_base64, generate
from utils.bigquery_utils import create_bigquery_client, add_property_row

def main():
    st.title("Webpage Screenshot Capture Tool")
    
    # Set up Chrome options for Linux environment
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.binary_location = "/usr/bin/chromium-browser"  # Use Chromium instead of Chrome

    # Initialize Chrome driver without webdriver_manager
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        st.error(f"Error initializing Chrome driver: {str(e)}")
        return

    # Set up credentials from Streamlit secrets
    if not os.path.exists("credentials.json"):
        with open("credentials.json", "w") as f:
            json.dump(json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]), f)

    # Set the environment variable to point to the credentials file
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("credentials.json")

    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Single URL", "Multiple URLs"]
    )
    
    if input_method == "Single URL":
        # Single URL input
        url = st.text_input("Enter webpage URL:")
        wait_time = st.slider("Page load wait time (seconds)", 5, 30, 10)
        
        if st.button("Capture Screenshot"):
            if url:
                try:
                    with st.spinner("Capturing screenshot..."):
                        screenshot = capture_webpage_screenshot(url, wait_time=wait_time)
                        image = Image.open(BytesIO(screenshot))
                        
                        temp_path = os.path.join(os.getcwd(), "screenshots", "temp.png")
                        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                        image.save(temp_path, format="PNG")
                        
                        base64_image = image_to_base64(temp_path)
                        raw_response = generate(base64_image)
                        
                        # Parse the nested JSON string
                        json_data = json.loads(raw_response["response"])
                        
                        # Debug print to see the structure
                        st.write("Debug - JSON Response:", json_data)
                        
                        # Create two columns for side-by-side display
                        col1, col2 = st.columns(2)
                        
                        # Display image in left column
                        with col1:
                            st.image(image, caption="Captured Screenshot", use_container_width=True)
                        
                        # Display editable fields in right column
                        with col2:
                            st.subheader("Edit Property Data")
                            edited_data = {}
                            
                            # Try to get AI-generated data
                            try:
                                base64_image = image_to_base64(temp_path)
                                raw_response = generate(base64_image)
                                json_data = json.loads(raw_response["response"])
                                st.info("AI data generated successfully")
                            except Exception as e:
                                st.error(f"AI data generation failed: {str(e)}")
                                json_data = {
                                    'property description': '',
                                    'property address': '',
                                    'price': '',
                                    'currency of price': '',
                                    'number of bedrooms': '',
                                    'number of bathrooms': '',
                                    'square feet': ''
                                }
                            
                            edited_data['property_description'] = st.text_area(
                                "Property Description",
                                value=json_data.get('property description', ''),
                                height=100
                            )
                            
                            edited_data['property_address'] = st.text_input(
                                "Property Address",
                                value=json_data.get('property address', '')
                            )
                            
                            edited_data['price'] = st.text_input(
                                "Price",
                                value=json_data.get('price', '')
                            )
                            
                            edited_data['currency_of_price'] = st.text_input(
                                "Currency",
                                value=json_data.get('currency of price', '')
                            )
                            
                            edited_data['bedrooms'] = st.text_input(
                                "Number of Bedrooms",
                                value=json_data.get('number of bedrooms', '')
                            )
                            
                            edited_data['bathrooms'] = st.text_input(
                                "Number of Bathrooms",
                                value=json_data.get('number of bathrooms', '')
                            )
                            
                            edited_data['square_feet'] = st.text_input(
                                "Square Feet",
                                value=json_data.get('square feet', '')
                            )
                            
                            # Add submit button
                            if st.button("Save Property Data"):
                                client = create_bigquery_client()
                                if add_property_row(client, edited_data, url):
                                    st.success("Property data saved successfully!")
                                else:
                                    st.error("Failed to save property data")
                        
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a URL")
    
    else:
        # Multiple URLs input
        urls = st.text_area("Enter URLs (one per line):")
        wait_time = st.slider("Page load wait time (seconds)", 5, 30, 10)
        output_folder = os.path.join(os.getcwd(), "screenshots")
        
        if st.button("Capture Screenshots"):
            if urls and urls.strip():
                try:
                    # Clean and filter URLs
                    url_list = [url.strip() for url in urls.split('\n') if url.strip() and url.startswith(('http://', 'https://'))]
                    
                    if not url_list:
                        st.warning("Please enter valid URLs (must start with http:// or https://)")
                        return
                    
                    # Create output directory if it doesn't exist
                    if not os.path.exists(output_folder):
                        os.makedirs(output_folder)
                    
                    with st.spinner(f"Capturing screenshots for {len(url_list)} URLs..."):
                        output_paths = []
                        json_data_list = []
                        try:
                            for i, url in enumerate(url_list):
                                try:
                                    driver.get(url)
                                    driver.implicitly_wait(wait_time)
                                    
                                    safe_filename = f"screenshot_{i+1}.png"
                                    output_path = os.path.join(output_folder, safe_filename)
                                    
                                    screenshot = driver.get_screenshot_as_png()
                                    with open(output_path, 'wb') as f:
                                        f.write(screenshot)
                                    output_paths.append(output_path)
                                    
                                    # Add debug prints
                                    st.write(f"Debug - Processing URL {i+1}: {url}")
                                    
                                    base64_image = image_to_base64(output_path)
                                    raw_response = generate(base64_image)
                                    
                                    # Debug print raw response
                                    st.write(f"Debug - Raw Response {i+1}:", raw_response)
                                    
                                    if raw_response and isinstance(raw_response, dict) and "response" in raw_response:
                                        try:
                                            json_data = json.loads(raw_response["response"])
                                            json_data_list.append(json_data)
                                            
                                            # Create two columns for side-by-side display
                                            col1, col2 = st.columns(2)
                                            
                                            # Display image in left column
                                            with col1:
                                                image = Image.open(output_path)
                                                st.image(image, caption=f"Screenshot {i+1}: {url}", use_container_width=True)
                                            
                                            # Display editable fields in right column
                                            with col2:
                                                st.subheader(f"Edit Property Data {i+1}")
                                                edited_data = {}
                                                
                                                # Try to get AI-generated data
                                                try:
                                                    base64_image = image_to_base64(output_path)
                                                    raw_response = generate(base64_image)
                                                    json_data = json.loads(raw_response["response"])
                                                    st.info("AI data generated successfully")
                                                except Exception as e:
                                                    st.error(f"AI data generation failed: {str(e)}")
                                                    json_data = {
                                                        'property description': '',
                                                        'property address': '',
                                                        'price': '',
                                                        'currency of price': '',
                                                        'number of bedrooms': '',
                                                        'number of bathrooms': '',
                                                        'square feet': ''
                                                    }
                                                
                                                edited_data['property_description'] = st.text_area(
                                                    "Property Description",
                                                    value=json_data.get('property description', ''),
                                                    height=100,
                                                    key=f"desc_{i}"
                                                )
                                                
                                                edited_data['property_address'] = st.text_input(
                                                    "Property Address",
                                                    value=json_data.get('property address', ''),
                                                    key=f"addr_{i}"
                                                )
                                                
                                                edited_data['price'] = st.text_input(
                                                    "Price",
                                                    value=json_data.get('price', ''),
                                                    key=f"price_{i}"
                                                )
                                                
                                                edited_data['currency_of_price'] = st.text_input(
                                                    "Currency",
                                                    value=json_data.get('currency of price', ''),
                                                    key=f"curr_{i}"
                                                )
                                                
                                                edited_data['bedrooms'] = st.text_input(
                                                    "Number of Bedrooms",
                                                    value=json_data.get('number of bedrooms', ''),
                                                    key=f"bed_{i}"
                                                )
                                                
                                                edited_data['bathrooms'] = st.text_input(
                                                    "Number of Bathrooms",
                                                    value=json_data.get('number of bathrooms', ''),
                                                    key=f"bath_{i}"
                                                )
                                                
                                                edited_data['square_feet'] = st.text_input(
                                                    "Square Feet",
                                                    value=json_data.get('square feet', ''),
                                                    key=f"sqft_{i}"
                                                )
                                                
                                                # Add submit button for each property
                                                if st.button("Save Property Data", key=f"save_{i}"):
                                                    client = create_bigquery_client()
                                                    if add_property_row(client, edited_data, url):
                                                        st.success("Property data saved successfully!")
                                                    else:
                                                        st.error("Failed to save property data")
                                        except json.JSONDecodeError as je:
                                            st.error(f"Error parsing JSON for URL {url}: {str(je)}")
                                            st.write("Raw response that caused error:", raw_response)
                                    else:
                                        st.error(f"Invalid response format for URL {url}")
                                        st.write("Raw response:", raw_response)
                                    
                                except Exception as e:
                                    st.error(f"Error capturing screenshot for URL {url}: {str(e)}")
                                    continue
                        finally:
                            driver.quit()
                                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter at least one URL")

if __name__ == "__main__":
    main()