# Veterinary Clinic Scraper API

A FastAPI server with web scraping capabilities for extracting structured data from veterinary clinic websites using Crawl4AI and Google Gemini AI.

## Project Structure

- **main.py**: Application entry point
- **routes/**: API route handlers
  - **scraper.py**: Web scraping and data extraction endpoints
  - **hello.py**: Simple hello endpoint
- **helpers/**: Utility functions
  - **scraperHelper.py**: Crawl4AI integration for web crawling
  - **geminiHelper.py**: Google Gemini AI integration for data extraction
  - **envHelper.py**: Environment configuration utilities

## Requirements

- Python 3.13 (or compatible version)
- pip
- Google Gemini API key

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment:

Create a `.env` file in the root directory (you can use `.env.example` as a template):

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8080

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
```

Replace `your_gemini_api_key_here` with your actual Google Gemini API key.

**Note**: The application uses **Pydantic BaseSettings** for type-safe configuration management. All environment variables are automatically loaded from the `.env` file and validated at startup.

3. Run the server:

```bash
python main.py
```

## API Endpoints

### Root

- `GET /`: Basic health check
  - Returns: `{"message": "Simple API is running"}`

### Hello Endpoint

- `GET /v1/hello`: Hello endpoint
  - Returns: `{"message": "Hello"}`
  - Also prints "Hello endpoint called" to console

### Scraper Endpoints

#### Crawl and Extract Data

- `POST /v1/scraper/crawl`: Crawl a veterinary clinic website and extract structured data
  - **Request Body:**
    ```json
    {
      "url": "https://example-vet-clinic.com",
      "max_depth": 3,
      "max_pages": 50
    }
    ```
  - **Parameters:**
    - `url` (required): Base URL of the website to crawl
    - `max_depth` (optional): Maximum crawl depth (1-10, default: 3)
    - `max_pages` (optional): Maximum pages to crawl (1-200, default: 50)
  
  - **Response:**
    ```json
    {
      "success": true,
      "url": "https://example-vet-clinic.com",
      "pages_crawled": 15,
      "data": {
        "name": "Example Veterinary Clinic",
        "phone": "555-1234",
        "address": "123 Main St, City, ST 12345",
        "email": "info@example-vet.com",
        "business_hours": {
          "monday": "9:00 AM - 5:00 PM",
          "tuesday": "9:00 AM - 5:00 PM",
          "wednesday": "9:00 AM - 5:00 PM",
          "thursday": "9:00 AM - 5:00 PM",
          "friday": "9:00 AM - 5:00 PM",
          "saturday": "10:00 AM - 2:00 PM",
          "sunday": "Closed"
        },
        "services": ["Wellness Exams", "Surgery", "Dental Care"],
        "staff": [
          {
            "name": "Dr. Jane Smith",
            "role": "Veterinarian",
            "specialization": "Surgery",
            "bio": "10 years experience..."
          }
        ],
        "faqs": [
          {
            "question": "What are your payment options?",
            "answer": "We accept cash, credit cards..."
          }
        ],
        "policies": "Appointment cancellation policy...",
        "additional_info": "Free parking available"
      },
      "error": null
    }
    ```

#### Health Check

- `GET /v1/scraper/health`: Scraper service health check
  - Returns: `{"status": "healthy", "service": "scraper"}`

## Testing

Once the server is running, test the endpoints:

1. Root endpoint:

```bash
curl http://localhost:8080/
```

2. Hello endpoint:

```bash
curl http://localhost:8080/v1/hello
```

3. Scraper endpoint:

```bash
curl -X POST http://localhost:8080/v1/scraper/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example-vet-clinic.com", "max_depth": 3, "max_pages": 50}'
```

Or visit the interactive API documentation:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## Features

### Web Scraping
- **Deep crawling** using Crawl4AI with breadth-first search strategy
- Configurable crawl depth and page limits
- Automatic filtering of non-content pages (CSS, JS, images, etc.)
- Stays within the same domain
- Extracts clean markdown content

### AI-Powered Data Extraction
- Uses **Google Gemini 2.0 Flash** for intelligent data extraction
- Extracts structured information:
  - Business name, contact info (phone, email, address)
  - Business hours (structured by day)
  - Services offered
  - Staff members with roles and specializations
  - FAQs
  - Policies (payment, appointment, emergency)
  - Additional information

### Cost Optimization
- Markdown format extraction (fewer tokens than HTML)
- Content truncation to stay within token limits
- Automatic skipping of non-content pages
- Low temperature for consistent extraction results

## Development

The server uses:

- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **Crawl4AI**: Advanced web crawling library
- **Google Gemini AI**: AI-powered data extraction
- **Pydantic**: Data validation and settings management with BaseSettings
- **pydantic-settings**: Type-safe environment variable loading

## Error Handling

The API includes comprehensive error handling for:
- Invalid URLs
- Crawling failures (timeouts, connection errors)
- Missing or invalid API keys
- Content extraction failures
- Empty or insufficient website content

All errors return appropriate HTTP status codes and descriptive error messages.
