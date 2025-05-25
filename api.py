import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from datetime import datetime

# Import the agent runner function
from agent import run_agent_query
# Import the memory saving function
from memory import save_interaction
# Import scraper directly as fallback
from scraper import scrape_all_sites

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Supplement Finder Agent API",
    description="API endpoint for the supplement finding AI agent with memory and fallback support.",
    version="0.2.0"
)

class QueryRequest(BaseModel):
    query: str

class AgentResponse(BaseModel):
    answer: str | None = None
    raw_data: list | None = None
    error: str | None = None


def create_fallback_response(query: str, raw_data: list) -> dict:
    """Create a basic response when AI agent is not available"""
    if not raw_data:
        return {
            "answer": "No supplement products found for your search. Please try different keywords or check back later.",
            "raw_data": [],
            "error": None,
            "result_count": 0
        }
    
    # Sort by price
    raw_data.sort(key=lambda x: float(x.get("price", float('inf'))))
    
    # Create basic markdown table
    markdown_table = "| Product | Price | Site | Link |\n"
    markdown_table += "|---------|-------|------|------|\n"
    
    for item in raw_data[:10]:  # Show top 10 results
        name = item['name'][:40] + "..." if len(item['name']) > 40 else item['name']
        price = f"${float(item['price']):.2f}" if isinstance(item['price'], (int, float)) else str(item['price'])
        site = item['site']
        url = str(item.get('url', ''))
        if url and not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url.lstrip('/')
        link = f"[View]({url})" if url else "N/A"
        
        markdown_table += f"| {name} | {price} | {site} | {link} |\n"
    
    cheapest = raw_data[0] if raw_data else None
    best_deal_text = f"\n\n**Best Deal:** {cheapest['name']} at ${float(cheapest['price']):.2f} from {cheapest['site']}" if cheapest else ""
    
    answer = f"Found {len(raw_data)} supplement products matching your search.{best_deal_text}\n\n## Price Comparison\n{markdown_table}"
    
    return {
        "answer": answer,
        "raw_data": raw_data,
        "error": None,
        "result_count": len(raw_data)
    }


@app.post("/find_supplements", response_model=AgentResponse)
async def find_supplements_endpoint(request: QueryRequest):
    """
    Receives a user query, runs the AI agent with fallback support,
    saves the interaction, and returns the findings.
    """
    logger.info(f"Received query: {request.query}")
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    agent_result = None
    try:
        # Try the AI agent first
        agent_result = run_agent_query(request.query)
        logger.info(f"Agent finished for query: {request.query}")

        # Save interaction
        save_interaction(request.query, agent_result)

        if "error" in agent_result and agent_result["error"]:
            # If agent had an error but still returned data, use it
            if agent_result.get("raw_data"):
                return AgentResponse(
                    answer=agent_result.get("answer"), 
                    raw_data=agent_result.get("raw_data"),
                    error=agent_result["error"]
                )
            else:
                # Try fallback scraping
                logger.warning("Agent failed, trying fallback scraping...")
                raw_data = scrape_all_sites(request.query)
                fallback_result = create_fallback_response(request.query, raw_data)
                save_interaction(request.query, fallback_result)
                return AgentResponse(**fallback_result)
        else:
            return AgentResponse(
                answer=agent_result.get("answer"), 
                raw_data=agent_result.get("raw_data")
            )

    except Exception as e:
        logger.exception(f"Unhandled exception in /find_supplements endpoint for query '{request.query}': {e}")
        
        # Try direct scraping as last resort
        try:
            logger.info("Attempting direct scraping as fallback...")
            raw_data = scrape_all_sites(request.query)
            fallback_result = create_fallback_response(request.query, raw_data)
            fallback_result["error"] = f"AI agent unavailable, using basic search: {str(e)}"
            save_interaction(request.query, fallback_result)
            return AgentResponse(**fallback_result)
        except Exception as scraper_error:
            logger.exception(f"Even fallback scraping failed: {scraper_error}")
            
            # Final fallback
            error_response = {
                "error": f"All systems unavailable: {str(e)}",
                "raw_data": []
            }
            save_interaction(request.query, error_response)
            raise HTTPException(
                status_code=500, 
                detail=f"Service temporarily unavailable. Please try again later."
            )


# Basic root endpoint
@app.get("/")
async def root():
    return {"message": "Supplement Finder Agent API v0.2.0 is running. Use the POST /find_supplements endpoint."}

# Endpoint to get recent queries
@app.get("/recent_queries")
async def get_recent_queries(limit: int = 5):
    """Retrieve recent user queries from the memory database"""
    try:
        from memory import get_recent_interactions
        recent_interactions = get_recent_interactions(limit=limit)
        
        # Format the response to match what the frontend expects
        recent_queries = [{
            "timestamp": item.get("timestamp", ""),
            "query": item.get("query", ""),
            "result_count": item.get("result_count", 0),
            "error": item.get("error_message")
        } for item in recent_interactions]
        
        return {"recent_queries": recent_queries}
    except Exception as e:
        logger.exception(f"Error retrieving recent queries: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent queries: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test if scraping works
        test_result = scrape_all_sites("test")
        return {
            "status": "healthy",
            "scraper_status": "working",
            "timestamp": str(datetime.now())
        }
    except Exception as e:
        return {
            "status": "degraded",
            "scraper_status": f"error: {str(e)}",
            "timestamp": str(datetime.now())
        }

# Run the API server
if __name__ == "__main__":
    logger.info("Starting Supplement Finder Agent API server...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)