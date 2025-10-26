"""
Scraper Routes - Web scraping and data extraction endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from helpers.scraperHelper import deep_crawl_website
from helpers.geminiHelper import (
    extract_clinic_data, 
    get_gemini_client,
    ClinicData,
    StaffMember,
    FAQ,
    BusinessHours
)
from helpers.loggerHelper import get_logger
import re

logger = get_logger(__name__)

router = APIRouter(prefix="/scraper", tags=["scraper"])


class ScrapeRequest(BaseModel):
    """Request model for scraping a website"""

    url: str = Field(
        ...,
        description="Base URL of the website to crawl",
        example="https://example-vet-clinic.com",
    )
    max_depth: Optional[int] = Field(
        default=3,
        description="Maximum depth to crawl (None for unlimited)",
        ge=1,
        le=10,
    )
    max_pages: Optional[int] = Field(
        default=50, description="Maximum number of pages to crawl", ge=1, le=200
    )

    @validator("url")
    def validate_url(cls, v):
        """Validate URL format"""
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        if not url_pattern.match(v):
            raise ValueError("Invalid URL format. Must start with http:// or https://")
        return v


class ScrapeResponse(BaseModel):
    """Response model for scraping results"""

    success: bool = Field(..., description="Whether the scraping was successful")
    url: str = Field(..., description="The URL that was crawled")
    pages_crawled: int = Field(..., description="Number of pages successfully crawled")
    data: Optional[ClinicData] = Field(
        None, description="Extracted clinic data (null if extraction failed)"
    )
    error: Optional[str] = Field(None, description="Error message if unsuccessful")




@router.post("/crawl", response_model=ScrapeResponse)
async def crawl_and_extract(request: ScrapeRequest):
    """
    Crawl a veterinary clinic website and extract structured data.

    This endpoint:
    1. Deep crawls the provided website URL
    2. Extracts clean content from all pages
    3. Uses Gemini AI to extract structured clinic information
    4. Returns comprehensive clinic data

    The extraction includes:
    - Business name, phone, address, email
    - Business hours
    - Services offered
    - Staff information
    - FAQs
    - Policies
    - Additional information
    """
    logger.info(f"POST /v1/scraper/crawl - Crawling {request.url}")

    try:
        # Initialize Gemini client early to catch API key issues
        try:
            gemini_client = get_gemini_client()
        except ValueError as e:
            raise HTTPException(
                status_code=500, detail=f"Gemini API configuration error: {str(e)}"
            )

        # Step 1: Crawl the website
        try:
            pages_data = await deep_crawl_website(
                url=request.url, max_depth=request.max_depth, max_pages=request.max_pages
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid URL: {str(e)}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Crawling failed: {str(e)}"
            )

        if not pages_data:
            return ScrapeResponse(
                success=False,
                url=request.url,
                pages_crawled=0,
                data=None,
                error="No content found on the website",
            )

        logger.info(f"Successfully crawled {len(pages_data)} pages")

        # Step 2: Extract structured data using Gemini
        try:
            clinic_data = await extract_clinic_data(pages_data, gemini_client)
        except Exception as e:
            # Return crawled pages count but indicate extraction failed
            return ScrapeResponse(
                success=False,
                url=request.url,
                pages_crawled=len(pages_data),
                data=None,
                error=f"Data extraction failed: {str(e)}",
            )
        
        # Step 3: Return results
        # clinic_data is already a ClinicData Pydantic model
        
        # Log extracted data to console
        logger.info("="*80)
        logger.info("EXTRACTED CLINIC DATA:")
        logger.info("="*80)
        logger.info(f"Name: {clinic_data.name}")
        logger.info(f"Phone: {clinic_data.phone}")
        logger.info(f"Email: {clinic_data.email}")
        logger.info(f"Address: {clinic_data.address}")
        logger.info(f"Business Hours: {clinic_data.business_hours}")
        logger.info(f"Services: {clinic_data.services}")
        logger.info(f"Staff: {clinic_data.staff}")
        logger.info(f"FAQs: {clinic_data.faqs}")
        logger.info(f"Policies: {clinic_data.policies}")
        logger.info(f"Additional Info: {clinic_data.additional_info}")
        logger.info("="*80)

        return ScrapeResponse(
            success=True,
            url=request.url,
            pages_crawled=len(pages_data),
            data=clinic_data,
            error=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in crawl_and_extract: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}"
        )


@router.get("/health")
async def scraper_health():
    """Health check endpoint for scraper service"""
    return {"status": "healthy", "service": "scraper"}

