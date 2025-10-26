"""
Example: Using Google GenAI with Response Schema
This demonstrates how to use Pydantic models for structured responses.
"""

from google import genai
from pydantic import BaseModel
from typing import Optional
from helpers.envHelper import settings


# Define Pydantic models for the response schema
class Recipe(BaseModel):
    """Recipe model"""
    recipe_name: str
    ingredients: list[str]


class Person(BaseModel):
    """Person model"""
    name: str
    age: int
    occupation: Optional[str] = None


def example_recipe_extraction():
    """Example: Extract recipes with structured schema"""
    client = genai.Client(api_key=settings.gemini_api_key)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents="List a few popular cookie recipes, and include the amounts of ingredients.",
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Recipe],
        },
    )
    
    # Use the response as a JSON string
    print("Response as JSON string:")
    print(response.text)
    print("\n" + "="*80 + "\n")
    
    # Use instantiated objects
    my_recipes: list[Recipe] = response.parsed
    print("Parsed Pydantic objects:")
    for recipe in my_recipes:
        print(f"Recipe: {recipe.recipe_name}")
        print(f"Ingredients: {', '.join(recipe.ingredients)}")
        print()


def example_person_extraction():
    """Example: Extract person information with structured schema"""
    client = genai.Client(api_key=settings.gemini_api_key)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Tell me about Albert Einstein - his name, age at death, and occupation.",
        config={
            "response_mime_type": "application/json",
            "response_schema": Person,
        },
    )
    
    # Use parsed object
    person: Person = response.parsed
    print("Person Information:")
    print(f"Name: {person.name}")
    print(f"Age: {person.age}")
    print(f"Occupation: {person.occupation}")


if __name__ == "__main__":
    print("Example 1: Recipe Extraction")
    print("="*80)
    example_recipe_extraction()
    
    print("\n\nExample 2: Person Information")
    print("="*80)
    example_person_extraction()


