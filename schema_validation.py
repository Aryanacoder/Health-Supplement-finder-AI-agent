from pydantic import BaseModel, Field, validator, HttpUrl, constr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

class ProductSchema(BaseModel):
    """Enhanced schema for product data validation"""
    # Required fields
    name: constr(min_length=2, max_length=500) = Field(..., description="Product name")
    price: float = Field(..., ge=0, description="Product price")
    url: HttpUrl = Field(..., description="Product URL")
    site: str = Field(..., description="Source website name")
    
    # Optional fields with defaults
    rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Product rating (0-5)")
    reviews: int = Field(default=0, ge=0, description="Number of reviews")
    size: str = Field(default="Standard", description="Product size/weight")
    brand: str = Field(default="Unknown", description="Product brand name")
    flavor: str = Field(default="Unflavored", description="Product flavor")
    in_stock: bool = Field(default=True, description="Whether product is in stock")
    region: str = Field(default="Global", description="Region/country availability")
    focus: Optional[str] = Field(default=None, description="Product focus/category")
    currency: str = Field(default="USD", description="Price currency")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp of data collection")
    
    # Additional fields for enhanced data
    ingredients: Optional[List[str]] = Field(default=None, description="List of ingredients")
    image_url: Optional[HttpUrl] = Field(default=None, description="Product image URL")
    discount_percentage: Optional[float] = Field(default=None, ge=0, le=100, description="Discount percentage")
    original_price: Optional[float] = Field(default=None, ge=0, description="Original price before discount")
    availability: Optional[str] = Field(default="In Stock", description="Availability status")
    shipping_info: Optional[str] = Field(default=None, description="Shipping information")
    seller: Optional[str] = Field(default=None, description="Seller or vendor name")
    product_id: Optional[str] = Field(default=None, description="Product identifier")
    
    @validator('name')
    def validate_name(cls, v):
        # Check for suspicious patterns in product names
        suspicious_patterns = ['[DELETED]', 'SAMPLE', 'TEST PRODUCT', 'DO NOT BUY']
        for pattern in suspicious_patterns:
            if pattern.lower() in v.lower():
                raise ValueError(f"Product name contains suspicious pattern: {pattern}")
        return v
    
    @validator('price')
    def validate_price(cls, v):
        # Additional validation for price
        if v > 10000:
            logger.warning(f"Unusually high price detected: ${v}")
        return v
    
    @validator('url')
    def validate_url(cls, v):
        # Check for suspicious URLs
        suspicious_domains = ['example.com', 'test.com', 'sample.com']
        for domain in suspicious_domains:
            if domain in str(v):
                raise ValueError(f"URL contains suspicious domain: {domain}")
        return v

def validate_product(product_data):
    """Validate product data against the schema"""
    try:
        # Create a ProductSchema instance and validate
        validated = ProductSchema(**product_data).dict()
        logger.info(f"Successfully validated product: {validated['name']}")
        return validated
    except Exception as e:
        # Log detailed error information
        product_name = product_data.get('name', 'Unknown product')
        logger.error(f"Validation error for product '{product_name}': {str(e)}")
        
        # Try to provide more specific error information based on the error message
        error_str = str(e).lower()
        if 'url' in error_str:
            logger.error(f"URL validation failed: {product_data.get('url', 'No URL provided')}")
        elif 'price' in error_str:
            logger.error(f"Price validation failed: {product_data.get('price', 'No price provided')}")
        elif 'name' in error_str:
            logger.error(f"Name validation failed: {product_data.get('name', 'No name provided')}")
        elif 'rating' in error_str:
            logger.error(f"Rating validation failed: {product_data.get('rating', 'No rating provided')}")
        elif 'reviews' in error_str:
            logger.error(f"Reviews validation failed: {product_data.get('reviews', 'No reviews provided')}")
        elif 'ingredients' in error_str:
            logger.error(f"Ingredients validation failed: {product_data.get('ingredients', 'No ingredients provided')}")
        
        # Attempt to fix common issues and revalidate
        try:
            fixed_data = fix_common_validation_issues(product_data, error_str)
            if fixed_data:
                logger.info(f"Attempting revalidation after fixing issues for: {product_name}")
                return validate_product(fixed_data)  # Recursive call with fixed data
        except Exception as fix_error:
            logger.debug(f"Could not fix validation issues: {str(fix_error)}")
        
        # Return None for invalid products
        return None

def fix_common_validation_issues(product_data, error_message):
    """Attempt to fix common validation issues in product data
    
    Args:
        product_data: The product data dictionary
        error_message: The error message from validation
        
    Returns:
        Fixed product data dictionary or None if unfixable
    """
    fixed_data = product_data.copy()
    
    # Fix URL issues
    if 'url' in error_message and 'url' in fixed_data:
        url = fixed_data['url']
        # Convert HttpUrl to string if needed
        url_str = str(url)
        # Add https:// if missing
        if not url_str.startswith(('http://', 'https://')):
            fixed_data['url'] = 'https://' + url_str.lstrip('/')
        # Remove query parameters if causing issues
        if '?' in url and ('invalid' in error_message or 'not a valid' in error_message):
            fixed_data['url'] = url.split('?')[0]
    
    # Fix price issues
    if 'price' in error_message and 'price' in fixed_data:
        try:
            # Extract numeric value if price contains currency symbols or commas
            price_str = str(fixed_data['price'])
            # Remove currency symbols and commas
            price_str = ''.join(c for c in price_str if c.isdigit() or c == '.' or c == ',')
            price_str = price_str.replace(',', '')
            fixed_data['price'] = float(price_str)
        except (ValueError, TypeError):
            # If conversion fails, set a default price
            fixed_data['price'] = 0.0
    
    # Fix rating issues
    if 'rating' in error_message and 'rating' in fixed_data:
        try:
            rating = float(fixed_data['rating'])
            # Ensure rating is within valid range
            fixed_data['rating'] = max(0.0, min(5.0, rating))
        except (ValueError, TypeError):
            fixed_data['rating'] = 0.0
    
    # Fix reviews count issues
    if 'reviews' in error_message and 'reviews' in fixed_data:
        try:
            # Extract numeric value if reviews contains non-numeric characters
            reviews_str = str(fixed_data['reviews'])
            reviews_str = ''.join(c for c in reviews_str if c.isdigit())
            fixed_data['reviews'] = int(reviews_str) if reviews_str else 0
        except (ValueError, TypeError):
            fixed_data['reviews'] = 0
    
    # Fix name issues
    if 'name' in error_message and 'name' in fixed_data:
        name = fixed_data['name']
        # Ensure name meets minimum length
        if len(name) < 2:
            fixed_data['name'] = name + ' Supplement'
        # Truncate if too long
        if len(name) > 500:
            fixed_data['name'] = name[:497] + '...'
    
    return fixed_data

def validate_products(products_data):
    """Validate a list of products"""
    if not products_data:
        logger.warning("No products to validate")
        return []
    
    validated = []
    invalid_count = 0
    fixed_count = 0
    validation_stats = {}
    
    for product in products_data:
        site = product.get('site', 'Unknown')
        if site not in validation_stats:
            validation_stats[site] = {'total': 0, 'valid': 0, 'invalid': 0, 'fixed': 0}
        
        validation_stats[site]['total'] += 1
        
        # Track original product state for comparison
        original_product = product.copy()
        valid_product = validate_product(product)
        
        if valid_product:
            validated.append(valid_product)
            validation_stats[site]['valid'] += 1
            
            # Check if product was fixed during validation
            if original_product != valid_product:
                fixed_count += 1
                validation_stats[site]['fixed'] += 1
        else:
            invalid_count += 1
            validation_stats[site]['invalid'] += 1
    
    # Log validation summary
    total = len(products_data)
    valid_count = len(validated)
    
    # Overall summary
    logger.info(f"Validation summary: {valid_count}/{total} products valid ({invalid_count} invalid, {fixed_count} fixed)")
    
    # Per-site summary
    for site, stats in validation_stats.items():
        logger.info(f"Site '{site}' validation: {stats['valid']}/{stats['total']} valid, {stats['fixed']} fixed, {stats['invalid']} invalid")
    
    return validated