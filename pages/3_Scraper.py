import streamlit as st
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import json
import base64
from utils.scraper_utils import capture_webpage_screenshot, capture_webpage_screenshot_multiple, image_to_base64, generate

def main():
    st.title("Webpage Screenshot Capture Tool")
    
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
                        # Convert bytes to image for display
                        image = Image.open(BytesIO(screenshot))
                        
                        # Save temporarily to convert to base64
                        temp_path = os.path.join(os.getcwd(), "screenshots", "temp.png")
                        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                        image.save(temp_path, format="PNG")
                        
                        # Convert to base64
                        base64_image = image_to_base64(temp_path)
                        
                        # Display the image
                        st.image(image, caption="Captured Screenshot", use_container_width=True)
                        
                        # Generate JSON data
                        json_data = generate(base64_image)
                        st.write(json_data)
                        
                        # Clean up temporary file
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
                    
                    # Initialize Chrome options outside the loop
                    chrome_options = Options()
                    chrome_options.add_argument("--headless")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")
                    chrome_options.add_argument("--disable-gpu")
                    
                    with st.spinner(f"Capturing screenshots for {len(url_list)} URLs..."):
                        output_paths = []
                        json_data = []
                        driver = None
                        try:
                            driver = webdriver.Chrome(options=chrome_options)
                            
                            for i, url in enumerate(url_list):
                                try:
                                    # Navigate to URL and capture screenshot
                                    driver.get(url)
                                    driver.implicitly_wait(wait_time)
                                    
                                    # Create a safe filename
                                    safe_filename = f"screenshot_{i+1}.png"
                                    output_path = os.path.join(output_folder, safe_filename)
                                    
                                    # Capture and save screenshot
                                    screenshot = driver.get_screenshot_as_png()
                                    with open(output_path, 'wb') as f:
                                        f.write(screenshot)
                                    output_paths.append(output_path)
                                    
                                    # Convert to base64
                                    base64_image = image_to_base64(output_path)
                                    
                                    # Generate JSON data
                                    json_data.append(generate(base64_image))
                                    
                                    # Display screenshot
                                    image = Image.open(output_path)
                                    st.image(image, caption=f"Screenshot {i+1}: {url}", use_container_width=True)
                                    
                                    # Display JSON data
                                    st.write(json_data[i])
                                    
                                except Exception as e:
                                    st.error(f"Error capturing screenshot for URL {url}: {str(e)}")
                                    continue
                        finally:
                            if driver:
                                driver.quit()
                                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter at least one URL")

if __name__ == "__main__":
    main()