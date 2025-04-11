import streamlit as st
import requests
import json
import time
import pandas as pd
import altair as alt
from typing import Dict, Any, Optional

# Configure the Streamlit page with improved styling
st.set_page_config(
    page_title="Supplement Price Finder",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4527A0;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #5E35B1;
        margin-top: 0;
    }
    .result-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #EDE7F6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .sidebar-content {
        padding: 15px;
        background-color: #f1f3f4;
        border-radius: 10px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Define the API endpoint
API_URL = "http://127.0.0.1:8000"
SEARCH_ENDPOINT = f"{API_URL}/find_supplements"
RECENT_QUERIES_ENDPOINT = f"{API_URL}/recent_queries"

# Function to call the API
def search_supplements(query: str) -> Dict[str, Any]:
    """
    Send a query to the backend API and return the response.
    
    Args:
        query: The user's supplement search query
        
    Returns:
        Dictionary containing the API response
    """
    # Add retry mechanism for connection issues
    max_retries = 3
    retry_count = 0
    retry_delay = 2  # seconds
    
    while retry_count < max_retries:
        try:
            response = requests.post(
                SEARCH_ENDPOINT,
                json={"query": query},
                timeout=120  # Long timeout for web scraping operations
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            # Don't retry on timeout as it's already a long operation
            return {
                "answer": "The search timed out. This might be due to slow website responses or complex search requirements.",
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

# Function to get recent queries
def get_recent_queries(limit: int = 5) -> list:
    """
    Retrieve recent queries from the backend API.
    
    Args:
        limit: Maximum number of recent queries to retrieve
        
    Returns:
        List of recent query data
    """
    try:
        # Add a longer timeout and retry mechanism
        max_retries = 3
        retry_count = 0
        retry_delay = 2  # seconds
        
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
                # For other exceptions, don't retry
                raise
    except Exception as e:
        st.sidebar.error(f"Error fetching recent queries: {str(e)}")
        return []

# Main UI layout with improved design
st.markdown("<h1 class='main-header'>💊 Supplement Price Finder</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Find the best prices for health supplements across multiple stores</p>", unsafe_allow_html=True)

# Create tabs for different sections
tabs = st.tabs(["🔍 Search", "📊 Compare", "ℹ️ About"])

with tabs[0]:  # Search tab
    st.markdown(
        """
        Enter a specific query like "cheapest whey protein chocolate 5lb" or "where to find creatine monohydrate 500g".
        Our AI will search multiple supplement stores to find the best deals for you.
        """
    )
    
    # Add example queries as chips that can be clicked
    st.markdown("### Try these examples:")
    col1, col2, col3 = st.columns(3)
    if col1.button("🥛 Whey Protein 5lb"):
        st.session_state["query"] = "cheapest whey protein 5lb"
        st.rerun()
    if col2.button("💪 Creatine Monohydrate"):
        st.session_state["query"] = "best creatine monohydrate powder"
        st.rerun()
    if col3.button("⚡ Pre-Workout"):
        st.session_state["query"] = "strongest pre-workout supplement"
        st.rerun()

with tabs[1]:  # Compare tab
    st.markdown("### Compare Supplement Prices")
    st.markdown(
        """
        This tab allows you to compare prices across different supplement categories.
        Select a category to see average prices and best deals.
        """
    )
    
    # Category selector
    category = st.selectbox(
        "Select Supplement Category",
        ["Protein Powder", "Creatine", "Pre-Workout", "Vitamins & Minerals", "Amino Acids"]
    )
    
    # Simulated comparison data
    if category:
        # Create simulated data for the selected category
        if category == "Protein Powder":
            comparison_data = {
                "OptimumNutrition": 59.99,
                "MyProtein": 49.99,
                "MuscleTech": 54.99,
                "Dymatize": 64.99,
                "BSN": 57.99
            }
            unit = "5lb container"
        elif category == "Creatine":
            comparison_data = {
                "OptimumNutrition": 29.99,
                "MyProtein": 24.99,
                "MuscleTech": 27.99,
                "AllMax": 32.99,
                "NowFoods": 19.99
            }
            unit = "500g container"
        elif category == "Pre-Workout":
            comparison_data = {
                "OptimumNutrition": 39.99,
                "C4": 34.99,
                "MuscleTech": 42.99,
                "BSN": 44.99,
                "Cellucor": 37.99
            }
            unit = "30 servings"
        elif category == "Vitamins & Minerals":
            comparison_data = {
                "NowFoods": 14.99,
                "NaturesMade": 12.99,
                "OptimumNutrition": 19.99,
                "GNC": 24.99,
                "Centrum": 15.99
            }
            unit = "90 capsules"
        else:  # Amino Acids
            comparison_data = {
                "OptimumNutrition": 34.99,
                "Scivation": 29.99,
                "MuscleTech": 32.99,
                "BSN": 36.99,
                "MyProtein": 27.99
            }
            unit = "30 servings"
        
        # Create a DataFrame for the chart
        chart_data = pd.DataFrame({
            "Brand": list(comparison_data.keys()),
            "Price": list(comparison_data.values())
        })
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Lowest Price", f"${min(comparison_data.values()):.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Average Price", f"${sum(comparison_data.values()) / len(comparison_data):.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Price Range", f"${max(comparison_data.values()) - min(comparison_data.values()):.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Create and display the chart
        st.markdown(f"### Price Comparison for {category} ({unit})")
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Brand:N', title='Brand'),
            y=alt.Y('Price:Q', title='Price ($)'),
            color=alt.Color('Brand:N', legend=None),
            tooltip=['Brand', 'Price']
        ).properties(
            height=400
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Display the best deal
        best_brand = min(comparison_data.items(), key=lambda x: x[1])[0]
        best_price = min(comparison_data.values())
        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        st.markdown(f"### Best Deal for {category}")
        st.markdown(f"**{best_brand}** offers the best price at **${best_price:.2f}** for {unit}.")
        st.markdown(f"This is **${(sum(comparison_data.values()) / len(comparison_data)) - best_price:.2f}** below the average price.")
        st.markdown("</div>", unsafe_allow_html=True)

with tabs[2]:  # About tab
    st.markdown("### About This Tool")
    st.markdown(
        """
        <div class='result-card'>
        <h4>AI-Powered Supplement Price Comparison</h4>
        <p>This tool uses artificial intelligence to help you find the best prices for health supplements across multiple online stores.</p>
        
        <h4>How It Works</h4>
        <ol>
            <li><strong>Natural Language Understanding</strong>: Enter your query in plain English, like "cheapest whey protein chocolate 5lb"</li>
            <li><strong>Intelligent Search</strong>: Our AI agent interprets your query and searches multiple supplement stores</li>
            <li><strong>Price Comparison</strong>: Results are sorted by price to show you the best deals</li>
            <li><strong>Detailed Information</strong>: View product details including ratings, sizes, flavors, and more</li>
        </ol>
        
        <h4>Features</h4>
        <ul>
            <li>Search across multiple supplement stores simultaneously</li>
            <li>Compare prices, ratings, and product details</li>
            <li>View price comparison charts</li>
            <li>Track your search history</li>
            <li>Get detailed product information</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Add information about supported stores
    st.markdown("### Supported Stores")
    
    # Create tabs for Indian and Global stores
    store_tabs = st.tabs(["🇮🇳 Indian Stores", "🌎 Global Stores", "🏆 Specialty Stores"])
    
    # Indian stores
    with store_tabs[0]:
        indian_stores = [
            {"name": "Nutrigize", "products": "Vitamins, minerals, protein supplements"},
            {"name": "MyFitFuel", "products": "Fitness-centric supplements (pre/post-workout)"},
            {"name": "Guardian", "products": "Authentic supplements with quality assurance"},
            {"name": "Nutrabay", "products": "Multi-brand supplements, fitness, and wellness"},
            {"name": "HealthXP", "products": "Sports nutrition, vitamins, and ayurvedic products"},
            {"name": "PharmEasy", "products": "OTC products, supplements, and healthcare devices"},
            {"name": "1mg", "products": "Multivitamins, condition-specific supplements"},
            {"name": "HealthKart", "products": "Supplements, fitness gear, and wellness products"},
            {"name": "MuscleBlaze", "products": "Bodybuilding and sports nutrition"}
        ]
        
        for store in indian_stores:
            st.markdown(f"<div style='padding: 10px; margin-bottom: 10px; background-color: #f5f5f5; border-radius: 5px;'>"
                      f"<h4>{store['name']}</h4>"
                      f"<p>{store['products']}</p>"
                      f"</div>", unsafe_allow_html=True)
    
    # Global stores
    with store_tabs[1]:
        global_stores = [
            {"name": "Bodybuilding.com", "products": "Sports nutrition, workouts, and expert advice"},
            {"name": "GNC", "products": "Vitamins, protein, and wellness products"},
            {"name": "The Vitamin Shoppe", "products": "Wide-range supplements and wellness solutions"},
            {"name": "Vitacost", "products": "Affordable supplements and health foods"},
            {"name": "Amazon Health", "products": "Global marketplace for supplements"},
            {"name": "iHerb", "products": "Natural and organic supplements"},
            {"name": "Holland & Barrett", "products": "Herbal and vegan-friendly products"}
        ]
        
        for store in global_stores:
            st.markdown(f"<div style='padding: 10px; margin-bottom: 10px; background-color: #f5f5f5; border-radius: 5px;'>"
                      f"<h4>{store['name']}</h4>"
                      f"<p>{store['products']}</p>"
                      f"</div>", unsafe_allow_html=True)
    
    # Specialty stores
    with store_tabs[2]:
        specialty_stores = [
            {"name": "Muscle & Strength", "products": "Bodybuilding supplements and workout plans"},
            {"name": "Steel Supplements", "products": "Performance-enhancing formulas"},
            {"name": "Quest Nutrition", "products": "Protein bars and low-carb supplements"},
            {"name": "MaryRuth's Organics", "products": "Vegan and non-GMO supplements"},
            {"name": "Vital Proteins", "products": "Collagen-based wellness products"},
            {"name": "Wellbel", "products": "Hair health and vegan supplements"}
        ]
        
        for store in specialty_stores:
            st.markdown(f"<div style='padding: 10px; margin-bottom: 10px; background-color: #f5f5f5; border-radius: 5px;'>"
                      f"<h4>{store['name']}</h4>"
                      f"<p>{store['products']}</p>"
                      f"</div>", unsafe_allow_html=True)

# Create a search form with improved styling
with st.form(key="search_form", clear_on_submit=False):
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "What supplement are you looking for?",
            placeholder="E.g., cheapest whey protein chocolate 5lb",
            value=st.session_state.get("query", "")
        )
    with col2:
        submit_button = st.form_submit_button(label="🔍 Find Supplements", use_container_width=True)

# Process the search when the form is submitted
if submit_button and query or ('query' in st.session_state and st.session_state.query):
    with st.spinner("Searching for the best supplement prices... This may take a minute."): 
        # Call the API
        result = search_supplements(query)
        
        # Display the results with improved styling
        if result.get("error") and not result.get("answer"):
            st.error(f"Error: {result['error']}")
        else:
            # Extract raw data for visualization
            raw_data = result.get("raw_data", [])
            result_count = result.get("result_count", len(raw_data))
            
            # Display result count with better styling
            st.markdown(f"<h3>Found {result_count} products matching your query</h3>", unsafe_allow_html=True)
            
            # Show any errors as warnings
            if result.get("error"):
                st.warning(f"Note: {result['error']}")
            
            # Add region filter
            if raw_data:
                # Check if region data is available
                has_region_data = any('region' in item for item in raw_data)
                
                if has_region_data:
                    # Get unique regions
                    regions = list(set([item.get('region', 'Global') for item in raw_data]))
                    
                    # Add an 'All Regions' option
                    regions = ['All Regions'] + sorted(regions)
                    
                    # Create region filter
                    selected_region = st.selectbox("Filter by Region", regions)
                    
                    # Filter data based on selected region
                    if selected_region != 'All Regions':
                        filtered_data = [item for item in raw_data if item.get('region', 'Global') == selected_region]
                    else:
                        filtered_data = raw_data
                else:
                    filtered_data = raw_data
                
                # Create metrics for quick insights
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.metric("Lowest Price", f"${min([float(item['price']) if isinstance(item['price'], (int, float)) else float(item['price'].replace('$', '')) for item in filtered_data]):.2f}")
                    st.markdown("</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.metric("Average Price", f"${sum([float(item['price']) if isinstance(item['price'], (int, float)) else float(item['price'].replace('$', '')) for item in filtered_data]) / len(filtered_data):.2f}")
                    st.markdown("</div>", unsafe_allow_html=True)
                with col3:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.metric("Number of Stores", len(set([item['site'] for item in filtered_data])))
                    st.markdown("</div>", unsafe_allow_html=True)
                with col4:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    if has_region_data:
                        region_counts = {}
                        for item in raw_data:
                            region = item.get('region', 'Global')
                            region_counts[region] = region_counts.get(region, 0) + 1
                        st.metric("Regions", len(region_counts))
                    else:
                        st.metric("Regions", "N/A")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Create price comparison chart
                st.markdown("### Price Comparison Chart")
                chart_data = pd.DataFrame([
                    {
                        "Product": item['name'][:30] + "..." if len(item['name']) > 30 else item['name'],
                        "Price": float(item['price']) if isinstance(item['price'], (int, float)) else float(item['price'].replace('$', '')),
                        "Store": item['site'],
                        "Region": item.get('region', 'Global')
                    } for item in filtered_data
                ])
                
                # Create the chart with region information if available
                if has_region_data:
                    chart = alt.Chart(chart_data).mark_bar().encode(
                        x=alt.X('Price:Q', title='Price ($)'),
                        y=alt.Y('Product:N', sort='-x', title='Product'),
                        color=alt.Color('Store:N', legend=alt.Legend(title="Store")),
                        tooltip=['Product', 'Price', 'Store', 'Region']
                    ).properties(
                        height=min(400, len(filtered_data) * 40)
                    )
                else:
                    chart = alt.Chart(chart_data).mark_bar().encode(
                        x=alt.X('Price:Q', title='Price ($)'),
                        y=alt.Y('Product:N', sort='-x', title='Product'),
                        color=alt.Color('Store:N', legend=alt.Legend(title="Store")),
                        tooltip=['Product', 'Price', 'Store']
                    ).properties(
                        height=min(400, len(filtered_data) * 40)
                    )
                
                st.altair_chart(chart, use_container_width=True)
            
            # Display the answer in a card
            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
            st.markdown(result["answer"])
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Display detailed product cards
            if raw_data:
                st.markdown("### Top Products")
                for i, product in enumerate(raw_data[:5]):  # Show top 5 products
                    with st.expander(f"{product['name']} - {product['price']}"):
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown(f"**Brand:** {product.get('brand', 'N/A')}")
                            st.markdown(f"**Size:** {product.get('size', 'N/A')}")
                            st.markdown(f"**Flavor:** {product.get('flavor', 'N/A')}")
                            st.markdown(f"**Rating:** {product.get('rating', 'N/A')}/5 ({product.get('reviews', 0)} reviews)")
                            st.markdown(f"**In Stock:** {'Yes' if product.get('in_stock', True) else 'No'}")
                        with col2:
                            st.markdown(f"**Store:** {product['site']}")
                            if 'region' in product:
                                st.markdown(f"**Region:** {product['region']}")
                            if 'focus' in product:
                                st.markdown(f"**Store Focus:** {product['focus']}")
                            st.markdown(f"**Price:** {product['price']}")
                            # Get URL from either 'url' or 'link' key and ensure it has proper scheme
                            url = product.get('url') or product.get('link', '')
                            # Convert to string if needed
                            url_str = str(url)
                            if url and not (url_str.startswith('http://') or url_str.startswith('https://')):
                                url = 'https://' + url_str.lstrip('/')
                            st.markdown(f"**Link:** [View Product]({url})")
                            
                            # Add a button to visit the product page
                            if st.button(f"Visit Store", key=f"visit_{i}"):
                                st.markdown(f"<script>window.open('{url}', '_blank');</script>", unsafe_allow_html=True)

# Sidebar with improved styling
st.sidebar.markdown("<h2 style='color: #4527A0;'>📋 Recent Searches</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)

# Button to refresh recent queries with better styling
if st.sidebar.button("🔄 Refresh Recent Searches", use_container_width=True):
    recent_queries = get_recent_queries()
    st.session_state["recent_queries"] = recent_queries
    # Clear any previous connection error state
    if "backend_connection_error" in st.session_state:
        del st.session_state["backend_connection_error"]
else:
    # Get recent queries if not already in session state
    if "recent_queries" not in st.session_state:
        try:
            recent_queries = get_recent_queries()
            st.session_state["recent_queries"] = recent_queries
            # Clear any previous connection error state
            if "backend_connection_error" in st.session_state:
                del st.session_state["backend_connection_error"]
        except requests.exceptions.ConnectionError as e:
            st.session_state["backend_connection_error"] = str(e)
            recent_queries = []
        except Exception as e:
            st.session_state["recent_queries"] = []
            recent_queries = []
    else:
        recent_queries = st.session_state["recent_queries"]

# Display connection error if present with a retry button
if "backend_connection_error" in st.session_state:
    st.sidebar.error(
        "⚠️ Cannot connect to the backend API. The server might be starting up or experiencing issues."
    )
    st.sidebar.code(str(st.session_state["backend_connection_error"]), language="bash")
    if st.sidebar.button("🔄 Retry Connection", type="primary", use_container_width=True):
        st.session_state.pop("backend_connection_error", None)
        try:
            recent_queries = get_recent_queries()
            st.session_state["recent_queries"] = recent_queries
            st.rerun()
        except Exception:
            st.sidebar.error("Still unable to connect. Please check if the backend server is running.")

# Display recent queries with improved styling
if recent_queries:
    for query_data in recent_queries:
        with st.sidebar.expander(f"🔍 {query_data['query']} ({query_data['result_count']} results)"):
            st.markdown(f"<span style='color: #666; font-size: 0.9rem;'>Time: {query_data['timestamp']}</span>", unsafe_allow_html=True)
            
            # Display a summary of results if available
            if query_data.get("results_summary"):
                st.markdown("<b>Top results:</b>", unsafe_allow_html=True)
                for i, result in enumerate(query_data["results_summary"][:3]):
                    st.markdown(f"<div style='padding: 5px; margin-bottom: 5px; background-color: #f5f5f5; border-radius: 5px;'>"
                               f"<b>{i+1}.</b> {result['name']}<br/>"
                               f"<span style='color: #4CAF50; font-weight: bold;'>${result['price']:.2f}</span> ({result['site']})"
                               f"</div>", unsafe_allow_html=True)
            
            # Button to re-run this query with better styling
            if st.button("🔄 Search Again", key=f"rerun_{query_data['timestamp']}", use_container_width=True):
                st.session_state["query"] = query_data["query"]
                st.rerun()
elif not "backend_connection_error" in st.session_state:
    st.sidebar.info("No recent searches found. Try searching for supplements to see your history here.")
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Add information about the app in the sidebar
st.sidebar.markdown("<h2 style='color: #4527A0;'>ℹ️ About</h2>", unsafe_allow_html=True)
st.sidebar.markdown("""
<div class='sidebar-content'>
<p>This AI-powered tool helps you find the best prices for health supplements across multiple online stores.</p>
<p>Simply enter what you're looking for, and our AI will search and compare prices for you.</p>
</div>
""", unsafe_allow_html=True)

# Footer with improved styling
st.markdown("---")
st.markdown("""
<div style='display: flex; justify-content: space-between; align-items: center;'>
    <span>AI-Powered Supplement Price Comparison Tool</span>
    <span>Version 1.1.0</span>
</div>
""", unsafe_allow_html=True)