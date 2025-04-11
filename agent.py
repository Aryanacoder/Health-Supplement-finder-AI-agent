import os
import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.schema import AgentAction, AgentFinish

# Import our custom modules
from scraper import AVAILABLE_SCRAPERS, scrape_all_sites
import memory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get Hugging Face API token from environment variables
HF_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
if not HF_API_TOKEN:
    logger.warning("HUGGINGFACEHUB_API_TOKEN not found in environment variables. Using demo mode.")

# Initialize the LLM
try:
    # Use Mistral-7B-Instruct or similar model via Hugging Face Inference API
    if HF_API_TOKEN:
        llm = HuggingFaceEndpoint(
            repo_id="mistralai/Mistral-7B-Instruct-v0.2",  # Can be changed to other models
            max_length=2048,
            temperature=0.7,
            token=HF_API_TOKEN,
        )
        logger.info("Successfully initialized Hugging Face LLM")
    else:
        # Fallback to a mock LLM for demo purposes
        from langchain.llms.fake import FakeListLLM
        llm = FakeListLLM(
            responses=["I'm running in demo mode without a valid Hugging Face API token. Please add a valid token to your .env file for full functionality."],
        )
        logger.warning("Using FakeListLLM as fallback due to missing API token")
except Exception as e:
    logger.error(f"Error initializing Hugging Face LLM: {str(e)}")
    # Fallback to a mock LLM for demo purposes
    from langchain.llms.fake import FakeListLLM
    llm = FakeListLLM(
        responses=["I'm running in demo mode without a valid Hugging Face API token. The original error was: " + str(e)],
    )
    logger.warning("Using FakeListLLM as fallback due to LLM initialization error")

# Define tools for the agent
def create_scraper_tool(site_name: str, scraper_func):
    """
    Create a LangChain Tool for a specific scraper function.
    
    Args:
        site_name: Name of the site
        scraper_func: Function that performs the scraping
        
    Returns:
        LangChain Tool object
    """
    return Tool(
        name=f"search_{site_name.lower().replace(' ', '_')}",
        description=f"Search for supplements on {site_name}. Input should be a specific supplement query.",
        func=lambda query: str(scraper_func(query))
    )

# Create tools for each available scraper
scraper_tools = [create_scraper_tool(site_name, scraper_func) 
                for site_name, scraper_func in AVAILABLE_SCRAPERS.items()]

# Add a tool for searching all sites at once
all_sites_tool = Tool(
    name="search_all_supplement_sites",
    description="Search for supplements across all available sites. Use this when you want comprehensive results.",
    func=lambda query: str(scrape_all_sites(query))
)

# Combine all tools
tools = scraper_tools + [all_sites_tool]

# Define the agent prompt template
prompt_template = """
You are a helpful AI assistant that helps users find the best prices for health supplements.
Your task is to understand the user's query, search for relevant supplements, and provide a helpful response.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
{agent_scratchpad}
"""

prompt = PromptTemplate.from_template(prompt_template)

# Create the agent
agent = create_react_agent(llm, tools, prompt)

# Create the agent executor
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5
)


def format_results_as_markdown_table(results: List[Dict[str, Any]]) -> str:
    """
    Format the scraped results as a Markdown table sorted by price.
    
    Args:
        results: List of product dictionaries
        
    Returns:
        Markdown formatted table string
    """
    if not results:
        return "No results found."
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(results)
    
    # Sort by price (lowest first)
    df = df.sort_values(by="price")
    
    # Format price as currency
    df["price"] = df["price"].apply(lambda x: f"${x:.2f}")
    
    # Create markdown table
    markdown_table = "| Product | Price | Rating | Size | Brand | Site | Link |\n"
    markdown_table += "|---------|-------|--------|------|-------|------|------|\n"
    
    for _, row in df.iterrows():
        # Truncate product name if too long
        name = row["name"]
        if len(name) > 40:
            name = name[:37] + "..."
        
        # Format rating with stars if available
        rating = row.get("rating", "N/A")
        if isinstance(rating, (int, float)):
            rating_str = f"{rating}/5 ({row.get('reviews', 0)} reviews)"
        else:
            rating_str = "N/A"
        
        # Get size if available
        size = row.get("size", "N/A")
        
        # Get brand if available
        brand = row.get("brand", "N/A")
        
        # Create proper markdown link with full URL
        url = row['url']
        # Convert HttpUrl to string if needed
        url_str = str(url)
        # Ensure URL has proper scheme
        if url and not (url_str.startswith('http://') or url_str.startswith('https://')):
            url = 'https://' + url_str.lstrip('/')
        link = f"[View]({url})"
        
        markdown_table += f"| {name} | {row['price']} | {rating_str} | {size} | {brand} | {row['site']} | {link} |\n"
    
    return markdown_table


def run_agent_query(user_query: str) -> Dict[str, Any]:
    """
    Process a user query through the agent and return structured results.
    
    Args:
        user_query: The user's query about supplements
        
    Returns:
        Dictionary containing the agent's answer, raw data, and any errors
    """
    logger.info(f"Processing query: {user_query}")
    
    try:
        # Get recent interactions to potentially enhance context
        recent_interactions = memory.get_recent_interactions(limit=3)
        
        # Run the agent
        agent_result = agent_executor.invoke({"input": user_query})
        
        # Extract the agent's textual response
        agent_answer = agent_result.get("output", "")
        
        # Re-run the scraper to get structured data
        # This is needed because the agent returns string representations of the data
        raw_data = scrape_all_sites(user_query)
        
        # Add region and focus information to each result if not already present
        for result in raw_data:
            site_name = result.get('site')
            if site_name in AVAILABLE_SCRAPERS and 'region' not in result:
                result['region'] = getattr(AVAILABLE_SCRAPERS[site_name], 'region', 'Global')
            if site_name in AVAILABLE_SCRAPERS and 'focus' not in result:
                result['focus'] = getattr(AVAILABLE_SCRAPERS[site_name], 'focus', '')
        
        # Sort the raw data by price (lowest first)
        raw_data.sort(key=lambda x: float(x.get("price", float('inf'))))
        
        # Generate markdown comparison table
        comparison_table = format_results_as_markdown_table(raw_data)
        
        # Find the cheapest option if available
        cheapest_option = None
        if raw_data:
            cheapest_option = raw_data[0]
            cheapest_text = f"\n\n**Best Deal:** {cheapest_option['name']} at ${cheapest_option['price']:.2f} from {cheapest_option['site']}"
        else:
            cheapest_text = ""
        
        # Combine agent's answer with the comparison table and cheapest option
        combined_answer = f"{agent_answer}{cheapest_text}\n\n## Price Comparison\n{comparison_table}"
        
        # Save the interaction to memory
        response_data = {
            "raw_data": raw_data,
            "error": None
        }
        memory.save_interaction(user_query, response_data)
        
        return {
            "answer": combined_answer,
            "raw_data": raw_data,
            "error": None,
            "result_count": len(raw_data)  # Add result count for the UI
        }
        
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        logger.error(error_msg)
        
        # Save the failed interaction to memory
        error_response = {
            "raw_data": [],
            "error": error_msg
        }
        memory.save_interaction(user_query, error_response)
        
        return {
            "answer": "I'm sorry, I encountered an error while processing your query.",
            "raw_data": [],
            "error": error_msg,
            "result_count": 0  # No results when there's an error
        }