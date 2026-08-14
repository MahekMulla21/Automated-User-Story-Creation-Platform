import os
import time
import random
from google import genai
from google.genai import errors
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

MAX_ATTEMPTS_PER_MODEL = 3
BASE_DELAY_SECONDS = 2


def get_response(prompt: str) -> str:
    """
    Calls Gemini with automatic retry (for transient 503s) and
    fallback across multiple models. Raises a clean, user-friendly
    exception if everything fails, instead of letting the raw
    google.genai error bubble up and crash the app.
    """
    last_error = None

    for model_name in MODELS:
        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text

            except errors.ServerError as e:
    
                last_error = e
                is_last_attempt = attempt == MAX_ATTEMPTS_PER_MODEL
                if not is_last_attempt:
                   
                    delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                    delay += random.uniform(0, 1)
                    time.sleep(delay)
                    continue
               
            except errors.ClientError as e:
                raise RuntimeError(
                    "Gemini rejected the request (client error). "
                    "Check your API key, quota, or request format."
                ) from e

            except Exception as e:
                last_error = e
                break

    raise RuntimeError(
        "Gemini is temporarily unavailable due to high demand. "
        "Please wait a minute and try again."
    ) from last_error
