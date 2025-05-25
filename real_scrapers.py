import requests
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import re
import time
import random
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# User-Agent rotation to help avoid detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

# Function to get a random user agent
def get_random_user_agent():
    return random.choice(USER_AGENTS)

# Function to add delay between requests to avoid rate limiting
def add_delay(min_delay=1, max_delay=3):
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)
    return delay

# iHerb scraper implementation
def scrape_iherb(product_query: str) -> List[Dict[str, Any]]:
    """
    Scrape product information from iHerb.
    
    Args:
        product_query: The user's search query for supplements
        
    Returns:
        List of dictionaries containing product information
    """
    logger.info(f"Attempting to scrape iHerb for: {product_query}")
    
    results = []
    
    try:
        # Construct search URL
        search_url = f"https://www.iherb.com/search?kw={product_query.replace(' ', '+')}"
        
        # Set up headers with random user agent
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.iherb.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Send HTTP request
        logger.debug(f"Sending request to: {search_url}")
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find product containers
        product_elements = soup.select('div.product-cell')
        
        logger.info(f"Found {len(product_elements)} products on iHerb")
        
        # Extract product information
        for product in product_elements:
            try:
                # Extract product name
                name_element = product.select_one('div.product-title')
                if not name_element:
                    continue
                name = name_element.text.strip()
                
                # Extract price
                price_element = product.select_one('div.product-price span.price')
                if not price_element:
                    continue
                
                price_text = price_element.text.strip()
                # Extract numeric price (remove currency symbols, etc.)
                price_match = re.search(r'\$([\d,.]+)', price_text)
                if not price_match:
                    continue
                price = float(price_match.group(1).replace(',', ''))
                
                # Extract product URL
                link_element = product.select_one('a.product-link')
                if not link_element:
                    continue
                
                link = link_element.get('href')
                if link and not link.startswith('http'):
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
                    "site": "iHerb",
                    "rating": rating if rating else 0,
                    "reviews": reviews,
                    "size": size,
                    "brand": brand,
                    "flavor": "Unflavored",  # Default flavor
                    "in_stock": in_stock,
                    "region": "Global",
                    "focus": "Natural and organic supplements"
                })
                
            except Exception as e:
                logger.error(f"Error extracting product data: {str(e)}")
                continue
        
        # Add delay to avoid rate limiting
        add_delay()
                
    except requests.exceptions.Timeout:
        logger.error("Request to iHerb timed out")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {str(e)}")
        
    return results

# Amazon Health scraper implementation
def scrape_amazon_health(product_query: str) -> List[Dict[str, Any]]:
    """
    Scrape product information from Amazon's health section.
    
    Args:
        product_query: The user's search query for supplements
        
    Returns:
        List of dictionaries containing product information
    """
    logger.info(f"Attempting to scrape Amazon Health for: {product_query}")
    
    results = []
    
    try:
        # Construct search URL
        search_url = f"https://www.amazon.com/s?k={product_query.replace(' ', '+')}&i=hpc"
        
        # Set up headers with random user agent
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.amazon.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Send HTTP request
        logger.debug(f"Sending request to: {search_url}")
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find product containers
        product_elements = soup.select('div.s-result-item[data-component-type="s-search-result"]')
        
        logger.info(f"Found {len(product_elements)} products on Amazon Health")
        
        # Extract product information
        for product in product_elements:
            try:
                # Skip sponsored products
                sponsored_element = product.select_one('span.s-label-popover-default')
                if sponsored_element and 'sponsor' in sponsored_element.text.lower():
                    continue
                
                # Extract product name
                name_element = product.select_one('h2 > a > span')
                if not name_element:
                    continue
                name = name_element.text.strip()
                
                # Extract price
                price_element = product.select_one('span.a-price > span.a-offscreen')
                if not price_element:
                    continue
                
                price_text = price_element.text.strip()
                # Extract numeric price (remove currency symbols, etc.)
                price_match = re.search(r'\$([\d,.]+)', price_text)
                if not price_match:
                    continue
                price = float(price_match.group(1).replace(',', ''))
                
                # Extract product URL
                link_element = product.select_one('h2 > a')
                if not link_element:
                    continue
                
                link = link_element.get('href')
                if link and not link.startswith('http'):
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
                    "site": "AmazonHealth",
                    "rating": rating if rating else 0,
                    "reviews": reviews,
                    "size": "Standard",  # Default size
                    "brand": brand,
                    "flavor": "Unflavored",  # Default flavor
                    "in_stock": True,  # Default to True
                    "region": "Global",
                    "focus": "Global marketplace for supplements"
                })
                
            except Exception as e:
                logger.error(f"Error extracting product data: {str(e)}")
                continue
        
        # Add delay to avoid rate limiting
        add_delay(2, 4)  # Longer delay for Amazon
                
    except requests.exceptions.Timeout:
        logger.error("Request to Amazon Health timed out")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {str(e)}")
        
    return results

# GNC scraper implementation
def scrape_gnc(product_query: str) -> List[Dict[str, Any]]:
    """
    Scrape product information from GNC.
    
    Args:
        product_query: The user's search query for supplements
        
    Returns:
        List of dictionaries containing product information
    """
    logger.info(f"Attempting to scrape GNC for: {product_query}")
    
    results = []
    
    try:
        # Construct search URL
        search_url = f"https://www.gnc.com/search?q={product_query.replace(' ', '+')}"
        
        # Set up headers with random user agent
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.gnc.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Send HTTP request
        logger.debug(f"Sending request to: {search_url}")
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find product containers - adjust selector based on GNC's actual HTML structure
        product_elements = soup.select('div.product-tile')
        
        logger.info(f"Found {len(product_elements)} products on GNC")
        
        # Extract product information
        for product in product_elements:
            try:
                # Extract product name
                name_element = product.select_one('a.product-name')
                if not name_element:
                    continue
                name = name_element.text.strip()
                
                # Extract price
                price_element = product.select_one('span.sales')
                if not price_element:
                    # Try alternative price selector
                    price_element = product.select_one('span.product-sales-price')
                    if not price_element:
                        continue
                
                price_text = price_element.text.strip()
                # Extract numeric price (remove currency symbols, etc.)
                price_match = re.search(r'\$(\d+\.\d+)', price_text)
                if not price_match:
                    continue
                price = float(price_match.group(1).replace(',', ''))
                
                # Extract product URL
                link_element = product.select_one('a.product-name')
                if not link_element:
                    continue
                
                link = link_element.get('href')
                if link and not link.startswith('http'):
                    link = urljoin('https://www.gnc.com', link)
                
                # Extract brand if available
                brand_element = product.select_one('div.product-brand')
                brand = brand_element.text.strip() if brand_element else "GNC"
                
                # Extract rating if available
                rating_element = product.select_one('span.product-rating')
                rating = None
                if rating_element:
                    rating_text = rating_element.get('title', '')
                    rating_match = re.search(r'([\d.]+) out of 5', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Extract review count if available
                reviews_element = product.select_one('span.review-count')
                reviews = 0
                if reviews_element:
                    reviews_text = reviews_element.text.strip().replace('(', '').replace(')', '').replace(',', '')
                    if reviews_text.isdigit():
                        reviews = int(reviews_text)
                
                # Extract size/quantity if available
                size = "Standard"
                size_element = product.select_one('span.product-variant')
                if size_element:
                    size = size_element.text.strip()
                
                # Check if in stock
                in_stock = True  # Default to True
                stock_element = product.select_one('div.availability-msg')
                if stock_element and ('out of stock' in stock_element.text.lower() or 'unavailable' in stock_element.text.lower()):
                    in_stock = False
                
                # Add to results
                results.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "site": "GNC",
                    "rating": rating if rating else 0,
                    "reviews": reviews,
                    "size": size,
                    "brand": brand,
                    "flavor": "Unflavored",  # Default flavor
                    "in_stock": in_stock,
                    "region": "Global",
                    "focus": "Vitamins, protein, and wellness products"
                })
                
            except Exception as e:
                logger.error(f"Error extracting product data from GNC: {str(e)}")
                continue
        
        # Add delay to avoid rate limiting
        add_delay(1.5, 3.5)
                
    except requests.exceptions.Timeout:
        logger.error("Request to GNC timed out")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during scraping GNC: {str(e)}")
        
    return results

# Vitamin Shoppe scraper implementation
def scrape_vitamin_shoppe(product_query: str) -> List[Dict[str, Any]]:
    """
    Scrape product information from Vitamin Shoppe.
    
    Args:
        product_query: The user's search query for supplements
        
    Returns:
        List of dictionaries containing product information
    """
    logger.info(f"Attempting to scrape Vitamin Shoppe for: {product_query}")
    
    results = []
    
    try:
        # Construct search URL
        search_url = f"https://www.vitaminshoppe.com/search?search={product_query.replace(' ', '+')}"
        
        # Set up headers with random user agent
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.vitaminshoppe.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Send HTTP request
        logger.debug(f"Sending request to: {search_url}")
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find product containers - adjust selector based on Vitamin Shoppe's actual HTML structure
        product_elements = soup.select('div.product-listing-item')
        
        logger.info(f"Found {len(product_elements)} products on Vitamin Shoppe")
        
        # Extract product information
        for product in product_elements:
            try:
                # Extract product name
                name_element = product.select_one('a.product-name')
                if not name_element:
                    continue
                name = name_element.text.strip()
                
                # Extract price
                price_element = product.select_one('span.product-price')
                if not price_element:
                    continue
                
                price_text = price_element.text.strip()
                # Extract numeric price (remove currency symbols, etc.)
                price_match = re.search(r'\$(\d+\.\d+)', price_text)
                if not price_match:
                    continue
                price = float(price_match.group(1).replace(',', ''))
                
                # Extract product URL
                link_element = product.select_one('a.product-name')
                if not link_element:
                    continue
                
                link = link_element.get('href')
                if link and not link.startswith('http'):
                    link = urljoin('https://www.vitaminshoppe.com', link)
                
                # Extract brand if available
                brand_element = product.select_one('div.product-brand')
                brand = brand_element.text.strip() if brand_element else "Vitamin Shoppe"
                
                # Extract rating if available
                rating_element = product.select_one('span.rating-value')
                rating = None
                if rating_element:
                    rating_text = rating_element.text.strip()
                    try:
                        rating = float(rating_text)
                    except ValueError:
                        pass
                
                # Extract review count if available
                reviews_element = product.select_one('span.review-count')
                reviews = 0
                if reviews_element:
                    reviews_text = reviews_element.text.strip().replace('(', '').replace(')', '').replace(',', '')
                    if reviews_text.isdigit():
                        reviews = int(reviews_text)
                
                # Extract size/quantity if available
                size = "Standard"
                size_element = product.select_one('span.product-size')
                if size_element:
                    size = size_element.text.strip()
                
                # Check if in stock
                in_stock = True  # Default to True
                stock_element = product.select_one('div.availability')
                if stock_element and ('out of stock' in stock_element.text.lower() or 'unavailable' in stock_element.text.lower()):
                    in_stock = False
                
                # Add to results
                results.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "site": "VitaminShoppe",
                    "rating": rating if rating else 0,
                    "reviews": reviews,
                    "size": size,
                    "brand": brand,
                    "flavor": "Unflavored",  # Default flavor
                    "in_stock": in_stock,
                    "region": "Global",
                    "focus": "Wide-range supplements and wellness solutions"
                })
                
            except Exception as e:
                logger.error(f"Error extracting product data from Vitamin Shoppe: {str(e)}")
                continue
        
        # Add delay to avoid rate limiting
        add_delay(1.5, 3.5)
                
    except requests.exceptions.Timeout:
        logger.error("Request to Vitamin Shoppe timed out")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during scraping Vitamin Shoppe: {str(e)}")
        
    return results

# Dictionary mapping site names to real scraper functions
REAL_SCRAPERS = {
    "iHerb": scrape_iherb,
    "AmazonHealth": scrape_amazon_health,
    "GNC": scrape_gnc,
    "VitaminShoppe": scrape_vitamin_shoppe
}