import os
import time
import json
from huggingface_hub import InferenceClient

# ===============================
# Hugging Face configuration
# ===============================
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    print("🔴 Error: HF_TOKEN not found. The wrapper will not work.")

client = InferenceClient(
    model="Qwen/Qwen3-Coder-Next",
    token=HF_TOKEN,
    timeout=60,  # seconds
)

# ===============================
# Call Qwen with retry
# ===============================
def call_qwen_with_retry(prompt, expect_json=False, max_retries=3):
    """
    Calls Hugging Face hosted Qwen3-Coder-Next with retries and exponential backoff.
    Designed for PR diff review + fix suggestions.
    """

    for attempt in range(max_retries):
        try:
            response = client.text_generation(
                prompt,
                temperature=0.2,
                top_p=0.9,
                max_new_tokens=2048,
            )

            text = response.strip()
            print("response:", text)

            if expect_json:
                # Remove markdown fences if present
                text = (
                    text.replace("```json", "")
                        .replace("```", "")
                        .strip()
                )
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    print(f"⚠️ JSON decode failed on attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        return []
                    continue

            return text

        except Exception as e:
            error_message = str(e)

            if any(k in error_message.lower() for k in ["503", "overloaded", "rate limit"]):
                if attempt < max_retries - 1:
                    backoff_time = 2 ** attempt
                    print(f"⚠️ Model busy. Retrying in {backoff_time}s...")
                    time.sleep(backoff_time)
                else:
                    print("🔴 Model overloaded after max retries.")
                    return "The AI model is currently overloaded. Please try again later."
            else:
                print(f"🔴 Unexpected HF API error: {error_message}")
                return f"An unexpected API error occurred: {error_message}"

    return "Failed to get a response after multiple retries."
