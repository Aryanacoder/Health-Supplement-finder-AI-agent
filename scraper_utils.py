import os
import random
import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Union
import logging
from functools import lru_cache
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from retrying import retry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# User-Agent rotation to help avoid detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 OPR/80.0.4170.63',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:97.0) Gecko/20100101 Firefox/97.0'
]

# Browser fingerprinting parameters
BROWSER_FINGERPRINTS = [
    {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "accept_encoding": "gzip, deflate, br",
        "accept_language": "en-US,en;q=0.5",
        "color_depth": 24,
        "resolution": "1920x1080",
        "timezone": "America/New_York",
        "platform": "Win32"
    },
    {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept_encoding": "gzip, deflate, br",
        "accept_language": "en-GB,en-US;q=0.9,en;q=0.8",
        "color_depth": 24,
        "resolution": "2560x1440",
        "timezone": "Europe/London",
        "platform": "MacIntel"
    },
    {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept_encoding": "gzip, deflate",
        "accept_language": "en-US,en;q=0.5",
        "color_depth": 32,
        "resolution": "1366x768",
        "timezone": "Asia/Kolkata",
        "platform": "Linux x86_64"
    }
]

# Proxy rotation system
PROXY_PROVIDERS = {
    "BrightData": "https://proxy.brightdata.com/",
    "Oxylabs": "https://oxylabs.io/",
    "SmartProxy": "https://smartproxy.com/",
    "ProxyScrape": "https://proxyscrape.com/",
    "WebShare": "https://webshare.io/"
}

# Track proxy performance
PROXY_PERFORMANCE = {}

# Enhanced proxy rotation with performance tracking and automatic fallback
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_rotating_proxy(country=None, site_name=None):
    """Rotate through multiple proxy providers with performance tracking and automatic fallback
    
    Args:
        country: Optional country code for geo-specific proxies
        site_name: Optional site name for site-specific proxy selection
        
    Returns:
        Proxy URL string
    """
    # Get available proxies
    available_proxies = [
        f"{PROXY_PROVIDERS['BrightData']}:{os.getenv('BRIGHTDATA_PORT')}",
        f"{PROXY_PROVIDERS['Oxylabs']}:{os.getenv('OXYLABS_PORT')}",
        f"{PROXY_PROVIDERS['WebShare']}:{os.getenv('WEBSHARE_PORT')}"
    ]
    
    if country:
        # Add country-specific proxies if available
        country_proxies = [
            f"{PROXY_PROVIDERS['BrightData']}/{country}:{os.getenv('BRIGHTDATA_PORT')}",
            f"{PROXY_PROVIDERS['Oxylabs']}/{country}:{os.getenv('OXYLABS_PORT')}"
        ]
        
        # Add country-specific proxies to available proxies
        available_proxies.extend(country_proxies)
    
    # If site_name is provided, check if we have site-specific proxy performance data
    if site_name and site_name in PROXY_PERFORMANCE:
        # Sort proxies by success rate for this specific site
        site_proxies = sorted(
            PROXY_PERFORMANCE[site_name].items(),
            key=lambda x: (x[1]['success_rate'], -x[1]['avg_response_time']),
            reverse=True
        )
        
        # Use the best performing proxy for this site
        if site_proxies:
            best_proxy = site_proxies[0][0]
            logger.info(f"Using best performing proxy for {site_name}: {best_proxy}")
            return best_proxy
    
    # Sort by performance if we have data
    if PROXY_PERFORMANCE:
        available_proxies.sort(key=lambda p: PROXY_PERFORMANCE.get(p, {'success_rate': 0})['success_rate'], reverse=True)
    
    # Get the best performing proxy or a random one if no performance data
    selected_proxy = available_proxies[0] if PROXY_PERFORMANCE else random.choice(available_proxies)
    
    return selected_proxy
    
    # Sort by performance if we have data
    if PROXY_PERFORMANCE:
        available_proxies.sort(key=lambda p: PROXY_PERFORMANCE.get(p, {'success_rate': 0})['success_rate'], reverse=True)
    
    # Get the best performing proxy or a random one if no performance data
    selected_proxy = available_proxies[0] if PROXY_PERFORMANCE else random.choice(available_proxies)
    
    return selected_proxy

def update_proxy_performance(proxy, success, response_time=None):
    """Update proxy performance metrics
    
    Args:
        proxy: The proxy URL
        success: Whether the request was successful
        response_time: Response time in milliseconds
    """
    if proxy not in PROXY_PERFORMANCE:
        PROXY_PERFORMANCE[proxy] = {
            'success_count': 0,
            'failure_count': 0,
            'success_rate': 0,
            'avg_response_time': 0,
            'last_used': datetime.now()
        }
    
    perf = PROXY_PERFORMANCE[proxy]
    perf['last_used'] = datetime.now()
    
    if success:
        perf['success_count'] += 1
        if response_time:
            # Update rolling average of response time
            if perf['avg_response_time'] == 0:
                perf['avg_response_time'] = response_time
            else:
                perf['avg_response_time'] = (perf['avg_response_time'] * 0.9) + (response_time * 0.1)
    else:
        perf['failure_count'] += 1
    
    total = perf['success_count'] + perf['failure_count']
    perf['success_rate'] = perf['success_count'] / total if total > 0 else 0

def get_random_user_agent():
    """Get a random user agent from the list"""
    return random.choice(USER_AGENTS)

def get_advanced_headers(site_name=None):
    """Get advanced headers with browser fingerprinting
    
    Args:
        site_name: Optional site name for site-specific headers
        
    Returns:
        Dictionary of HTTP headers
    """
    # Select a random browser fingerprint
    fingerprint = random.choice(BROWSER_FINGERPRINTS)
    
    # Generate a consistent but random session ID
    session_id = hashlib.md5(f"{time.time()}-{random.random()}".encode()).hexdigest()
    
    # Create base headers
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': fingerprint['accept'],
        'Accept-Language': fingerprint['accept_language'],
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': f'"{fingerprint["platform"]}"',
    }
    
    # Add site-specific headers if needed
    if site_name == "AmazonHealth":
        headers['Referer'] = 'https://www.amazon.com/'
        headers['Origin'] = 'https://www.amazon.com'
    elif site_name == "iHerb":
        headers['Referer'] = 'https://www.iherb.com/'
        headers['Origin'] = 'https://www.iherb.com'
    
    # Add cookies to simulate a real browser session
    current_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    expiry_date = (datetime.now() + timedelta(days=30)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    headers['Cookie'] = f'session-id={session_id}; session-token={hashlib.sha256(session_id.encode()).hexdigest()}; ubid-main={hashlib.md5(get_random_user_agent().encode()).hexdigest()}; session-created={current_date}; session-expires={expiry_date}'
    
    return headers

def add_delay(min_delay=1, max_delay=3, site_name=None):
    """Add a random delay between requests to avoid rate limiting
    
    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds
        site_name: Optional site name for site-specific delays
        
    Returns:
        The actual delay used in seconds
    """
    # Site-specific delays (some sites need longer delays)
    site_specific_delays = {
        "iHerb": (2, 5),
        "Amazon": (3, 7),
        "Walmart": (2, 4)
    }
    
    # Use site-specific delay if available
    if site_name and site_name in site_specific_delays:
        min_delay, max_delay = site_specific_delays[site_name]
    
    # Add jitter for more natural timing
    jitter = random.uniform(0, 0.5)
    delay = random.uniform(min_delay, max_delay) + jitter
    
    # Exponential backoff if we detect we're being rate limited
    global _rate_limit_counter
    if '_rate_limit_counter' not in globals():
        _rate_limit_counter = {}
    
    if site_name:
        if site_name not in _rate_limit_counter:
            _rate_limit_counter[site_name] = 0
        
        # Apply exponential backoff if we've hit rate limits recently
        if _rate_limit_counter[site_name] > 0:
            backoff_factor = min(5, _rate_limit_counter[site_name])  # Cap at 5x
            delay *= backoff_factor
            _rate_limit_counter[site_name] -= 1
    
    time.sleep(delay)
    return delay

# Error classification
ERROR_CODES = {
    "BLOCKED": "Cloudflare challenge detected",
    "TIMEOUT": "Response timeout exceeded",
    "CAPTCHA": "CAPTCHA page rendered",
    "STRUCTURE": "HTML structure changed",
    "RATE_LIMIT": "429 Too Many Requests",
    "BOT_DETECTION": "Bot detection triggered",
    "IP_BANNED": "IP address banned",
    "EMPTY_RESPONSE": "Empty response received",
    "REDIRECT_LOOP": "Redirect loop detected",
    "HONEYPOT": "Honeypot trap detected"
}

class ScraperError(Exception):
    """Custom exception for scraper errors"""
    def __init__(self, error_code, message=None, site_name=None):
        self.error_code = error_code
        self.message = message or ERROR_CODES.get(error_code, "Unknown error")
        self.site_name = site_name
        super().__init__(self.message)

def classify_error(response, site_name=None):
    """Classify the error based on the response
    
    Args:
        response: The HTTP response object
        site_name: Optional site name for site-specific error handling
        
    Raises:
        ScraperError: When an error is detected
    """
    # Track rate limiting for exponential backoff
    global _rate_limit_counter
    if '_rate_limit_counter' not in globals():
        _rate_limit_counter = {}
    
    # Check for rate limiting
    if response.status_code == 429:
        if site_name:
            if site_name not in _rate_limit_counter:
                _rate_limit_counter[site_name] = 0
            _rate_limit_counter[site_name] += 1
        raise ScraperError("RATE_LIMIT", site_name=site_name)
    
    # Check for blocking
    elif response.status_code == 403:
        if "cf-challenge" in response.text or "cloudflare" in response.text.lower():
            raise ScraperError("BLOCKED", "Cloudflare protection detected", site_name)
        elif "captcha" in response.text.lower():
            raise ScraperError("CAPTCHA", "CAPTCHA challenge detected", site_name)
        elif "bot" in response.text.lower() or "automated" in response.text.lower():
            raise ScraperError("BOT_DETECTION", "Bot detection triggered", site_name)
        else:
            raise ScraperError("IP_BANNED", f"Access forbidden (403)", site_name)
    
    # Check for other HTTP errors
    elif response.status_code >= 400:
        raise ScraperError("STRUCTURE", f"HTTP error {response.status_code}", site_name)
    
    # Check for empty responses
    elif not response.text.strip():
        raise ScraperError("EMPTY_RESPONSE", "Empty response received", site_name)
    
    # Check for honeypot traps (fake data that only bots would see)
    elif "honeypot" in response.text.lower() or "bot-trap" in response.text.lower():
        raise ScraperError("HONEYPOT", "Honeypot trap detected", site_name)
    
    # Check for too many redirects
    elif len(response.history) > 5:
        raise ScraperError("REDIRECT_LOOP", "Too many redirects", site_name)

# Redis-based caching system
try:
    import redis
    redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), 
                              port=int(os.getenv('REDIS_PORT', 6379)), 
                              db=0,
                              decode_responses=True)
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Fallback to in-memory cache
    logger.warning("Redis not available (ImportError), falling back to in-memory cache")
except Exception as e:
    REDIS_AVAILABLE = False
    # Fallback to in-memory cache
    logger.warning(f"Redis connection failed: {str(e)}, falling back to in-memory cache")

def get_cache_key(query, site):
    """Generate a cache key for the query and site
    
    Args:
        query: The search query
        site: The site name
        
    Returns:
        A unique cache key
    """
    # Create a deterministic hash for the cache key
    key_data = f"{query.lower().strip()}:{site.lower()}"
    return f"scraper:cache:{hashlib.md5(key_data.encode()).hexdigest()}"

def get_cached_data(query, site):
    """Get cached data if available
    
    Args:
        query: The search query
        site: The site name
        
    Returns:
        Cached data or None if not found
    """
    cache_key = get_cache_key(query, site)
    
    if REDIS_AVAILABLE:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Redis error: {str(e)}")
    else:
        # Fallback to in-memory cache using lru_cache
        return _in_memory_cache.get(cache_key)
    
    return None

def set_cached_data(query, site, data, expire_seconds=3600):
    """Cache data with expiration
    
    Args:
        query: The search query
        site: The site name
        data: The data to cache
        expire_seconds: Cache expiration time in seconds
    """
    cache_key = get_cache_key(query, site)
    serialized = json.dumps(data)
    
    if REDIS_AVAILABLE:
        try:
            redis_client.set(cache_key, serialized, ex=expire_seconds)
        except Exception as e:
            logger.error(f"Redis error: {str(e)}")
            # Fallback to in-memory cache
            _in_memory_cache[cache_key] = data
    else:
        # Use in-memory cache
        _in_memory_cache[cache_key] = data

# In-memory cache fallback
_in_memory_cache = {}

@lru_cache(maxsize=1024)
def cached_scrape(query, site, scraper_func):
    """Cache scraping results
    
    Args:
        query: The search query
        site: The site name
        scraper_func: Function to call if cache miss
        
    Returns:
        Cached or fresh scraping results
    """
    # Try to get from cache first
    cached_data = get_cached_data(query, site)
    if cached_data:
        logger.info(f"Cache hit for {site}:{query}")
        return cached_data
    
    # Cache miss, fetch fresh data
    logger.info(f"Cache miss for {site}:{query}, fetching fresh data")
    results = scraper_func(query)
    
    # Cache the results
    set_cached_data(query, site, results)
    
    return results

# Selector versioning
SELECTOR_VERSIONS = {
    "iHerb_2025v2": {
        "product_selector": "div.product-cell",
        "name_selector": "div.product-title",
        "price_selector": "div.product-price span.price",
        "link_selector": "a.product-link"
    },
    "AmazonHealth_2025v2": {
        "product_selector": "div.s-result-item[data-component-type='s-search-result']",
        "name_selector": "h2 > a > span",
        "price_selector": "span.a-price > span.a-offscreen",
        "link_selector": "h2 > a"
    }
}

def get_selector_version(site_name):
    """Get the current selector version for a site"""
    # In a production environment, this might be stored in a database or configuration file
    return "2025v2"

def update_selectors(site_name):
    """Update selectors based on the current version"""
    current_version = get_selector_version(site_name)
    return SELECTOR_VERSIONS.get(f"{site_name}_{current_version}", {})

# Data normalization
def normalize_data(products):
    """Normalize product data to ensure compatibility with ProductSchema"""
    normalized = []
    
    for product in products:
        # Skip products without required fields
        if not all(key in product for key in ['name', 'price', 'url', 'site']):
            logger.warning(f"Skipping product missing required fields: {product.get('name', 'Unknown')}") 
            continue
            
        # Normalize price to float and round to 2 decimal places
        try:
            price = float(product['price'])
            price = round(price, 2)
        except (ValueError, TypeError):
            logger.warning(f"Invalid price format for product: {product.get('name', 'Unknown')}") 
            continue
            
        # Ensure URL is properly formatted
        # Convert HttpUrl to string if needed
        url_str = str(product['url'])
        if not url_str.startswith(('http://', 'https://')):
            product['url'] = 'https://' + url_str.lstrip('/')
            
        # Create normalized product with all required fields
        normalized_product = {
            **product,
            "price": price,
            "currency": product.get("currency", "USD"),
            "timestamp": datetime.utcnow().isoformat(),
            "rating": float(product.get("rating", 0.0)),
            "reviews": int(product.get("reviews", 0)),
            "in_stock": bool(product.get("in_stock", True))
        }
        
        # Add optional fields with proper defaults if missing
        if "brand" not in normalized_product:
            normalized_product["brand"] = "Unknown"
            
        if "size" not in normalized_product:
            normalized_product["size"] = "Standard"
            
        if "flavor" not in normalized_product:
            normalized_product["flavor"] = "Unflavored"
            
        if "region" not in normalized_product:
            normalized_product["region"] = "Global"
            
        normalized.append(normalized_product)
    
    logger.info(f"Normalized {len(normalized)}/{len(products)} products")
    return normalized

# Monitoring metrics (simplified for this implementation)
SCRAPER_METRICS = {
    "success_rate": {},
    "response_time": {}
}

def update_success_rate(site, success):
    """Update success rate metric"""
    if site not in SCRAPER_METRICS["success_rate"]:
        SCRAPER_METRICS["success_rate"][site] = {"success": 0, "total": 0}
    
    SCRAPER_METRICS["success_rate"][site]["total"] += 1
    if success:
        SCRAPER_METRICS["success_rate"][site]["success"] += 1

def update_response_time(site, time_ms):
    """Update response time metric"""
    if site not in SCRAPER_METRICS["response_time"]:
        SCRAPER_METRICS["response_time"][site] = []
    
    SCRAPER_METRICS["response_time"][site].append(time_ms)
    # Keep only the last 100 measurements
    SCRAPER_METRICS["response_time"][site] = SCRAPER_METRICS["response_time"][site][-100:]

def send_alert(site, error):
    """Send an alert for a scraper error"""
    logger.error(f"ALERT: {site} failed with {error}")
    # In a production environment, this might send an email, Slack message, etc.
    # requests.post(ALERT_WEBHOOK, json={"site": site, "error": error})