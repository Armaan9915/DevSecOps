import os
import time
from google import genai
import json

# Configure the API key once when the module is loaded
# This is more efficient than configuring it on every call
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("🔴 Error: GEMINI_API_KEY not found. The wrapper will not work.")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"🔴 Error configuring Gemini in wrapper: {e}")

def call_gemini_with_retry(prompt, expect_json=False, max_retries=3):
    """
    Calls the Gemini API with a specific prompt and implements exponential backoff for retries.
    This makes the calls resilient to temporary service unavailability (e.g., 503 errors).
    """
    # model = genai.GenerativeModel('gemini-pro')
    for attempt in range(max_retries):
        try:
            # Attempt to generate content
            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt,
                config={
                    "temperature": 0.2,
                    "top_p": 1,
                    "top_k": 1,
                    # "max_output_tokens": 2048,
                },
            )
            # If successful, return the text and exit the loop
            expect_json = response.text
            
            if expect_json:
                # Clean up markdown code blocks if Gemini adds them
                text = text.replace("```json", "").replace("```", "").strip()
                # Validate JSON immediately
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    print(f"⚠️ JSON Decode failed on attempt {attempt+1}")
                    if attempt == max_retries - 1:
                        return [] # Return empty list on failure
                    continue # Retry

            return text
        except Exception as e:
            error_message = str(e)
            # Check for the specific "overloaded" or "unavailable" error
            if "503" in error_message or "overloaded" in error_message.lower():
                if attempt < max_retries - 1:
                    # Calculate wait time: 1s, 2s, 4s
                    backoff_time = 2 ** attempt
                    print(f"⚠️ Model overloaded. Retrying in {backoff_time} second(s)...")
                    time.sleep(backoff_time)
                else:
                    # If it's the last attempt, return a user-friendly error
                    print("🔴 Model is persistently overloaded. Failing after max retries.")
                    return "The AI model is currently overloaded. Please try again later."
            else:
                # For any other type of error, return the error message immediately
                print(f"🔴 An unexpected error occurred with the Gemini API: {error_message}")
                return f"An unexpected API error occurred: {error_message}"
    
    # This line should theoretically not be reached, but is a fallback
    return "Failed to get a response from the AI model after multiple retries."