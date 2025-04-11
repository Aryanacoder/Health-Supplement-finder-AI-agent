import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Callable
from functools import lru_cache
import json

# Import scraper base
from scraper_base import create_scraper
from scraper_utils import normalize_data

logger = logging.getLogger(__name__)

# In-memory cache using lru_cache decorator
@lru_cache(maxsize=1024)
def cached_scrape(query: str, site_name: str, scraper_func: Callable):
    """
    Cache scraping results to avoid repeated requests for the same query.
    
    Args:
        query: The product query
        site_name: The name of the site being scraped
        scraper_func: The function to call if cache miss
        
    Returns:
        Cached or fresh scraping results
    """
    logger.info(f"Cache miss for {site_name}:{query}, fetching fresh data")
    results = scraper_func(query)
    return json.dumps(results)  # Convert to string for caching


def get_cached_results(query: str, site_name: str, scraper_func: Callable):
    """
    Get results from cache or scrape fresh data.
    
    Args:
        query: The product query
        site_name: The name of the site being scraped
        scraper_func: The function to call if cache miss
        
    Returns:
        Scraping results (from cache or fresh)
    """
    cached = cached_scrape(query, site_name, scraper_func)
    return json.loads(cached)  # Convert back to Python objects


def parallel_scrape(site_configs: Dict[str, Dict], product_query: str, max_workers: int = 5) -> List[Dict[str, Any]]:
    """
    Scrape multiple sites in parallel using ThreadPoolExecutor.
    
    Args:
        site_configs: Dictionary of site configurations
        product_query: The product query to search for
        max_workers: Maximum number of concurrent workers
        
    Returns:
        Combined list of product information from all sites
    """
    all_results = []
    real_scraper_success = False
    
    # Create a list of (site_name, scraper) tuples, excluding the simulated scraper
    scrapers = [
        (site_name, create_scraper(site_name, config))
        for site_name, config in site_configs.items()
        if site_name != "SimulatedSupplementSite"
    ]
    
    # Define a function to scrape a single site with timing and error handling
    def scrape_site(site_tuple):
        site_name, scraper = site_tuple
        try:
            logger.info(f"Starting parallel scrape of {site_name} for: {product_query}")
            start_time = time.time()
            
            # Try to get cached results first
            site_results = get_cached_results(
                product_query, 
                site_name, 
                lambda q: scraper.scrape(q)
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Scraped {site_name} in {elapsed:.2f}s, found {len(site_results)} results")
            
            return site_name, site_results, True
        except Exception as e:
            logger.error(f"Error scraping {site_name}: {str(e)}")
            return site_name, [], False
    
    # Execute scraping in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scraping tasks
        future_to_site = {executor.submit(scrape_site, site_tuple): site_tuple for site_tuple in scrapers}
        
        # Process results as they complete
        for future in as_completed(future_to_site):
            site_tuple = future_to_site[future]
            try:
                site_name, site_results, success = future.result()
                if site_results:
                    all_results.extend(site_results)
                    logger.info(f"Retrieved {len(site_results)} results from {site_name}")
                    real_scraper_success = True
                else:
                    logger.warning(f"No results found on {site_name} for query: {product_query}")
            except Exception as e:
                logger.error(f"Exception occurred while scraping {site_tuple[0]}: {str(e)}")
    
    # If no real scrapers returned results, use the simulated scraper as fallback
    if not real_scraper_success and "SimulatedSupplementSite" in site_configs:
        try:
            from scraper import simulate_scrape_supplement_site
            logger.info(f"No results from real scrapers, falling back to simulated data for: {product_query}")
            simulated_results = simulate_scrape_supplement_site(product_query)
            all_results.extend(simulated_results)
            logger.info(f"Retrieved {len(simulated_results)} simulated results")
        except Exception as e:
            logger.error(f"Error with simulated scraper: {str(e)}")
    
    # Normalize all results
    normalized_results = normalize_data(all_results)
    
    # Validate all results against schema
    from schema_validation import validate_products
    validated_results = validate_products(normalized_results)
    
    return validated_results