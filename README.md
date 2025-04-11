# AI-Powered Health Supplement Price Comparison Agent

This project is an AI-powered health supplement price comparison tool that allows users to query for health supplements and find the best prices across multiple e-commerce sites.

## Features

- Natural language understanding of supplement queries
- Real-time web scraping of supplement e-commerce sites
- Price comparison across multiple sources
- Interactive web UI built with Streamlit
- Conversation history and basic memory system
- Markdown comparison tables sorted by price

## Project Structure

```
├── agent.py          # LangChain agent implementation
├── api.py            # FastAPI backend
├── main_ui.py        # Streamlit frontend
├── memory.py         # TinyDB-based interaction history
├── scraper.py        # Web scraping functionality
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment variables
└── data/             # Directory for storing interaction data
    └── user_interactions.json  # TinyDB database file
```

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- A Hugging Face account and API token

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd supp_ai
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the provided `.env.example`:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file and add your Hugging Face API token:
   ```
   HUGGINGFACEHUB_API_TOKEN=your_token_here
   ```

### Running the Application

1. Start the FastAPI backend:
   ```
   uvicorn api:app --reload
   ```

2. In a separate terminal, start the Streamlit frontend:
   ```
   streamlit run main_ui.py
   ```

3. Open your browser and navigate to http://localhost:8501 to use the application.

## Usage

1. Enter a specific supplement query in the search box, such as:
   - "cheapest whey protein chocolate 5lb"
   - "where to find creatine monohydrate 500g"
   - "best price for fish oil capsules"

2. The AI agent will process your query, search for supplements, and return a comparison of prices.

3. Results will be displayed as a conversational response along with a price comparison table.

## Important Notes

- The example scrapers provided are for demonstration purposes only.
- The simulated scraper returns realistic but fictional data for testing purposes.
- Real website scrapers have been implemented for iHerb, Amazon Health, GNC, and Vitamin Shoppe.
- Web scraping may be subject to legal restrictions and website terms of service. Always ensure you have permission to scrape a website before doing so.
- The real scrapers implement rate limiting and user-agent rotation to minimize impact on the target websites.
- Some websites may block scraping attempts or change their HTML structure, which could cause the scrapers to stop working.
- The system includes robust error handling to gracefully manage failed scraping attempts without crashing.

## Customization

### Adding New Scrapers

To add a new scraper for a specific supplement site:

1. Create a new scraper function in `real_scrapers.py`
2. Add the site configuration to the `SITE_CONFIG` dictionary in `scraper.py`
3. Register the scraper in the `REAL_SCRAPERS` dictionary in `real_scrapers.py`

### Using Real Website Scrapers

The application now includes real website scrapers for iHerb, Amazon Health, GNC, and Vitamin Shoppe. Here's what you need to know:

1. **Legal Considerations**: Before using the real scrapers, ensure you're complying with the website's terms of service and robots.txt file. Many websites prohibit scraping or have specific limitations.

2. **Rate Limiting**: The real scrapers include built-in delays between requests to avoid overwhelming the target websites. This helps prevent your IP from being blocked. Each scraper implements site-specific delays (1-3 seconds for iHerb, 2-4 seconds for Amazon, 1.5-3.5 seconds for GNC and Vitamin Shoppe).

3. **User-Agent Rotation**: The scrapers rotate between different user-agent strings to mimic different browsers, which helps avoid detection. The system includes a diverse set of user agents representing various browsers and operating systems.

4. **Error Handling**: All scrapers implement comprehensive error handling for common issues like timeouts, HTTP errors, and parsing failures. This ensures the application continues to function even if one scraper fails.

5. **Troubleshooting**: If a scraper stops working, it's likely because the website has changed its HTML structure. You'll need to update the CSS selectors in the `SITE_CONFIG` dictionary and possibly modify the scraper function.

6. **Adding More Real Scrapers**: To add more real website scrapers, follow the pattern in `real_scrapers.py`. Each scraper function should handle errors gracefully and return results in the same format as the existing scrapers.

### Anti-Scraping Measures

Be aware that websites may employ various anti-scraping techniques:

- CAPTCHA challenges
- IP-based rate limiting
- JavaScript-rendered content (which requires a headless browser like Selenium or Playwright)
- Dynamic CSS class names
- Header and cookie verification
- Request pattern detection

Our implementation includes the following countermeasures:

- **Randomized delays**: Each scraper uses variable wait times between requests to avoid detection
- **User-agent rotation**: Requests use different browser identifiers to appear as different users
- **Robust error handling**: Graceful recovery from timeouts, blocks, and parsing errors
- **Selective scraping**: Only essential product data is extracted to minimize request footprint
- **Fallback mechanisms**: If a real scraper fails, the system can use simulated data

For more robust scraping, consider using dedicated scraping libraries or services like Scrapy, Selenium, or commercial API services that provide structured data from websites.

### Changing the LLM Model

To use a different Hugging Face model:

1. Open `agent.py`
2. Modify the `repo_id` parameter in the `HuggingFaceEndpoint` initialization

## License

[MIT License](LICENSE)