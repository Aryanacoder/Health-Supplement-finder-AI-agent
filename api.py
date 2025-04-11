import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Import the agent runner function
from agent import run_agent_query
# Import the memory saving function << --- NEW
from memory import save_interaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Supplement Finder Agent API",
    description="API endpoint for the supplement finding AI agent with memory.", # Updated description
    version="0.1.1" # Bump version
)

class QueryRequest(BaseModel):
    query: str

class AgentResponse(BaseModel):
    answer: str | None = None
    raw_data: list | None = None
    error: str | None = None


@app.post("/find_supplements", response_model=AgentResponse)
async def find_supplements_endpoint(request: QueryRequest):
    """
    Receives a user query, runs the AI agent, saves the interaction,
    and returns the findings.
    """
    logger.info(f"Received query: {request.query}")
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    agent_result = None # Initialize agent_result
    try:
        agent_result = run_agent_query(request.query)
        logger.info(f"Agent finished for query: {request.query}")

        # --- Save Interaction (regardless of error in agent response) ---
        # We save the outcome, whether it was successful or resulted in an error message
        save_interaction(request.query, agent_result)
        # --- End Save Interaction ---

        if "error" in agent_result and agent_result["error"]:
             return AgentResponse(error=agent_result["error"], raw_data=agent_result.get("raw_data"))
        else:
             return AgentResponse(answer=agent_result.get("answer"), raw_data=agent_result.get("raw_data"))

    except Exception as e:
        logger.exception(f"Unhandled exception in /find_supplements endpoint for query '{request.query}': {e}")
        # Also try to save the fact that an internal error occurred, if possible
        if agent_result is None: # If error happened before agent even returned
            error_response_for_saving = {"error": f"Internal Server Error: {str(e)}", "raw_data": []}
            save_interaction(request.query, error_response_for_saving)

        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")


# Basic root endpoint
@app.get("/")
async def root():
    return {"message": "Supplement Finder Agent API v0.1.1 is running. Use the POST /find_supplements endpoint."}

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

# Run the API server
if __name__ == "__main__":
    logger.info("Starting Supplement Finder Agent API server...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False) # Use reload=True for dev if needed