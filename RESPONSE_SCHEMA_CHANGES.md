# Response Schema Implementation

## Overview
Updated the codebase to use Google GenAI's response schema feature with Pydantic models for structured, type-safe responses.

## Changes Made

### 1. `helpers/geminiHelper.py`

**Added Pydantic Models:**
- `StaffMember`: Staff member information with name, role, specialization, and bio
- `FAQ`: FAQ items with question and answer
- `BusinessHours`: Business hours for each day of the week
- `ClinicData`: Main clinic data model with all extracted information

**Updated `extract_clinic_data()` function:**
- **Before**: Returned `Dict[str, Any]` and manually parsed JSON with `json.loads()`
- **After**: Returns `ClinicData` Pydantic model and uses `response.parsed`
- Added `response_schema=ClinicData` to the config
- Automatic validation against the schema
- Better error handling with empty `ClinicData()` on errors

**Key Benefits:**
```python
# Old way (manual parsing)
response = await client.aio.models.generate_content(...)
extracted_data = json.loads(response.text)  # Manual parsing, no validation

# New way (with response schema)
response = await client.aio.models.generate_content(
    config={
        "response_mime_type": "application/json",
        "response_schema": ClinicData,  # Pydantic model
    }
)
extracted_data: ClinicData = response.parsed  # Automatic parsing & validation
```

### 2. `routes/scraper.py`

**Updated imports:**
- Import Pydantic models from `geminiHelper` instead of defining them locally
- Removed duplicate model definitions

**Simplified data handling:**
- `extract_clinic_data()` now directly returns a `ClinicData` model
- No need to convert dictionaries to Pydantic models manually

## Benefits of Response Schema

### 1. **Type Safety**
- Pydantic models provide automatic type validation
- IDE autocomplete and type hints work properly
- Catch type errors at development time

### 2. **Automatic Parsing**
- No need for manual `json.loads()` and error handling
- GenAI validates the response against the schema
- Get parsed objects directly with `response.parsed`

### 3. **Better Error Handling**
- Schema validation happens on the GenAI side
- Guaranteed structure of the response
- Easier to debug when extraction fails

### 4. **Cleaner Code**
- No need for `_get_empty_clinic_data()` helper
- Direct instantiation with `ClinicData()`
- Less boilerplate code

### 5. **Documentation**
- Pydantic models serve as documentation
- Clear field types and optional/required fields
- Easy to understand the data structure

## Usage Example

See `example_response_schema.py` for a complete example:

```python
from google import genai
from pydantic import BaseModel

class Recipe(BaseModel):
    recipe_name: str
    ingredients: list[str]

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents="List a few popular cookie recipes.",
    config={
        "response_mime_type": "application/json",
        "response_schema": list[Recipe],  # Use Pydantic model
    },
)

# Get parsed objects directly
my_recipes: list[Recipe] = response.parsed
for recipe in my_recipes:
    print(f"{recipe.recipe_name}: {recipe.ingredients}")
```

## How It Works

1. **Define Pydantic Models**: Create models that represent your desired data structure
2. **Pass to Config**: Add `response_schema` parameter to the generation config
3. **Get Parsed Results**: Access validated objects via `response.parsed`

## Migration Guide

### Old Code:
```python
response = await client.aio.models.generate_content(
    model=GEMINI_MODEL,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
    ),
)
extracted_data = json.loads(response.text)
return extracted_data
```

### New Code:
```python
response = await client.aio.models.generate_content(
    model=GEMINI_MODEL,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ClinicData,  # Add this
    ),
)
extracted_data: ClinicData = response.parsed  # Use this
return extracted_data
```

## Testing

To test the changes:

1. Ensure your `.env` file has `GEMINI_API_KEY` set
2. Run the example: `python example_response_schema.py`
3. Test the API endpoint: `POST /scraper/crawl` with a clinic website URL

## Notes

- Response schema requires `google-genai>=0.2.0` (already in requirements.txt)
- Works with both sync and async API calls
- Compatible with `gemini-2.0-flash-exp` and `gemini-2.5-flash` models
- The schema validation happens server-side by Google's API


