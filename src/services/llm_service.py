import google.generativeai as genai
from src.configs.settings import GEMINI_API_KEY, GEMINI_MODEL_NAME

class LLMService:
    def __init__(self):
        """Initialize the LLM service with Google's Gemini API."""
        self.api_key = GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    
    async def generate_content(self, final_prompt):
        """Generate response from LLM with the given prompt."""
        try:
            response = self.model.generate_content(final_prompt)
            return response.text
        except Exception as e:
            print(f"LLM error: {str(e)}")
            raise Exception(f"LLM generation failed: {str(e)}")
