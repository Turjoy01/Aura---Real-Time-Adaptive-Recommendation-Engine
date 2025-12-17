from openai import OpenAI
from src.models.recommend import ParsedIntent
from src.core.config import settings

class NaturalLanguageParser:
    """Parse natural language queries into structured event filters using LLM"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def parse_query(self, query: str) -> ParsedIntent:
        """
        Convert natural language query to structured intent
        Example: "techno in Brooklyn tonight under $40" →
        {"categories": ["Techno"], "price_max": 40, "time_slot": "Late Night", ...}
        """
        
        prompt = f"""
You are an expert event search query parser. Parse the following user query and extract:
1. Event categories (Techno, Hip-Hop, House, Jazz, Comedy, Theater, etc.)
2. Max price willing to pay (if mentioned)
3. Time slot preference (Early Evening, Evening, Late Night, Afternoon, All Day)
4. Location/neighborhood preferences
5. Age restrictions (21+, 18+, All Ages)
6. Vibe keywords (intimate, energetic, chill, underground, mainstream, etc.)

Query: "{query}"

Respond ONLY with valid JSON (no markdown, no code blocks):
{{
  "categories": ["category1", "category2"],
  "price_max": null or number,
  "time_slot": "Evening" or null,
  "location": "Brooklyn" or null,
  "age_restriction": "21+" or null,
  "vibe_keywords": ["keyword1", "keyword2"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON parsing API. Always respond with valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            import json
            content = response.choices[0].message.content.strip()
            
            # Clean up if wrapped in markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1].replace("json", "", 1).strip()
            
            parsed_data = json.loads(content)
            
            return ParsedIntent(
                categories=parsed_data.get("categories", []),
                price_max=parsed_data.get("price_max"),
                time_slot=parsed_data.get("time_slot"),
                location=parsed_data.get("location"),
                age_restriction=parsed_data.get("age_restriction"),
                vibe_keywords=parsed_data.get("vibe_keywords", [])
            )
            
        except Exception as e:
            print(f"Error parsing query: {e}")
            # Fallback: return empty parsed intent
            return ParsedIntent(
                categories=[],
                vibe_keywords=["general"]
            )

    async def generate_explanation(
        self,
        query: str,
        parsed_intent: ParsedIntent,
        event_count: int
    ) -> str:
        """Generate user-friendly explanation of search results"""
        
        prompt = f"""
Summarize why we found {event_count} events for this search in 1 short sentence.

User query: "{query}"
Parsed as:
- Categories: {', '.join(parsed_intent.categories) if parsed_intent.categories else 'any'}
- Max price: ${parsed_intent.price_max if parsed_intent.price_max else 'no limit'}
- Time: {parsed_intent.time_slot or 'any time'}
- Location: {parsed_intent.location or 'nearby'}

Response with just 1 sentence explanation.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except:
            return "Here are personalized event recommendations based on your search."
