import streamlit as st
import os
from PIL import Image
from io import BytesIO
import json
import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting
from dotenv import load_dotenv
from google.oauth2 import service_account
from typing import List, Dict
import requests
import asyncio
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

# Set up credentials from Streamlit secrets
if not os.path.exists("credentials.json"):
    with open("credentials.json", "w") as f:
        json.dump(json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]), f)

# Set the environment variable to point to the credentials file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("credentials.json")

# Detect whether running locally or on Streamlit Cloud
def is_running_on_streamlit_cloud():
    return "STREAMLIT_SERVER_PORT" in os.environ

def setup_webdriver():
    """
    Initializes and returns a Selenium WebDriver instance with the correct configuration.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance.
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('--remote-debugging-port=9222')

    if is_running_on_streamlit_cloud():
        # Streamlit Cloud uses Chromium at this location
        chrome_options.binary_location = "/usr/bin/chromium"
        service = Service("/usr/bin/chromedriver")
    else:
        # Use locally installed Chrome
        chrome_options.binary_location = st.secrets.get("CHROME_BINARY_LOCATION")
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def capture_webpage_screenshot(driver, url, wait_time=10):
    """
    Captures a screenshot of a webpage using Selenium and Chrome.

    Args:
        driver (webdriver.Chrome): The Chrome driver instance
        url (str): The URL of the webpage to capture
        wait_time (int, optional): Time to wait for the page to load in seconds. Defaults to 10 seconds.

    Returns:
        dict: A dictionary containing the screenshot (bytes) and the URL.
    """
    try:
        driver.set_window_size(1920, 1080)
        driver.get(url)
        driver.implicitly_wait(wait_time)

        # Get full page size for scrolling pages
        page_width = driver.execute_script('return document.body.scrollWidth')
        page_height = driver.execute_script('return document.body.scrollHeight')
        driver.set_window_size(page_width, page_height)

        screenshot = driver.get_screenshot_as_png()

        return {"url": url, "screenshot": screenshot}
    
    except Exception as e:
        return {"url": url, "error": str(e)}
    
async def capture_screenshots_async(urls):
    """
    Asynchronously capture screenshots and apply AI processing.

    Args:
        urls (list): List of URLs to capture.

    Returns:
        list: A list of dictionaries containing the URL, screenshot, and AI response.
    """
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        loop = asyncio.get_event_loop()
        driver = setup_webdriver()  # ✅ Initialize the WebDriver instance
        
        futures = [
            loop.run_in_executor(executor, capture_webpage_screenshot, driver, url)
            for url in urls
        ]

        for result in await asyncio.gather(*futures):
            if "error" in result:
                results.append(result)  # Store errors separately
                continue  # Skip processing if screenshot failed
            
            # ✅ Convert image to Base64
            encoded_image = image_to_base64(result["screenshot"])

            # ✅ Apply AI Processing
            try:
                ai_response = generate(encoded_image)  # Get AI-generated data
            except Exception as e:
                ai_response = {"error": f"AI processing failed: {str(e)}"}

            # ✅ Store everything in results
            results.append({
                "url": result["url"],
                "screenshot": result["screenshot"],
                "ai_response": ai_response
            })

        driver.quit()  # ✅ Close WebDriver after all processing

    return results
    
    # this function does the same as the function  capture_webpage_screenshot with the modification that it allows a list of urls

def capture_webpage_screenshot_multiple(driver, image_urls, output_folder, wait_time=10):
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
        capture_webpage_screenshot(driver, url, output_path, wait_time)
    print("process completed")
    return output_path

def image_to_base64(image_bytes):
    """
    Convert image bytes to a base64 string.

    Args:
        image_bytes (bytes): Image in byte format

    Returns:
        str: Base64 encoded string of the image
    """
    buffered = BytesIO(image_bytes)  # Wrap image bytes in a BytesIO object
    image = Image.open(buffered)

    # Convert image to Base64
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

text1 = """
return the data seen in this image in json format as follows:
{
property description: ,
property address: , 
price: ,
currency of price: , 
number of bedrooms: , 
number of bathrooms: , 
square feet: 
}
Absolutely no other text or comments should be included in the response.
"""

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

def search_properties(location: str, api_key: str, search_engine_id: str, num_results: int = 20) -> List[Dict]:
    """
    Query Google Custom Search API for property results based on the request.

    :param location: Location of the property.
    :param api_key: Google API key.
    :param search_engine_id: Google Custom Search Engine ID.
    :param num_results: Number of results to retrieve.
    :return: List of dictionaries containing the top num_results search results.
    """
    
    query = f"real estate for sale in {location} Jamaica -airbnb -rent -lot -land -commercial"
    url = "https://www.googleapis.com/customsearch/v1"
    results = []
    for start in range(1, num_results, 10):
        params = {
            "q": query,
            "key": api_key,
            "cx": search_engine_id,
            "num": 10,
            "start": start
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Google Search API error: {response.status_code}, {response.text}")
        items = response.json().get("items", [])
        results.extend([{"title": item.get("title"), "link": item.get("link"), "snippet": item.get("snippet")} for item in items])
    return results