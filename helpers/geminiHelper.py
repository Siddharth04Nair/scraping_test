"""
Gemini Helper - Integration with Google Gemini API for data extraction
"""

from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel
from helpers.envHelper import settings
from helpers.loggerHelper import get_logger

logger = get_logger(__name__)


GEMINI_MODEL = "gemini-2.5-flash"


# Pydantic models for response schema
class StaffMember(BaseModel):
    """Staff member information"""
    name: str
    role: str
    specialization: Optional[str] = None
    bio: Optional[str] = None


class FAQ(BaseModel):
    """FAQ item"""
    question: str
    answer: str


class BusinessHours(BaseModel):
    """Business hours for each day of the week"""
    monday: Optional[str] = None
    tuesday: Optional[str] = None
    wednesday: Optional[str] = None
    thursday: Optional[str] = None
    friday: Optional[str] = None
    saturday: Optional[str] = None
    sunday: Optional[str] = None


class ClinicData(BaseModel):
    """Extracted veterinary clinic data"""
    name: Optional[str] = None
    phone: Optional[str | List[str]] = None
    address: Optional[str] = None
    email: Optional[str | List[str]] = None
    business_hours: Optional[BusinessHours | str] = None
    services: Optional[List[str]] = None
    staff: Optional[List[StaffMember]] = None
    faqs: Optional[List[FAQ]] = None
    policies: Optional[str | List[str]] = None
    additional_info: Optional[str] = None


def get_gemini_client() -> genai.Client:
    """
    Get initialized Gemini client

    Returns:
        Configured Gemini client

    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    api_key = settings.gemini_api_key
    if not api_key:
        raise ValueError(
            "Gemini API key is required. Set GEMINI_API_KEY environment variable."
        )
    return genai.Client(api_key=api_key)


async def extract_clinic_data(
    pages_data: List[Dict[str, str]], client: Optional[genai.Client] = None
) -> ClinicData:
    """
    Extract structured veterinary clinic data from crawled pages using Gemini.

    Args:
        pages_data: List of dicts with 'url' and 'content' keys
        client: Optional pre-initialized Gemini client

    Returns:
        ClinicData model with extracted clinic information
    """
    if client is None:
        client = get_gemini_client()

    # Prepare content for Gemini
    combined_content = _prepare_content_for_extraction(pages_data)

    # Create extraction prompt
    prompt = _build_extraction_prompt()

    try:
        # Call Gemini API with response schema (asynchronously)
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"{prompt}\n\n{combined_content}",
            config=types.GenerateContentConfig(
                temperature=0,  
                response_mime_type="application/json",
                response_schema=ClinicData,  # Use Pydantic model for response schema
                thinking_config=types.ThinkingConfig(thinking_budget=0),  # Disable thinking
            ),
        )

        # Use parsed response - Gemini automatically validates against schema
        extracted_data: ClinicData = response.parsed
        return extracted_data

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        # Return empty ClinicData model on error
        return ClinicData()


def _prepare_content_for_extraction(pages_data: List[Dict[str, str]]) -> str:
    """
    Prepare crawled page content for extraction.

    Args:
        pages_data: List of dicts with 'url' and 'content' keys

    Returns:
        Combined formatted content string
    """
    # Limit content to avoid token limits (roughly 800k characters for Gemini 2.0)
    max_chars_per_page = 50000
    max_total_chars = 500000

    formatted_pages = []
    total_chars = 0

    for page in pages_data:
        url = page.get("url", "Unknown URL")
        content = page.get("content", "")

        # Skip empty pages
        if not content.strip():
            continue

        # Truncate very long pages
        if len(content) > max_chars_per_page:
            content = content[:max_chars_per_page] + "\n...[content truncated]"

        page_text = f"--- PAGE: {url} ---\n{content}\n\n"

        # Check if adding this page would exceed total limit
        if total_chars + len(page_text) > max_total_chars:
            break

        formatted_pages.append(page_text)
        total_chars += len(page_text)

    return "".join(formatted_pages)


def _build_extraction_prompt() -> str:
    """
    Build the extraction prompt for Gemini.

    Returns:
        Structured prompt string
    """
    return """You are a data extraction specialist. Extract structured information about a veterinary clinic from the provided website content.

Extract all available information about the clinic. The data will be validated against a strict schema.

INSTRUCTIONS:
1. Extract the full business name of the veterinary clinic
2. Extract phone numbers (can be a single string or list of strings if multiple)
3. Extract the full street address including city, state, and zip code
4. Extract email addresses (can be a single string or list of strings if multiple)
5. Extract business hours for each day of the week (monday through sunday)
   - Try to structure as separate fields for each day
   - If only text description is available, provide it as a string
6. Extract all services offered (as a list)
7. Extract all staff members with their name, role, specialization, and bio if available
8. Extract FAQs with questions and answers
9. Extract policies (can be a single string or list of strings)
10. Extract any additional relevant information (parking, accessibility, languages spoken, etc.)

If a field is not found on the website, omit it or use null.
Only include information explicitly stated on the website.
Be thorough and accurate.

Website content:"""

