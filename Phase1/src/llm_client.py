import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
import pandas as pd
from src.config import DEFAULT_MODEL

# Define the Pydantic models for structured output schema
class RecommendationItem(BaseModel):
    name: str = Field(description="Name of the restaurant")
    rating: float = Field(description="Rating of the restaurant")
    cost: int = Field(description="Average cost for two people")
    cuisines: str = Field(description="Cuisines offered")
    location: str = Field(description="Neighborhood location")
    explanation: str = Field(description="AI explanation explaining why this matches user soft-preferences")

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem] = Field(description="List of top recommendations matching preferences")

def get_recommendations(candidates_df: pd.DataFrame, 
                        user_description: str = "", 
                        model_name: str = DEFAULT_MODEL) -> RecommendationResponse:
    """
    Leverages Gemini LLM to rank and provide explanations for the filtered candidate restaurants.
    Falls back to mock explanations if GEMINI_API_KEY is not configured or if API call fails.
    """
    
    # Format candidates list
    candidates = []
    for _, row in candidates_df.iterrows():
        candidates.append({
            "name": row['name'],
            "rating": row['rate_float'],
            "cost": row['cost_clean'],
            "cuisines": row['cuisines'],
            "location": row['location'],
            "address": row['address']
        })

    api_key = os.getenv("GEMINI_API_KEY")

    # If API key is missing or no candidates, return mock / basic response
    if not api_key:
        print("⚠️ GEMINI_API_KEY environment variable not set. Generating mock explanations...")
        return get_mock_response(candidates, user_description)

    try:
        # Initialize the new SDK client
        client = genai.Client(api_key=api_key)

        prompt = f"""
        User Description / Soft Preferences: "{user_description}"

        Candidate Restaurants:
        {candidates}
        """

        system_instruction = (
            "You are Zomato-AI, a premium restaurant recommendation agent. "
            "Your task is to review the candidate list of restaurants, rank the best matches (up to 5) "
            "based on both the user's description (soft preferences) and restaurant quality. "
            "For each selected restaurant, write a short, highly personalized explanation "
            "detailing why it fits their description."
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RecommendationResponse,
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )

        # Parse and return structured Pydantic response
        # The new SDK response.text is guaranteed to match the Pydantic schema
        import json
        data = json.loads(response.text)
        return RecommendationResponse(**data)

    except Exception as e:
        print(f"⚠️ API call failed: {e}. Falling back to mock explanations...")
        return get_mock_response(candidates, user_description)

def get_mock_response(candidates: list, user_description: str) -> RecommendationResponse:
    """
    Generates a mock response with rule-based explanations for demonstration.
    """
    recs = []
    # Take top 5 candidates
    for item in candidates[:5]:
        explanation = f"Recommended based on your query '{user_description}'."
        if user_description:
            desc_lower = user_description.lower()
            if "quiet" in desc_lower or "romantic" in desc_lower:
                explanation = f"Perfect choice for a quiet and cozy dinner away from the crowd."
            elif "cheap" in desc_lower or "budget" in desc_lower:
                explanation = f"An excellent budget-friendly spot serving delicious food without breaking the bank."
            elif "family" in desc_lower or "kids" in desc_lower:
                explanation = f"Very family-friendly seating and menu options suitable for all ages."
            elif "rooftop" in desc_lower or "view" in desc_lower:
                explanation = f"Great ambiance with stunning scenic views and relaxing vibes."
            else:
                explanation = f"A popular choice in {item['location']} featuring authentic {item['cuisines']} cuisines."
        else:
            explanation = f"Highly rated spot in {item['location']} serving popular {item['cuisines']} specialties."

        recs.append(RecommendationItem(
            name=item['name'],
            rating=item['rating'],
            cost=item['cost'],
            cuisines=item['cuisines'],
            location=item['location'],
            explanation=explanation
        ))
    
    return RecommendationResponse(recommendations=recs)
