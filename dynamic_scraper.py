import logging
import time
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Import utility functions
from scraper_utils import (
    get_random_user_agent,
    update_success_rate,
    update_response_time,
    send_alert,
    normalize_data
)

logger = logging.getLogger(__name__)

def get_headless_driver(browser_type="chrome"):
    """
    Create and configure a headless browser driver.
    
    Args:
        browser_type: Type of browser to use (chrome or firefox)
        
    Returns:
        Configured WebDriver instance
    """
    if browser_type.lower() == "chrome":
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--user-agent={get_random_user_agent()}")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        return webdriver.Chrome(options=options)
    elif browser_type.lower() == "firefox":
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument(f"--user-agent={get_random_user_agent()}")
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        return webdriver.Firefox(options=options)
    else:
        raise ValueError(f"Unsupported browser type: {browser_type}")

def wait_for_element(driver, selector, timeout=10):
    """
    Wait for an element to be present on the page.
    
    Args:
        driver: WebDriver instance
        selector: CSS selector for the element
        timeout: Maximum time to wait in seconds
        
    Returns:
        The element if found, None otherwise
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element
    except Exception as e:
        logger.error(f"Timeout waiting for element {selector}: {str(e)}")
        return None

class DynamicScraper:
    """
    Scraper for JavaScript-heavy websites using Selenium.
    """
    
    def __init__(self, site_config):
        self.config = site_config
        self.site_name = site_config.get("site_name", "Unknown")
        self.timeout = site_config.get("timeout", 30)  # Longer timeout for JS rendering
        self.browser_type = site_config.get("browser", "chrome")
        
    def scrape(self, product_query):
        """
        Scrape a dynamic website using Selenium.
        
        Args:
            product_query: The product query to search for
            
        Returns:
            List of product information dictionaries
        """
        driver = None
        results = []
        start_time = time.time()
        
        # Import schema validation
        from schema_validation import validate_products
        
        try:
            # Initialize the driver
            driver = get_headless_driver(self.browser_type)
            
            # Set page load timeout
            driver.set_page_load_timeout(self.timeout)
            
            # Build search URL
            base_url = self.config["base_url"]
            search_param = self.config["search_param"]
            search_url = f"{base_url}?{search_param}={product_query.replace(' ', '+')}"            
            
            # Navigate to the search page
            logger.info(f"Navigating to {search_url} with {self.browser_type} browser")
            driver.get(search_url)
            
            # Wait for the product container to load
            product_selector = self.config.get("product_selector")
            if not product_selector:
                logger.error(f"No product selector configured for {self.site_name}")
                return []
                
            # Wait for products to load
            wait_for_element(driver, product_selector, self.timeout)
            
            # Get the page source after JavaScript has rendered
            page_source = driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Extract products
            product_elements = soup.select(product_selector)
            logger.info(f"Found {len(product_elements)} products on {self.site_name}")
            
            # Extract product information based on selectors
            for product in product_elements:
                try:
                    # Extract product name
                    name_selector = self.config.get("name_selector")
                    if not name_selector:
                        continue
                        
                    name_element = product.select_one(name_selector)
                    if not name_element:
                        continue
                    name = name_element.text.strip()
                    
                    # Extract price
                    price_selector = self.config.get("price_selector")
                    if not price_selector:
                        continue
                        
                    price_element = product.select_one(price_selector)
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
                    link_selector = self.config.get("link_selector")
                    if not link_selector:
                        continue
                        
                    link_element = product.select_one(link_selector)
                    if not link_element:
                        continue
                    
                    link = link_element.get('href')
                    if link and not link.startswith('http'):
                        from urllib.parse import urljoin
                        link = urljoin(base_url, link)
                    
                    # Add to results
                    results.append({
                        "name": name,
                        "price": price,
                        "url": link,
                        "site": self.site_name,
                        "rating": 0,  # Default values
                        "reviews": 0,
                        "size": "Standard",
                        "brand": "Unknown",
                        "flavor": "Unflavored",
                        "in_stock": True,
                        "region": self.config.get("region", "Global"),
                        "focus": self.config.get("focus", "")
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting product data: {str(e)}")
                    continue
            
            # Update metrics
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            update_response_time(self.site_name, elapsed_time)
            update_success_rate(self.site_name, True)
            
            # Normalize data
            return normalize_data(results)
            
        except Exception as e:
            logger.error(f"Error during dynamic scraping of {self.site_name}: {str(e)}")
            update_success_rate(self.site_name, False)
            send_alert(self.site_name, str(e))
            return []
            
        finally:
            # Always close the driver to free resources
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.error(f"Error closing WebDriver: {str(e)}")

# Factory function to create a dynamic scraper
def create_dynamic_scraper(site_name, site_config):
    """
    Create a dynamic scraper for JavaScript-heavy sites.
    
    Args:
        site_name: Name of the site
        site_config: Configuration for the site
        
    Returns:
        Configured DynamicScraper instance
    """
    # Add site name to config
    config = site_config.copy()
    config["site_name"] = site_name
    
    return DynamicScraper(config)