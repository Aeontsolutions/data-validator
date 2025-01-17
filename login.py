import streamlit as st
import os
from authlib.integrations.requests_client import OAuth2Session
from dotenv import load_dotenv

load_dotenv()

if "google_user" not in st.session_state:
    st.session_state["google_user"] = None

def google_login():
    "Redirect to Google login page"
    oauth = OAuth2Session(
        client_id=os.getenv("GOOGLE_CLIENT_ID"), 
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"), 
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
        scope=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"]
    )
    authorization_url, state = oauth.create_authorization_url(os.getenv("GOOGLE_AUTHORIZATION_URI"))
    st.session_state["oauth_state"] = state
    st.markdown(f"[Login with Google]({authorization_url})")

def fetch_google_user():
    "Fetch user from Google"
    try:
        oauth = OAuth2Session(
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
        )
        
        current_url = f"{os.getenv('GOOGLE_REDIRECT_URI')}?{st.query_params.to_dict()}"
        
        token = oauth.fetch_token(
            os.getenv("GOOGLE_TOKEN_URI"),
            authorization_response=current_url,
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )
        
        user = oauth.get(os.getenv("GOOGLE_USER_INFO_URI")).json()
        st.session_state["google_user"] = user
        st.rerun()
        return user
        
    except Exception as e:
        st.error(f"Failed to fetch user info: {str(e)}")
        st.write("Debug info:")
        st.write(f"Query params: {st.query_params.to_dict()}")
        st.write(f"Session state: {st.session_state}")
        return None

# Main UI logic
if st.session_state["google_user"]:
    st.write("✅ Successfully logged in!")
    st.write(f"Welcome, {st.session_state['google_user'].get('name', 'User')}!")
    if "picture" in st.session_state["google_user"]:
        st.image(st.session_state["google_user"]["picture"])
else:
    if "code" in st.query_params:
        st.info("Processing login...")
        fetch_google_user()
    else:
        st.write("Please log in to continue:")
        google_login()
