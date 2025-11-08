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


# Pydantic models for response schema - Frontend compatible
class Veterinarian(BaseModel):
    """Veterinarian information"""

    name: str
    specialties: str
    acceptingNewPatients: bool = False


class BusinessHours(BaseModel):
    """Business hours for each day of the week - simple string format"""

    monday: str = ""
    tuesday: str = ""
    wednesday: str = ""
    thursday: str = ""
    friday: str = ""
    saturday: str = ""
    sunday: str = ""


class ClinicData(BaseModel):
    """Extracted veterinary clinic data - matches frontend form structure exactly"""

    name: str = ""
    phoneNumber: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    website: str = ""
    email: str = ""
    businessHours: BusinessHours = BusinessHours()
    is_24_7: bool = False
    holidayClosures: str = ""
    veterinarians: List[Veterinarian] = []
    practiceManager: str = ""
    headTechnician: str = ""
    servicesOffered: List[str] = []
    servicesNotOffered: str = ""
    speciesTreated: List[str] = []


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
                thinking_config=types.ThinkingConfig(
                    thinking_budget=0
                ),  # Disable thinking
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

Extract all available information about the clinic. The data will be validated against a strict schema and sent directly to a frontend form.

IMPORTANT: Return data in this exact structure - it will populate a form with ZERO transformation.

INSTRUCTIONS:
1. name: Extract the full business name of the veterinary clinic (string)
   - If none found, return empty string ""

2. phoneNumbers: Extract ALL phone numbers as a comma-separated string
   - Format: "(555) 123-4567, (555) 123-4568" or "(555) 123-4567"
   - If multiple numbers, separate with comma and space
   - If none found, return empty string ""

3. address: Extract the primary street address only (string)
   - Format: "123 Oak Street" (street number and name only)
   - If none found, return empty string ""

4. city: Extract the city name (string)
   - If none found, return empty string ""

5. state: Extract the state name or abbreviation (string)
   - If none found, return empty string ""

6. pincode: Extract the ZIP/postal code (string)
   - If none found, return empty string ""

7. website: Extract the clinic's website URL (string)
   - If none found, return empty string ""

8. email Extract one or more email address

9. businessHours: Extract business hours as a simple object with day keys
   - Format: Simple strings like "8:00 AM - 6:00 PM", "Closed", or "24/7"
   - Structure:
     {
       "monday": "8:00 AM - 6:00 PM",
       "tuesday": "8:00 AM - 6:00 PM",
       "wednesday": "8:00 AM - 6:00 PM",
       "thursday": "8:00 AM - 6:00 PM",
       "friday": "8:00 AM - 6:00 PM",
       "saturday": "9:00 AM - 2:00 PM",
       "sunday": "Closed"
     }
   - If hours not found for a day, use empty string ""
   - If clinic is 24/7, still populate hours (frontend will handle is_24_7 flag)

10. is_24_7: Set to true if clinic operates 24/7, otherwise false (boolean)
    - Default: false

11. holidayClosures: Extract information about holiday closures (string)
    - Format: "Closed for Thanksgiving (Nov 28). Closed at 12 PM on Christmas Eve (Dec 24)."
    - If none found, return empty string ""

12. veterinarians: Extract ALL veterinarians as an array of objects
    - Structure: {"name": "Dr. Name, DVM", "specialties": "Area of expertise", "acceptingNewPatients": true/false}
    - acceptingNewPatients defaults to false if not specified
    - If none found, return empty array []

13. practiceManager: Extract the practice manager's name (string)
    - If none found, return empty string ""

14. headTechnician: Extract the head technician's name and credentials (string)
    - Format: "Name, CVT" or "Name, LVT"
    - If none found, return empty string ""

15. servicesOffered: Extract ALL services offered as an array of strings
    - Format: ["Service 1", "Service 2", "Service 3"]
    - If none found, return empty array []

16. servicesNotOffered: Extract services explicitly NOT offered (string)
    - Format: "Boarding, Grooming, Mobile veterinary visits"
    - Comma-separated if multiple
    - If none found, return empty string ""

17. speciesTreated: Extract ALL species/animal types treated as an array of strings
    - Format: ["Dogs", "Cats", "Rabbits", "Birds"]
    - If none found, return empty array []

EMPTY VALUES STRATEGY:
- Arrays: Use empty array [] if no data found
- Strings: Use empty string "" if no data found
- Booleans: Use false as default
- businessHours object: Return full structure with empty strings for each day if no data found

Only include information explicitly stated on the website.
Be thorough and accurate.

Website content:"""
