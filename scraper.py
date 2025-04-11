import os
import random
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

# Import utility modules
from scraper_utils import (
    get_random_user_agent, 
    get_advanced_headers, 
    get_rotating_proxy,
    add_delay, 
    classify_error, 
    ScraperError,
    update_success_rate,
    update_response_time,
    send_alert,
    normalize_data,
    update_selectors
)

# Import scraper base classes
from scraper_base import create_scraper, ScraperBase
from dynamic_scraper import create_dynamic_scraper
from concurrent_scraper import parallel_scrape
from schema_validation import validate_products

# Import real scrapers
from real_scrapers import REAL_SCRAPERS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define site configuration with selectors and base URLs
# NOTE: These are EXAMPLE configurations and will NOT work on real sites without customization
SITE_CONFIG = {
    # Original example sites
    "ExampleSupplementStore": {
        "base_url": "https://example-supplement-store.com/search",
        "search_param": "q",
        "product_selector": ".product-item",
        "name_selector": ".product-title",
        "price_selector": ".product-price",
        "link_selector": ".product-link",
        "timeout": 10,
        "region": "Global"
    },
    "AnotherExampleSite": {
        "base_url": "https://another-example-site.com/products",
        "search_param": "search",
        "product_selector": ".product-card",
        "name_selector": ".product-name",
        "price_selector": ".product-cost",
        "link_selector": "a.product-link",
        "timeout": 10,
        "region": "Global"
    },
    "SimulatedSupplementSite": {
        "base_url": "https://simulated-supplement-site.com/search",
        "search_param": "term",
        "timeout": 5,
        "region": "Global"
    },
    
    # Indian Healthcare Supplement Platforms
    "Nutrigize": {
        "base_url": "https://nutrigize.in/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Vitamins, minerals, protein supplements"
    },
    "MyFitFuel": {
        "base_url": "https://myfitfuel.in/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Fitness-centric supplements (pre/post-workout)"
    },
    "Guardian": {
        "base_url": "https://guardian.in/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Authentic supplements with quality assurance"
    },
    "Nutrabay": {
        "base_url": "https://nutrabay.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Multi-brand supplements, fitness, and wellness"
    },
    "HealthXP": {
        "base_url": "https://healthxp.in/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Sports nutrition, vitamins, and ayurvedic products"
    },
    "PharmEasy": {
        "base_url": "https://pharmeasy.in/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "OTC products, supplements, and healthcare devices"
    },
    "1mg": {
        "base_url": "https://www.1mg.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Multivitamins, condition-specific supplements"
    },
    "GetSupp": {
        "base_url": "https://www.getsupp.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Herbal, ayurvedic, and sports supplements"
    },
    "WellbeingNutrition": {
        "base_url": "https://wellbeingnutrition.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Clean, science-backed formulations"
    },
    "VitabioticsIndia": {
        "base_url": "https://vitabiotics.in/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "UK-based multivitamins (Wellman, Wellwoman)"
    },
    "MuscleBlaze": {
        "base_url": "https://muscleblaze.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Bodybuilding and sports nutrition"
    },
    "HealthKart": {
        "base_url": "https://healthkart.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Supplements, fitness gear, and wellness products"
    },
    "Netmeds": {
        "base_url": "https://netmeds.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Pharmaceuticals and dietary supplements"
    },
    "ApolloPharmacy": {
        "base_url": "https://apollopharmacy.in/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Vitamins, minerals, and OTC health products"
    },
    "BigBasket": {
        "base_url": "https://bigbasket.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Indian",
        "focus": "Groceries with a dedicated supplements section"
    },
    
    # Global Healthcare Supplement Platforms
    "Bodybuilding": {
        "base_url": "https://bodybuilding.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Sports nutrition, workouts, and expert advice"
    },
    "GNC": {
        "base_url": "https://gnc.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Vitamins, protein, and wellness products"
    },
    "VitaminShoppe": {
        "base_url": "https://vitaminshoppe.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Wide-range supplements and wellness solutions"
    },
    "Vitacost": {
        "base_url": "https://vitacost.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Affordable supplements and health foods"
    },
    "AmazonHealth": {
        "base_url": "https://www.amazon.com/s",
        "search_param": "k",
        "product_selector": "div.s-result-item[data-component-type='s-search-result']",
        "name_selector": "h2 > a > span",
        "price_selector": "span.a-price > span.a-offscreen",
        "link_selector": "h2 > a",
        "timeout": 15,
        "region": "Global",
        "focus": "Global marketplace for supplements"
    },
    "WalmartHealth": {
        "base_url": "https://walmart.com/health",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Budget-friendly supplements and OTC products"
    },
    "eBaySupplements": {
        "base_url": "https://ebay.com/sch",
        "search_param": "_nkw",
        "timeout": 10,
        "region": "Global",
        "focus": "Auction-based supplement marketplace"
    },
    "iHerb": {
        "base_url": "https://www.iherb.com/search",
        "search_param": "kw",
        "product_selector": "div.product-cell",
        "name_selector": "div.product-title",
        "price_selector": "div.product-price span.price",
        "link_selector": "a.product-link",
        "timeout": 15,
        "region": "Global",
        "focus": "Natural and organic supplements"
    },
    "HollandBarrett": {
        "base_url": "https://hollandandbarrett.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Herbal and vegan-friendly products"
    },
    "PuritansPride": {
        "base_url": "https://puritan.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Vitamins, minerals, and specialty formulations"
    },
    "SwansonVitamins": {
        "base_url": "https://swansonvitamins.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Affordable supplements and wellness tools"
    },
    "CVSPharmacy": {
        "base_url": "https://cvs.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "OTC products and condition-specific supplements"
    },
    "Walgreens": {
        "base_url": "https://walgreens.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Multivitamins and health devices"
    },
    "TargetHealth": {
        "base_url": "https://target.com/s",
        "search_param": "searchTerm",
        "timeout": 10,
        "region": "Global",
        "focus": "Curated wellness and supplement brands"
    },
    "ChemistWarehouse": {
        "base_url": "https://chemistwarehouse.com.au/search",
        "search_param": "searchterm",
        "timeout": 10,
        "region": "Global",
        "focus": "Australian-based supplements and pharmaceuticals"
    },
    
    # Niche and Specialty Platforms
    "MuscleStrength": {
        "base_url": "https://muscleandstrength.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Bodybuilding supplements and workout plans"
    },
    "PipingRock": {
        "base_url": "https://pipingrock.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Discounted vitamins and herbal products"
    },
    "SteelSupplements": {
        "base_url": "https://steelsupplements.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Performance-enhancing formulas"
    },
    "NatureMade": {
        "base_url": "https://naturemade.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "USP-verified multivitamins"
    },
    "QuestNutrition": {
        "base_url": "https://questnutrition.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Protein bars and low-carb supplements"
    },
    "MaryRuthOrganics": {
        "base_url": "https://maryruthorganics.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Vegan and non-GMO supplements"
    },
    "VitalProteins": {
        "base_url": "https://vitalproteins.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Collagen-based wellness products"
    },
    "Wellbel": {
        "base_url": "https://wellbel.com/search",
        "search_param": "q",
        "timeout": 10,
        "region": "Global",
        "focus": "Hair health and vegan supplements"
    }
}


# Legacy scraper functions kept for backward compatibility
def scrape_example_site(product_query: str) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility"""
    logger.warning("Using legacy scraper function. Consider using the new class-based scrapers.")
    config = SITE_CONFIG["ExampleSupplementStore"]
    scraper = create_scraper("ExampleSupplementStore", config)
    return scraper.scrape(product_query)


def scrape_another_example_site(product_query: str) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility"""
    logger.warning("Using legacy scraper function. Consider using the new class-based scrapers.")
    config = SITE_CONFIG["AnotherExampleSite"]
    scraper = create_scraper("AnotherExampleSite", config)
    return scraper.scrape(product_query)


def simulate_scrape_supplement_site(product_query: str) -> List[Dict[str, Any]]:
    """
    Simulate scraping from a supplement site by returning hardcoded/randomized data.
    This function is useful for testing the agent without making actual web requests.
    
    Args:
        product_query: The user's search query for supplements
        
    Returns:
        List of dictionaries containing simulated product information
    """
    logger.info(f"Simulating scrape for: {product_query}")
    
    # Parse query to determine what kind of supplement the user is looking for
    query_lower = product_query.lower()
    
    # Determine supplement type from query
    if "protein" in query_lower:
        supplement_type = "protein"
    elif "creatine" in query_lower:
        supplement_type = "creatine"
    elif "vitamin" in query_lower:
        supplement_type = "vitamin"
    elif "pre workout" in query_lower or "preworkout" in query_lower:
        supplement_type = "pre-workout"
    else:
        supplement_type = "general supplement"
    
    # Simulate different product variants based on the query
    results = []
    brands = ["OptimumNutrition", "MyProtein", "MuscleTech", "Dymatize", "BSN", "AllMax", "NowFoods"]
    
    # Generate 3-7 random products
    num_products = random.randint(3, 7)
    
    for i in range(num_products):
        brand = random.choice(brands)
        
        if supplement_type == "protein":
            flavors = ["Chocolate", "Vanilla", "Strawberry", "Cookies & Cream", "Banana"]
            sizes = ["2lb", "5lb", "10lb"]
            flavor = random.choice(flavors)
            size = random.choice(sizes)
            name = f"{brand} Gold Standard Whey Protein - {flavor} ({size})"
            # Price range based on size
            if size == "2lb":
                price = round(random.uniform(24.99, 39.99), 2)
            elif size == "5lb":
                price = round(random.uniform(49.99, 69.99), 2)
            else:  # 10lb
                price = round(random.uniform(89.99, 119.99), 2)
                
        elif supplement_type == "creatine":
            types = ["Monohydrate", "HCL", "Ethyl Ester", "Nitrate"]
            sizes = ["300g", "500g", "1kg"]
            creatine_type = random.choice(types)
            size = random.choice(sizes)
            name = f"{brand} Creatine {creatine_type} - Unflavored ({size})"
            # Price range based on size and type
            if size == "300g":
                price = round(random.uniform(14.99, 24.99), 2)
            elif size == "500g":
                price = round(random.uniform(19.99, 34.99), 2)
            else:  # 1kg
                price = round(random.uniform(29.99, 49.99), 2)
                
        elif supplement_type == "pre-workout":
            strengths = ["Standard", "Advanced", "Extreme", "Elite"]
            flavors = ["Fruit Punch", "Blue Raspberry", "Watermelon", "Green Apple"]
            strength = random.choice(strengths)
            flavor = random.choice(flavors)
            name = f"{brand} {strength} Pre-Workout - {flavor} (30 servings)"
            # Price based on strength
            if strength == "Standard":
                price = round(random.uniform(24.99, 34.99), 2)
            elif strength == "Advanced":
                price = round(random.uniform(34.99, 44.99), 2)
            elif strength == "Extreme":
                price = round(random.uniform(44.99, 54.99), 2)
            else:  # Elite
                price = round(random.uniform(54.99, 69.99), 2)
                
        else:  # general supplement or vitamin
            types = ["Multivitamin", "Fish Oil", "Magnesium", "Zinc", "Vitamin D3", "B Complex"]
            supplement = random.choice(types)
            name = f"{brand} {supplement} (90 capsules)"
            price = round(random.uniform(9.99, 29.99), 2)
        
        # Add more detailed product information with region data
        results.append({
            "name": name,
            "price": price,
            "url": f"https://simulated-supplement-site.com/products/{brand.lower()}-{supplement_type.replace(' ', '-')}-{i}",
            "site": "SimulatedSupplementSite",
            "rating": round(random.uniform(3.0, 5.0), 1),  # Random rating between 3.0-5.0
            "reviews": random.randint(10, 500),  # Random number of reviews
            "size": size if 'size' in locals() else "Standard",  # Size if available
            "brand": brand,  # Brand name
            "flavor": flavor if 'flavor' in locals() else "Unflavored",  # Flavor if available
            "in_stock": random.choice([True, True, True, False]),  # Usually in stock
            "region": SITE_CONFIG["SimulatedSupplementSite"].get("region", "Global"),  # Get region from config
            "focus": SITE_CONFIG["SimulatedSupplementSite"].get("focus", "Offers competitive prices on all types of supplements")
        })
    
    # Sort by price to make it more realistic
    results.sort(key=lambda x: x["price"])
    
    return results


# Dictionary mapping site names to scraper functions
AVAILABLE_SCRAPERS: Dict[str, Callable[[str], List[Dict[str, Any]]]] = {
    # Real website scrapers - prioritize these for actual results
    **REAL_SCRAPERS,  # Add all real scrapers from the real_scrapers module
    
    # Include the simulated scraper as a fallback when real scrapers fail
    "SimulatedSupplementSite": simulate_scrape_supplement_site,
    
    # Example scrapers are commented out
    # "ExampleSupplementStore": scrape_example_site,
    # "AnotherExampleSite": scrape_another_example_site,
}


def scrape_all_sites(product_query: str) -> List[Dict[str, Any]]:
    """
    Scrape all available sites for the given product query using parallel scraping.
    
    Args:
        product_query: The user's search query for supplements
        
    Returns:
        Combined list of product information from all sites
    """
    # Use the new parallel scraping implementation
    all_results = parallel_scrape(SITE_CONFIG, product_query, max_workers=5)
    
    # Log the number of results before validation
    logger.info(f"Retrieved {len(all_results)} total products before validation")
    
    # Group products by site for pre-validation stats
    site_counts = {}
    for product in all_results:
        site = product.get('site', 'Unknown')
        site_counts[site] = site_counts.get(site, 0) + 1
    
    for site, count in site_counts.items():
        logger.info(f"Retrieved {count} products from {site}")
    
    # Validate all results against the schema
    validated_results = validate_products(all_results)
    
    # Log validation efficiency
    validation_ratio = len(validated_results) / len(all_results) if all_results else 0
    logger.info(f"Validation efficiency: {validation_ratio:.2%} ({len(validated_results)}/{len(all_results)} products passed validation)")
    
    return validated_results


# Circuit breaker pattern implementation for scraping
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = {}
        self.circuit_open = {}
        self.last_failure_time = {}
    
    def execute(self, site_name, scraper_func, *args, **kwargs):
        # Check if circuit is open (too many failures)
        if self.circuit_open.get(site_name, False):
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time.get(site_name, 0) > self.recovery_timeout:
                # Reset circuit
                self.circuit_open[site_name] = False
                self.failures[site_name] = 0
                logger.info(f"Circuit reset for {site_name} after recovery timeout")
            else:
                # Circuit still open, skip scraping
                logger.warning(f"Circuit open for {site_name}, skipping scrape")
                return []
        
        try:
            # Execute scraper function
            results = scraper_func(*args, **kwargs)
            
            # Success, reset failure count
            self.failures[site_name] = 0
            return results
            
        except Exception as e:
            # Increment failure count
            self.failures[site_name] = self.failures.get(site_name, 0) + 1
            self.last_failure_time[site_name] = time.time()
            
            # Check if failure threshold reached
            if self.failures[site_name] >= self.failure_threshold:
                self.circuit_open[site_name] = True
                logger.error(f"Circuit opened for {site_name} after {self.failures[site_name]} failures")
                send_alert(site_name, f"Circuit breaker tripped: {str(e)}")
            
            # Re-raise exception
            raise


# Initialize circuit breaker
circuit_breaker = CircuitBreaker()


# Function to get dynamic content scrapers for JavaScript-heavy sites
def get_dynamic_scrapers():
    """
    Get a list of sites that require dynamic content handling with Selenium.
    
    Returns:
        Dictionary mapping site names to dynamic scraper instances
    """
    # Sites that are known to require JavaScript rendering
    js_heavy_sites = [
        "WalmartHealth",
        "TargetHealth",
        # Add more sites as needed
    ]
    
    dynamic_scrapers = {}
    for site_name in js_heavy_sites:
        if site_name in SITE_CONFIG:
            dynamic_scrapers[site_name] = create_dynamic_scraper(site_name, SITE_CONFIG[site_name])
    
    return dynamic_scrapers