import requests
import logging
import time
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import random

# Import utility functions
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

logger = logging.getLogger(__name__)

class ScraperBase:
    """Base class for all scrapers"""
    
    def __init__(self, site_config):
        self.config = site_config
        self.site_name = None  # To be set by subclasses
        self.retries = 3
        self.backoff_factor = 0.5
        self.timeout = site_config.get("timeout", 10)
        self.use_proxies = False  # Set to True in subclasses that need proxies
        
    def fetch_page(self, url, use_proxy=False):
        """Fetch a page with retry logic and proxy rotation"""
        start_time = time.time()
        
        # Set up session with retry logic
        session = requests.Session()
        retries = Retry(
            total=self.retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # Set up headers with site-specific customization
        headers = get_advanced_headers(site_name=self.site_name)
        
        # Set up proxies if needed
        proxies = None
        if use_proxy or self.use_proxies:
            proxy = get_rotating_proxy(site_name=self.site_name)
            proxies = {
                'http': proxy,
                'https': proxy
            }
        
        try:
            # Add random delay before request to mimic human behavior
            add_delay(min_delay=0.5, max_delay=2.0)
            
            # Send request
            response = session.get(
                url, 
                headers=headers, 
                proxies=proxies, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Check for anti-scraping measures
            classify_error(response)
            
            # Update metrics
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            update_response_time(self.site_name, elapsed_time)
            update_success_rate(self.site_name, True)
            
            # Track proxy performance if using proxies
            if proxies and 'https' in proxies:
                proxy_url = proxies['https']
                if self.site_name not in PROXY_PERFORMANCE:
                    PROXY_PERFORMANCE[self.site_name] = {}
                if proxy_url not in PROXY_PERFORMANCE[self.site_name]:
                    PROXY_PERFORMANCE[self.site_name][proxy_url] = {
                        'success_count': 0,
                        'failure_count': 0,
                        'success_rate': 0.0,
                        'avg_response_time': 0.0,
                        'response_times': []
                    }
                
                # Update proxy performance metrics
                perf = PROXY_PERFORMANCE[self.site_name][proxy_url]
                perf['success_count'] += 1
                perf['response_times'].append(elapsed_time)
                perf['avg_response_time'] = sum(perf['response_times']) / len(perf['response_times'])
                perf['success_rate'] = perf['success_count'] / (perf['success_count'] + perf['failure_count'])
            
            return response
            
        except ScraperError as e:
            logger.error(f"{self.site_name} scraper encountered {e.error_code}: {e.message}")
            update_success_rate(self.site_name, False)
            
            # Track proxy failure
            if proxies and 'https' in proxies:
                proxy_url = proxies['https']
                if self.site_name not in PROXY_PERFORMANCE:
                    PROXY_PERFORMANCE[self.site_name] = {}
                if proxy_url not in PROXY_PERFORMANCE[self.site_name]:
                    PROXY_PERFORMANCE[self.site_name][proxy_url] = {
                        'success_count': 0,
                        'failure_count': 0,
                        'success_rate': 0.0,
                        'avg_response_time': 0.0,
                        'response_times': []
                    }
                
                # Update proxy failure metrics
                perf = PROXY_PERFORMANCE[self.site_name][proxy_url]
                perf['failure_count'] += 1
                perf['success_rate'] = perf['success_count'] / (perf['success_count'] + perf['failure_count'])
            
            send_alert(self.site_name, e.message)
            raise
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            update_success_rate(self.site_name, False)
            
            # Track proxy failure for general exceptions too
            if proxies and 'https' in proxies:
                proxy_url = proxies['https']
                if self.site_name not in PROXY_PERFORMANCE:
                    PROXY_PERFORMANCE[self.site_name] = {}
                if proxy_url not in PROXY_PERFORMANCE[self.site_name]:
                    PROXY_PERFORMANCE[self.site_name][proxy_url] = {
                        'success_count': 0,
                        'failure_count': 0,
                        'success_rate': 0.0,
                        'avg_response_time': 0.0,
                        'response_times': []
                    }
                
                # Update proxy failure metrics
                perf = PROXY_PERFORMANCE[self.site_name][proxy_url]
                perf['failure_count'] += 1
                perf['success_rate'] = perf['success_count'] / (perf['success_count'] + perf['failure_count'])
            
            raise
    
    def parse_page(self, html):
        """Parse HTML content"""
        return BeautifulSoup(html, 'lxml')
    
    def extract_products(self, soup):
        """Extract products from soup - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement extract_products")
    
    def scrape(self, product_query):
        """Main scraping method"""
        try:
            # Update selectors if needed
            updated_selectors = update_selectors(self.site_name)
            if updated_selectors:
                self.config.update(updated_selectors)
            
            # Construct search URL
            search_url = self._build_search_url(product_query)
            
            # Fetch page
            response = self.fetch_page(search_url)
            
            # Parse HTML
            soup = self.parse_page(response.text)
            
            # Extract products
            products = self.extract_products(soup)
            
            # Normalize data
            normalized_products = normalize_data(products)
            
            # Validate products against schema
            from schema_validation import validate_products
            validated_products = validate_products(normalized_products)
            
            # Add delay to avoid rate limiting
            add_delay()
            
            return validated_products
            
        except Exception as e:
            logger.error(f"Error scraping {self.site_name}: {str(e)}")
            return []
    
    def _build_search_url(self, product_query):
        """Build search URL from product query"""
        base_url = self.config["base_url"]
        search_param = self.config["search_param"]
        return f"{base_url}?{search_param}={product_query.replace(' ', '+')}"


class AmazonScraper(ScraperBase):
    """Amazon-specific scraper implementation"""
    
    def __init__(self, site_config):
        super().__init__(site_config)
        self.site_name = "AmazonHealth"
        self.use_proxies = True  # Amazon often blocks scrapers
    
    def extract_products(self, soup):
        """Extract products from Amazon search results"""
        results = []
        product_elements = soup.select(self.config["product_selector"])
        
        logger.info(f"Found {len(product_elements)} products on {self.site_name}")
        
        for product in product_elements:
            try:
                # Skip sponsored products
                sponsored_element = product.select_one('span.s-label-popover-default')
                if sponsored_element and 'sponsor' in sponsored_element.text.lower():
                    continue
                
                # Extract product name
                name_element = product.select_one(self.config["name_selector"])
                if not name_element:
                    continue
                name = name_element.text.strip()
                
                # Extract price
                price_element = product.select_one(self.config["price_selector"])
                if not price_element:
                    continue
                
                price_text = price_element.text.strip()
                # Extract numeric price (remove currency symbols, etc.)
                import re
                price_match = re.search(r'\$(\d+\.\d+)', price_text)
                if not price_match:
                    continue
                price = float(price_match.group(1).replace(',', ''))
                
                # Extract product URL
                link_element = product.select_one(self.config["link_selector"])
                if not link_element:
                    continue
                
                link = link_element.get('href')
                if link and not link.startswith('http'):
                    from urllib.parse import urljoin
                    link = urljoin('https://www.amazon.com', link)
                
                # Extract rating if available
                rating_element = product.select_one('span.a-icon-alt')
                rating = None
                if rating_element:
                    rating_text = rating_element.text.strip()
                    rating_match = re.search(r'([\d.]+) out of 5 stars', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Extract review count if available
                reviews_element = product.select_one('span.a-size-base.s-underline-text')
                reviews = 0
                if reviews_element:
                    reviews_text = reviews_element.text.strip().replace(',', '')
                    if reviews_text.isdigit():
                        reviews = int(reviews_text)
                
                # Extract brand if available
                brand = "Unknown"
                brand_element = product.select_one('h5.s-line-clamp-1')
                if brand_element:
                    brand = brand_element.text.strip()
                
                # Add to results
                results.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "site": self.site_name,
                    "rating": rating if rating else 0,
                    "reviews": reviews,
                    "size": "Standard",  # Default size
                    "brand": brand,
                    "flavor": "Unflavored",  # Default flavor
                    "in_stock": True,  # Default to True
                    "region": self.config.get("region", "Global"),
                    "focus": self.config.get("focus", "Global marketplace for supplements")
                })
                
            except Exception as e:
                logger.error(f"Error extracting product data: {str(e)}")
                continue
        
        return results


class iHerbScraper(ScraperBase):
    """iHerb-specific scraper implementation"""
    
    def __init__(self, site_config):
        super().__init__(site_config)
        self.site_name = "iHerb"
    
    def extract_products(self, soup):
        """Extract products from iHerb search results"""
        results = []
        product_elements = soup.select(self.config["product_selector"])
        
        logger.info(f"Found {len(product_elements)} products on {self.site_name}")
        
        for product in product_elements:
            try:
                # Extract product name
                name_element = product.select_one('div.product-title')
                if not name_element:
                    continue
                name = name_element.text.strip()
                
                # Extract price
                price_element = product.select_one(self.config["price_selector"])
                if not price_element:
                    continue
                
                price_text = price_element.text.strip()
                # Extract numeric price (remove currency symbols, etc.)
                import re
                price_match = re.search(r'\$(\d+\.\d+)', price_text)
                if not price_match:
                    continue
                price = float(price_match.group(1).replace(',', ''))
                
                # Extract product URL
                link_element = product.select_one(self.config["link_selector"])
                if not link_element:
                    continue
                
                link = link_element.get('href')
                if link and not link.startswith('http'):
                    from urllib.parse import urljoin
                    link = urljoin('https://www.iherb.com', link)
                
                # Extract brand
                brand_element = product.select_one('div.product-brand')
                brand = brand_element.text.strip() if brand_element else "Unknown"
                
                # Extract rating if available
                rating_element = product.select_one('div.rating span.rating-count')
                rating = None
                reviews = 0
                
                if rating_element:
                    rating_text = rating_element.text.strip()
                    rating_match = re.search(r'([\d.]+)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Extract review count if available
                reviews_element = product.select_one('div.rating span.rating-count')
                if reviews_element:
                    reviews_text = reviews_element.text.strip()
                    reviews_match = re.search(r'\((\d+)\)', reviews_text)
                    if reviews_match:
                        reviews = int(reviews_match.group(1))
                
                # Extract size/quantity if available
                size_element = product.select_one('div.product-size')
                size = size_element.text.strip() if size_element else "Standard"
                
                # Check if in stock
                stock_element = product.select_one('div.product-stock')
                in_stock = True  # Default to True
                if stock_element and 'out of stock' in stock_element.text.lower():
                    in_stock = False
                
                # Add to results
                results.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "site": self.site_name,
                    "rating": rating if rating else 0,
                    "reviews": reviews,
                    "size": size,
                    "brand": brand,
                    "flavor": "Unflavored",  # Default flavor
                    "in_stock": in_stock,
                    "region": self.config.get("region", "Global"),
                    "focus": self.config.get("focus", "Natural and organic supplements")
                })
                
            except Exception as e:
                logger.error(f"Error extracting product data: {str(e)}")
                continue
        
        return results


# Factory function to create appropriate scraper based on site name
def create_scraper(site_name, site_config):
    """Create a scraper instance based on site name"""
    scrapers = {
        "AmazonHealth": AmazonScraper,
        "iHerb": iHerbScraper,
        # Add more scrapers here as they are implemented
    }
    
    scraper_class = scrapers.get(site_name)
    if scraper_class:
        return scraper_class(site_config)
    else:
        # Return a generic scraper for sites without specific implementations
        generic = ScraperBase(site_config)
        generic.site_name = site_name
        return generic