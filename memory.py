import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from tinydb import TinyDB, Query

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Initialize TinyDB database
try:
    db = TinyDB('data/user_interactions.json')
    logger.info("Successfully initialized TinyDB database")
except Exception as e:
    logger.error(f"Error initializing TinyDB database: {str(e)}")
    # Fallback to an in-memory database if file access fails
    db = TinyDB(storage=TinyDB.default_storage_class())
    logger.warning("Using in-memory database as fallback")


def save_interaction(user_query: str, response_data: Dict[str, Any]) -> bool:
    """
    Save user interaction to the database.
    
    Args:
        user_query: The user's original query
        response_data: Dictionary containing the agent's response data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract relevant information from response_data
        result_count = len(response_data.get("raw_data", []))
        error_status = response_data.get("error") is not None
        
        # Create interaction record
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "query": user_query,
            "result_count": result_count,
            "error_status": error_status,
            "error_message": response_data.get("error"),
            # Store a summary of results (not the full data to save space)
            "results_summary": [
                {"name": item["name"], "price": item["price"], "site": item["site"]}
                for item in response_data.get("raw_data", [])
            ]
        }
        
        # Insert into database
        db.insert(interaction)
        logger.info(f"Saved interaction for query: {user_query}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving interaction to database: {str(e)}")
        return False


def get_recent_interactions(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve recent user interactions from the database.
    
    Args:
        limit: Maximum number of interactions to retrieve
        
    Returns:
        List of interaction records, sorted by timestamp (newest first)
    """
    try:
        # Get all interactions
        all_interactions = db.all()
        
        # Sort by timestamp (newest first)
        sorted_interactions = sorted(
            all_interactions,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        # Return limited number of interactions
        return sorted_interactions[:limit]
        
    except Exception as e:
        logger.error(f"Error retrieving recent interactions: {str(e)}")
        return []


def get_interaction_by_query(query_text: str) -> Optional[Dict[str, Any]]:
    """
    Find a specific interaction by query text.
    
    Args:
        query_text: The query text to search for
        
    Returns:
        Interaction record if found, None otherwise
    """
    try:
        User = Query()
        results = db.search(User.query == query_text)
        
        if results:
            # Return the most recent matching interaction
            return sorted(
                results,
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )[0]
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error searching for interaction: {str(e)}")
        return None


def clear_all_interactions() -> bool:
    """
    Clear all interactions from the database.
    Primarily used for testing or resetting the application.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db.truncate()
        logger.info("Cleared all interactions from database")
        return True
    except Exception as e:
        logger.error(f"Error clearing interactions: {str(e)}")
        return False