import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

st.set_page_config(
    page_title="Model Training Dashboard",
    page_icon="🎯",
    layout="wide"
)

with open('utils/auth_config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
    
# Generate hashed passwords
stauth.Hasher.hash_passwords(config['credentials'])

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 40px;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 30px;
    }
    .sub-header {
        font-size: 25px;
        font-weight: semi-bold;
        color: #424242;
    }
    .welcome-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #2C3E50;  /* Dark blue-gray */
        margin-bottom: 20px;
        border: 2px solid #34495E;
    }
    .welcome-text {
        color: #ECF0F1;  /* Almost white */
        font-size: 24px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Main header with custom styling

try:
     # Login page styling
    st.markdown("""
        <div style='text-align: center; padding: 30px;'>
            <h2>Welcome to Model Training Dashboard</h2>
        </div>
    """, unsafe_allow_html=True)
    authenticator.login("sidebar")
except Exception as e:
    st.error(e)

if st.session_state['authentication_status']:
    authenticator.logout(location="sidebar")
    
    # Welcome message in a container
    with st.container():
        st.markdown(f"""
        <div class="welcome-box">
            <h2 class="welcome-text">👋 Welcome, {st.session_state["name"]}!</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Dashboard overview in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p class="sub-header">📊 Dashboard Overview</p>', unsafe_allow_html=True)
        st.write("""
        Welcome to your centralized Model Training Dashboard. This platform provides 
        comprehensive insights into training data from various sources.
        """)
        
    with col2:
        st.markdown('<p class="sub-header">🚀 Quick Actions</p>', unsafe_allow_html=True)
        st.page_link(label="Explore Training Data", page="pages/2_Dashboard.py")
        st.page_link(label="Validate Training Data", page="pages/1_Validator.py")
    
    # Feature highlights
    st.markdown('<p class="sub-header">✨ Key Features</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📈 Data Analytics")
        st.write("Explore and analyze your training data with interactive visualizations")
        
    with col2:
        st.markdown("### 🔍 Model Monitoring")
        st.write("Track and monitor your model's performance in real-time")
        st.markdown("🔜 **Coming Soon!**", help="This feature is under development")
        
    with col3:
        st.markdown("### 📊 Reports")
        st.write("Generate comprehensive reports and insights")
        st.markdown("🔜 **Coming Soon!**", help="This feature is under development")

elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
    
elif st.session_state['authentication_status'] is None:
    # Login instructions that only appear before login
    
    st.info('👈 Please login using the sidebar to continue', icon="ℹ️")