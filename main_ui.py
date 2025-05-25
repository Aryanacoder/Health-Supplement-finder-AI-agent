import streamlit as st
import requests
import json
import time
import pandas as pd
import altair as alt
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

# Configure the Streamlit page with improved styling
st.set_page_config(
    page_title="💊 SupplementHub - Smart Price Finder",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for cart and user
if "cart_items" not in st.session_state:
    st.session_state.cart_items = []
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "total_savings" not in st.session_state:
    st.session_state.total_savings = 0.0

# Modern CSS with beautiful animations and professional design - Yellow & Blue Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles - Yellow & Blue Theme */
    .main {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #ffd700 0%, #1e90ff 100%);
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #fff8dc 0%, #e6f3ff 100%);
    }
    
    /* Header Styles */
    .main-header {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffd700 0%, #1e90ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
        animation: fadeInDown 1s ease-out;
        text-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        font-size: 1.4rem;
        color: #4682b4;
        text-align: center;
        margin-top: 0;
        font-weight: 400;
        animation: fadeInUp 1s ease-out;
    }
    
    /* Card Styles */
    .modern-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 20px 40px rgba(255, 215, 0, 0.2);
        border: 1px solid rgba(255, 215, 0, 0.3);
        margin: 20px 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: slideInUp 0.6s ease-out;
    }
    
    .modern-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 30px 60px rgba(30, 144, 255, 0.2);
    }
    
    .product-card {
        background: linear-gradient(145deg, #ffffff 0%, #fffacd 100%);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(255, 215, 0, 0.15);
        border: 1px solid rgba(255, 215, 0, 0.2);
        margin: 16px 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .product-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,215,0,0.3), transparent);
        transition: left 0.5s;
    }
    
    .product-card:hover::before {
        left: 100%;
    }
    
    .product-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 16px 48px rgba(30, 144, 255, 0.2);
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #ffd700 0%, #1e90ff 100%);
        color: white;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(255, 215, 0, 0.4);
        transition: all 0.3s ease;
        animation: bounceIn 0.8s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%);
        transform: scale(0);
        transition: transform 0.6s ease;
    }
    
    .metric-card:hover::before {
        transform: scale(1);
    }
    
    .metric-card:hover {
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 16px 48px rgba(30, 144, 255, 0.5);
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #ffd700 0%, #1e90ff 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(255, 215, 0, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(30, 144, 255, 0.5);
        background: linear-gradient(135deg, #1e90ff 0%, #ffd700 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Cart Button */
    .cart-button {
        background: linear-gradient(135deg, #32cd32 0%, #228b22 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(50, 205, 50, 0.3);
        cursor: pointer;
    }
    
    .cart-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(50, 205, 50, 0.4);
    }
    
    /* Search Container */
    .search-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 40px;
        margin: 30px 0;
        box-shadow: 0 20px 40px rgba(255, 215, 0, 0.2);
        border: 1px solid rgba(255, 215, 0, 0.3);
        animation: slideInUp 0.8s ease-out;
    }
    
    /* Form Styling */
    .stTextInput > div > div > input {
        border: 2px solid #ffd700;
        border-radius: 12px;
        padding: 16px;
        font-size: 16px;
        background: rgba(255, 255, 255, 0.9);
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.1);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #1e90ff;
        box-shadow: 0 0 0 3px rgba(30, 144, 255, 0.2);
        background: white;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #fffacd 0%, #e6f3ff 100%);
    }
    
    .sidebar-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 8px 24px rgba(255, 215, 0, 0.15);
        border: 1px solid rgba(255, 215, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .sidebar-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(30, 144, 255, 0.2);
    }
    
    /* Cart Item */
    .cart-item {
        background: linear-gradient(145deg, #fffacd 0%, #ffffff 100%);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #ffd700;
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.15);
        transition: all 0.3s ease;
        animation: slideInRight 0.5s ease-out;
    }
    
    .cart-item:hover {
        transform: translateX(4px);
        box-shadow: 0 6px 16px rgba(30, 144, 255, 0.2);
    }
    
    /* Status Messages */
    .success-message {
        background: linear-gradient(135deg, #32cd32 0%, #228b22 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        margin: 16px 0;
        box-shadow: 0 4px 16px rgba(50, 205, 50, 0.3);
        animation: slideInDown 0.5s ease-out;
    }
    
    .warning-message {
        background: linear-gradient(135deg, #ffa500 0%, #ff8c00 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        margin: 16px 0;
        box-shadow: 0 4px 16px rgba(255, 165, 0, 0.3);
        animation: slideInDown 0.5s ease-out;
    }
    
    .error-message {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        margin: 16px 0;
        box-shadow: 0 4px 16px rgba(220, 53, 69, 0.3);
        animation: slideInDown 0.5s ease-out;
    }
    
    /* Animations */
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInUp {
        from { opacity: 0; transform: translateY(50px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes bounceIn {
        0% { opacity: 0; transform: scale(0.3); }
        50% { opacity: 1; transform: scale(1.05); }
        70% { transform: scale(0.9); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Loading Animation */
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #ffd700;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 215, 0, 0.1);
        border-radius: 12px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 8px;
        border: none;
        color: #4682b4;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ffd700 0%, #1e90ff 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.4);
    }
    
    /* Chart Styling */
    .vega-embed {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(255, 215, 0, 0.2);
        background: white;
    }
    
    /* Price Tag */
    .price-tag {
        background: linear-gradient(135deg, #32cd32 0%, #228b22 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 18px;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(50, 205, 50, 0.3);
        animation: pulse 2s infinite;
    }
    
    /* Floating Action Button */
    .fab {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #ffd700 0%, #1e90ff 100%);
        color: white;
        border: none;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        font-size: 24px;
        box-shadow: 0 8px 24px rgba(255, 215, 0, 0.4);
        transition: all 0.3s ease;
        z-index: 1000;
    }
    
    .fab:hover {
        transform: scale(1.1);
        box-shadow: 0 12px 32px rgba(30, 144, 255, 0.5);
    }
    
    /* Notification Badge */
    .notification-badge {
        background: #dc3545;
        color: white;
        border-radius: 50%;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: 700;
        position: absolute;
        top: -8px;
        right: -8px;
        min-width: 20px;
        text-align: center;
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Define the API endpoint
API_URL = "http://127.0.0.1:8000"
SEARCH_ENDPOINT = f"{API_URL}/find_supplements"
RECENT_QUERIES_ENDPOINT = f"{API_URL}/recent_queries"

# Helper functions for cart management
def add_to_cart(product):
    """Add a product to the cart"""
    try:
        # Ensure cart_items exists
        if "cart_items" not in st.session_state:
            st.session_state.cart_items = []
        
        # Create a copy of the product to avoid modifying the original
        product_copy = product.copy()
        
        # Check if product already exists in cart
        for item in st.session_state.cart_items:
            if item.get('name') == product_copy.get('name') and item.get('site') == product_copy.get('site'):
                item['quantity'] = item.get('quantity', 1) + 1
                return True
        
        # Add new item to cart
        product_copy['quantity'] = 1
        product_copy['id'] = str(uuid.uuid4())
        st.session_state.cart_items.append(product_copy)
        return True
    except Exception as e:
        st.error(f"Error adding to cart: {str(e)}")
        return False

def remove_from_cart(product_id):
    """Remove a product from the cart"""
    try:
        if "cart_items" not in st.session_state:
            st.session_state.cart_items = []
            return
        
        # Remove by ID or by name if ID not found
        original_count = len(st.session_state.cart_items)
        st.session_state.cart_items = [
            item for item in st.session_state.cart_items 
            if item.get('id') != product_id and item.get('name') != product_id
        ]
        
        # Return True if something was removed
        return len(st.session_state.cart_items) < original_count
    except Exception as e:
        st.error(f"Error removing from cart: {str(e)}")
        return False

def get_cart_total():
    """Calculate total cart value"""
    total = 0
    for item in st.session_state.cart_items:
        price = float(item['price']) if isinstance(item['price'], (int, float)) else float(str(item['price']).replace('$', ''))
        total += price * item['quantity']
    return total

def get_cart_count():
    """Get total number of items in cart"""
    return sum(item['quantity'] for item in st.session_state.cart_items)

# Function to call the API
def search_supplements(query: str) -> Dict[str, Any]:
    """Send a query to the backend API and return the response."""
    max_retries = 3
    retry_count = 0
    retry_delay = 2
    
    while retry_count < max_retries:
        try:
            response = requests.post(
                SEARCH_ENDPOINT,
                json={"query": query},
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {
                "answer": "The search timed out. Please try a different search term.",
                "result_count": 0,
                "error": "Request timed out after 120 seconds"
            }
        except requests.exceptions.ConnectionError:
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(retry_delay)
                continue
            return {
                "answer": "Could not connect to the API server. Please make sure the backend is running.",
                "result_count": 0,
                "error": f"Connection error after {retry_count} attempts"
            }
        except Exception as e:
            return {
                "answer": f"An error occurred: {str(e)}",
                "result_count": 0,
                "error": str(e)
            }

def get_recent_queries(limit: int = 5) -> list:
    """Retrieve recent queries from the backend API."""
    try:
        max_retries = 3
        retry_count = 0
        retry_delay = 2
        
        while retry_count < max_retries:
            try:
                response = requests.get(f"{RECENT_QUERIES_ENDPOINT}?limit={limit}", timeout=5)
                response.raise_for_status()
                return response.json().get("recent_queries", [])
            except requests.exceptions.ConnectionError:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise
            except Exception:
                raise
    except Exception as e:
        return []

# Main Header with modern design
st.markdown("<h1 class='main-header'>💊 SupplementHub</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>🚀 Smart AI-Powered Supplement Price Finder & Shopping Assistant</p>", unsafe_allow_html=True)

# Welcome card with system status
st.markdown("""
<div class='modern-card'>
    <div style='text-align: center;'>
        <h2 style='color: #4682b4; margin-bottom: 16px; font-weight: 600;'>🎯 Welcome to Your Smart Shopping Assistant!</h2>
        <p style='color: #1e90ff; font-size: 1.1rem; margin-bottom: 0;'>
            Discover the best supplement deals with AI-powered price comparison across multiple stores
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# System status check with modern styling
try:
    status_response = requests.get(f"{API_URL}/health", timeout=5)
    if status_response.status_code == 200:
        status_data = status_response.json()
        if status_data.get("status") == "healthy":
            st.markdown("""
            <div class='success-message'>
                <div style='text-align: center;'>
                    <strong>✅ All Systems Operational</strong><br>
                    <small>AI features and price comparison fully available</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='warning-message'>
                <div style='text-align: center;'>
                    <strong>⚠️ Limited Features</strong><br>
                    <small>AI features may be limited, but search functionality is available</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
except:
    st.markdown("""
    <div class='warning-message'>
        <div style='text-align: center;'>
            <strong>⚠️ Backend Connection</strong><br>
            <small>Please start the backend server: <code>uvicorn api:app --reload</code></small>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Sidebar with modern cart functionality
with st.sidebar:
    st.markdown("<h2 style='color: #4682b4; text-align: center; margin-bottom: 24px;'>🛒 Shopping Cart</h2>", unsafe_allow_html=True)
    
    cart_count = get_cart_count()
    cart_total = get_cart_total()
    
    # Cart summary
    st.markdown(f"""
    <div class='sidebar-card'>
        <div style='text-align: center;'>
            <h3 style='color: #ffd700; margin-bottom: 8px;'>{cart_count} Items</h3>
            <div class='price-tag'>${cart_total:.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Cart items
    if st.session_state.cart_items:
        st.markdown("<h4 style='color: #4682b4; margin: 20px 0 10px 0;'>Cart Items:</h4>", unsafe_allow_html=True)
        
        for i, item in enumerate(st.session_state.cart_items):
            price = float(item['price']) if isinstance(item['price'], (int, float)) else float(str(item['price']).replace('$', ''))
            
            st.markdown(f"""
            <div class='cart-item'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <strong style='color: #4682b4;'>{item['name'][:30]}...</strong><br>
                        <small style='color: #1e90ff;'>{item['site']} • Qty: {item['quantity']}</small><br>
                        <span style='color: #32cd32; font-weight: 600;'>${price:.2f}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Use unique key with index to avoid conflicts
            if st.button(f"🗑️ Remove", key=f"remove_cart_{i}_{item.get('id', i)}", help="Remove from cart"):
                remove_from_cart(item.get('id', item['name']))
                st.success(f"Removed {item['name'][:20]}... from cart!")
                time.sleep(1)
                st.rerun()
        
        # Checkout section
        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        
        if st.button("🛒 Proceed to Checkout", use_container_width=True, type="primary"):
            st.markdown("""
            <div class='success-message'>
                <div style='text-align: center;'>
                    <strong>🎉 Checkout Initiated!</strong><br>
                    <small>Redirecting to secure payment...</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(2)
            st.balloons()
        
        if st.button("🗑️ Clear Cart", use_container_width=True):
            st.session_state.cart_items = []
            st.success("Cart cleared!")
            time.sleep(1)
            st.rerun()
    else:
        st.markdown("""
        <div style='text-align: center; padding: 40px 20px; color: #4682b4;'>
            <h4>🛒 Your cart is empty</h4>
            <p>Add some supplements to get started!</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent searches section
    st.markdown("<hr style='margin: 30px 0 20px 0;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #495057; text-align: center;'>📋 Recent Searches</h4>", unsafe_allow_html=True)
    
    recent_queries = get_recent_queries(3)
    if recent_queries:
        for i, query_data in enumerate(recent_queries):
            query_text = query_data.get("query", "Unknown query")
            display_query = query_text if len(query_text) <= 30 else query_text[:27] + "..."
            
            if st.button(f"🔍 {display_query}", key=f"recent_{i}", use_container_width=True):
                st.session_state["query"] = query_text
                st.rerun()

# Main content with tabs
tabs = st.tabs(["🔍 Smart Search", "📊 Price Analytics", "🏪 Store Directory", "ℹ️ About"])

with tabs[0]:  # Smart Search tab
    st.markdown("""
    <div class='modern-card'>
        <h3 style='color: #4682b4; margin-bottom: 20px; text-align: center;'>🚀 AI-Powered Supplement Search</h3>
        <p style='color: #1e90ff; text-align: center; margin-bottom: 30px;'>
            Enter your supplement needs and let our AI find the best deals across multiple stores
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick search buttons
    st.markdown("<h4 style='color: #4682b4; margin: 30px 0 15px 0;'>⚡ Quick Search Options:</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🥛 Whey Protein", use_container_width=True):
            st.session_state["query"] = "best whey protein powder 5lb"
            st.rerun()
        if st.button("🐟 Fish Oil", use_container_width=True):
            st.session_state["query"] = "omega 3 fish oil capsules"
            st.rerun()
    
    with col2:
        if st.button("💪 Creatine", use_container_width=True):
            st.session_state["query"] = "creatine monohydrate powder 500g"
            st.rerun()
        if st.button("🌿 Multivitamin", use_container_width=True):
            st.session_state["query"] = "daily multivitamin tablets"
            st.rerun()
    
    with col3:
        if st.button("⚡ Pre-Workout", use_container_width=True):
            st.session_state["query"] = "pre workout supplement powder"
            st.rerun()
        if st.button("🔥 Fat Burner", use_container_width=True):
            st.session_state["query"] = "fat burner weight loss supplement"
            st.rerun()

with tabs[1]:  # Price Analytics tab
    st.markdown("""
    <div class='modern-card'>
        <h3 style='color: #495057; margin-bottom: 20px; text-align: center;'>📊 Market Price Analytics</h3>
        <p style='color: #6c757d; text-align: center;'>
            Analyze supplement prices across different categories and brands
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sample analytics data
    categories = ["Protein Powder", "Creatine", "Pre-Workout", "Vitamins", "Fish Oil"]
    avg_prices = [45.99, 25.99, 35.99, 18.99, 22.99]
    
    chart_data = pd.DataFrame({
        "Category": categories,
        "Average Price": avg_prices
    })
    
    chart = alt.Chart(chart_data).mark_bar(
        cornerRadiusTopLeft=8,
        cornerRadiusTopRight=8,
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='#ffd700', offset=0),
                   alt.GradientStop(color='#1e90ff', offset=1)],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=alt.X('Category:N', title='Supplement Category'),
        y=alt.Y('Average Price:Q', title='Average Price ($)'),
        tooltip=['Category', 'Average Price']
    ).properties(
        height=400,
        title="Average Supplement Prices by Category"
    )
    
    st.altair_chart(chart, use_container_width=True)

with tabs[2]:  # Store Directory tab
    st.markdown("""
    <div class='modern-card'>
        <h3 style='color: #495057; margin-bottom: 20px; text-align: center;'>🏪 Partner Store Directory</h3>
        <p style='color: #6c757d; text-align: center;'>
            Discover our trusted supplement store partners
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    stores = [
        {"name": "SupplementStore Pro", "rating": "4.8/5", "specialty": "Premium Brands", "discount": "15% OFF"},
        {"name": "FitnessHub Direct", "rating": "4.7/5", "specialty": "Sports Nutrition", "discount": "20% OFF"},
        {"name": "HealthMax Online", "rating": "4.6/5", "specialty": "Organic & Natural", "discount": "10% OFF"},
        {"name": "PowerSupps", "rating": "4.5/5", "specialty": "Bodybuilding", "discount": "25% OFF"}
    ]
    
    for store in stores:
        st.markdown(f"""
        <div class='product-card'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h4 style='color: #495057; margin-bottom: 8px;'>🏪 {store['name']}</h4>
                    <p style='color: #6c757d; margin-bottom: 4px;'>⭐ {store['rating']} • {store['specialty']}</p>
                    <span style='background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 600;'>
                        {store['discount']}
                    </span>
                </div>
                <div>
                    <button class='cart-button'>Visit Store</button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tabs[3]:  # About tab
    st.markdown("""
    <div class='modern-card'>
        <h3 style='color: #495057; margin-bottom: 20px; text-align: center;'>ℹ️ About SupplementHub</h3>
        
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px;'>
            <div>
                <h4 style='color: #667eea;'>🤖 AI Technology</h4>
                <ul style='color: #6c757d;'>
                    <li>Advanced Natural Language Processing</li>
                    <li>Smart Price Comparison Algorithms</li>
                    <li>Real-time Market Analysis</li>
                    <li>Personalized Recommendations</li>
                </ul>
            </div>
            <div>
                <h4 style='color: #667eea;'>🛡️ Features</h4>
                <ul style='color: #6c757d;'>
                    <li>Multi-store Price Comparison</li>
                    <li>Smart Shopping Cart</li>
                    <li>Secure Checkout Process</li>
                    <li>Order History & Tracking</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Enhanced search form
st.markdown("<div class='search-container'>", unsafe_allow_html=True)
st.markdown("<h3 style='color: #495057; text-align: center; margin-bottom: 24px;'>🔍 Search Supplements</h3>", unsafe_allow_html=True)

with st.form(key="search_form", clear_on_submit=False):
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "",
            placeholder="🔍 Search for supplements (e.g., 'whey protein chocolate 5lb', 'creatine monohydrate')",
            value=st.session_state.get("query", ""),
            help="Be specific about size, flavor, and brand for best results"
        )
    with col2:
        submit_button = st.form_submit_button(
            label="🚀 Search", 
            use_container_width=True,
            help="Find the best supplement deals"
        )

st.markdown("</div>", unsafe_allow_html=True)

# Process search results
if submit_button and query or ('query' in st.session_state and st.session_state.query):
    if 'query' in st.session_state:
        query = st.session_state.query
        del st.session_state.query
    
    # Enhanced loading animation
    with st.spinner("🔍 Searching for the best supplement deals..."):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            progress_bar.progress(i + 1)
        
        result = search_supplements(query)
        progress_bar.empty()
        
        if result.get("error") and not result.get("answer"):
            st.markdown(f"""
            <div class='error-message'>
                <div style='text-align: center;'>
                    <strong>❌ Search Error</strong><br>
                    <small>{result['error']}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            raw_data = result.get("raw_data", [])
            result_count = result.get("result_count", len(raw_data))
            
            # Results header
            st.markdown(f"""
            <div class='modern-card' style='text-align: center; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white;'>
                <h2 style='margin-bottom: 12px;'>🎉 Found {result_count} Great Deals!</h2>
                <p style='margin-bottom: 0; opacity: 0.9;'>Here are the best supplement prices we found for you</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show warnings if any
            if result.get("error"):
                error_msg = result['error']
                if "AI analysis unavailable" in error_msg or "AI agent unavailable" in error_msg:
                    st.markdown("""
                    <div class='warning-message'>
                        <div style='text-align: center;'>
                            <strong>⚠️ Limited AI Features</strong><br>
                            <small>AI analysis temporarily unavailable, but we found great deals for you!</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            if raw_data:
                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                
                prices = [float(item['price']) if isinstance(item['price'], (int, float)) else float(str(item['price']).replace('$', '')) for item in raw_data]
                
                with col1:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <h3 style='margin-bottom: 8px;'>💰 Best Price</h3>
                        <h2 style='margin: 0;'>${min(prices):.2f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <h3 style='margin-bottom: 8px;'>📊 Average</h3>
                        <h2 style='margin: 0;'>${sum(prices)/len(prices):.2f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <h3 style='margin-bottom: 8px;'>🏪 Stores</h3>
                        <h2 style='margin: 0;'>{len(set([item['site'] for item in raw_data]))}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    potential_savings = max(prices) - min(prices)
                    st.markdown(f"""
                    <div class='metric-card'>
                        <h3 style='margin-bottom: 8px;'>💸 Max Savings</h3>
                        <h2 style='margin: 0;'>${potential_savings:.2f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Product results
                st.markdown("<h3 style='color: #495057; margin: 40px 0 20px 0; text-align: center;'>🏆 Best Deals Found</h3>", unsafe_allow_html=True)
                
                for i, product in enumerate(raw_data[:6]):  # Show top 6 products
                    price = float(product['price']) if isinstance(product['price'], (int, float)) else float(str(product['price']).replace('$', ''))
                    
                    # Determine if it's a good deal
                    avg_price = sum(prices) / len(prices)
                    is_good_deal = price < avg_price
                    deal_badge = "🔥 HOT DEAL" if is_good_deal else "💎 PREMIUM"
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div class='product-card'>
                            <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;'>
                                <div style='flex: 1;'>
                                    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 8px;'>
                                        <h4 style='color: #495057; margin: 0; flex: 1;'>{product['name'][:50]}...</h4>
                                        <span style='background: {"linear-gradient(135deg, #dc3545 0%, #c82333 100%)" if is_good_deal else "linear-gradient(135deg, #6f42c1 0%, #5a2d91 100%)"}; color: white; padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 600;'>
                                            {deal_badge}
                                        </span>
                                    </div>
                                    <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px;'>
                                        <div>
                                            <small style='color: #6c757d;'>Store</small><br>
                                            <strong style='color: #495057;'>🏪 {product['site']}</strong>
                                        </div>
                                        <div>
                                            <small style='color: #6c757d;'>Brand</small><br>
                                            <strong style='color: #495057;'>🏷️ {product.get('brand', 'N/A')}</strong>
                                        </div>
                                        <div>
                                            <small style='color: #6c757d;'>Rating</small><br>
                                            <strong style='color: #495057;'>⭐ {product.get('rating', 'N/A')}/5</strong>
                                        </div>
                                    </div>
                                    <div style='display: flex; align-items: center; justify-content: space-between;'>
                                        <div class='price-tag'>${price:.2f}</div>
                                        <div style='display: flex; gap: 8px;'>
                                            <a href='{product.get("url", "#")}' target='_blank' style='text-decoration: none;'>
                                                <button class='cart-button'>🔗 View Product</button>
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Create unique key for each add to cart button
                        cart_key = f"add_cart_{i}_{product.get('name', 'unknown')[:10]}_{product.get('site', 'unknown')}"
                        
                        if st.button(f"🛒 Add to Cart", key=cart_key, use_container_width=True, type="primary"):
                            success = add_to_cart(product)
                            if success:
                                st.success(f"✅ Added {product.get('name', 'Product')[:20]}... to cart!")
                                # Force a rerun to update the cart display
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Failed to add item to cart. Please try again.")

# Footer
st.markdown("<hr style='margin: 60px 0 30px 0;'>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; color: white; margin-top: 40px;'>
    <h3 style='margin-bottom: 16px;'>💊 SupplementHub</h3>
    <p style='margin-bottom: 8px; opacity: 0.9;'>AI-Powered Smart Shopping Assistant</p>
    <p style='margin: 0; opacity: 0.7; font-size: 14px;'>Version 3.0.0 | Made with ❤️ and 🤖</p>
</div>
""", unsafe_allow_html=True)