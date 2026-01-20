import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


for model in genai.list_models():
    print("Name:", model.name)
    print("  Display name:", model.display_name)
    print("  Supported methods:", model.supported_generation_methods)
    print()
