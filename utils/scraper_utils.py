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
import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting
from dotenv import load_dotenv
from google.oauth2 import service_account
import google.cloud.aiplatform as aiplatform

load_dotenv()

# Set up credentials from Streamlit secrets
if not os.path.exists("credentials.json"):
    with open("credentials.json", "w") as f:
        json.dump(json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]), f)

# Set the environment variable to point to the credentials file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("credentials.json")

def capture_webpage_screenshot(url, output_path=None, wait_time=10):
    """
    Captures a screenshot of a webpage using Selenium and Chrome.

    Args:
        url (str): The URL of the webpage to capture
        output_path (str, optional): Path where the screenshot should be saved.
                                   If None, returns the image as bytes.
        wait_time (int, optional): Time to wait for the page to load in seconds.
                                 Defaults to 10 seconds.

    Returns:
        bytes or str: If output_path is None, returns the screenshot as bytes.
                     If output_path is provided, saves the image and returns the path.

    Raises:
        Exception: If there's an error capturing the screenshot
    """
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--start-maximized')

        # Initialize the Chrome driver
        driver = webdriver.Chrome(options=chrome_options)

        # Set window size (adjust as needed)
        driver.set_window_size(1920, 1080)

        # Navigate to the URL
        driver.get(url)

        # Wait for the page to load
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_all_elements_located(('tag name', 'body'))
        )

        # Get page dimensions and update window size
        page_width = driver.execute_script('return document.body.scrollWidth')
        page_height = driver.execute_script('return document.body.scrollHeight')
        driver.set_window_size(page_width, page_height)

        # Capture the screenshot
        screenshot = driver.get_screenshot_as_png()

        # Close the browser
        driver.quit()

        if output_path:
            # Save the screenshot to file
            with open(output_path, 'wb') as f:
                f.write(screenshot)
            return output_path
        else:
            # Return the screenshot as bytes
            return screenshot

    except Exception as e:
        raise Exception(f"Error capturing screenshot: {str(e)}")
    
    # this function does the same as the function  capture_webpage_screenshot with the modification that it allows a list of urls

def capture_webpage_screenshot_multiple(image_urls, output_folder, wait_time=10):
    """
    Captures screenshots of multiple webpages using Selenium and Chrome.

    Args:
        image_urls (list): List of URLs of the webpages to capture
        output_folder (str): Folder where the screenshots should be saved
        wait_time (int, optional): Time to wait for the page to load in seconds.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_paths = []
    for i, url in enumerate(image_urls):
        output_path = os.path.join(output_folder, f"screenshot_{i+1}.png")
        output_paths.append(output_path)
        capture_webpage_screenshot(url, output_path, wait_time)
    print("process completed")
    return output_path

def image_to_base64(image_path):
    """
    Convert an image file to base64 string.

    Args:
        image_path (str): Path to the image file

    Returns:
        str: Base64 encoded string of the image
    """
    # Load the image from filepath
    image = Image.open(image_path)

    # Convert to base64
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    encoded_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return encoded_image

def generate(encoded_image):
    """
    Generate JSON data from an image using Vertex AI.
    
    Args:
        encoded_image (str): Base64 encoded image string
    
    Returns:
        dict: JSON response from the model
    """
    try:
        # Create credentials from the service account info
        credentials_dict = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"])
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict
        )
        
        # Initialize Vertex AI with explicit credentials
        vertexai.init(
            project=st.secrets.get("PROJECT_ID"),
            location="us-central1",
            credentials=credentials
        )
        
        model = GenerativeModel("gemini-1.5-pro-002")
        
        # Create the image part with proper MIME type
        image_part = Part.from_data(
            data=base64.b64decode(encoded_image),
            mime_type="image/png"
        )
        
        responses = model.generate_content(
            [image_part, text1],
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=True,
        )
        
        response_string = ""
        for response in responses:
            response_string = response_string + response.text
        
        return json.loads(response_string)
        
    except Exception as e:
        st.error(f"Error in generate function: {str(e)}")
        raise

text1 = """return the data seen in this image in json format as follows{property description: ,property address: , price: ,currency of price: , number of bedrooms: , number of bathrooms: , square feet: }"""

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
    "response_mime_type": "application/json",
    "response_schema": {"type":"OBJECT","properties":{"response":{"type":"STRING"}}},
}

safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
]