import os
import time
import random
from google import genai
from google.genai import errors, types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash"
]

MODEL_CONFIGS = {

    "gemini-2.5-flash": types.GenerateContentConfig(
        response_mime_type="application/json",
        max_output_tokens=32768,
        temperature=0.4,
    ),

    "gemini-2.0-flash": types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.9,
        top_k=40,
        max_output_tokens=4096,
        response_mime_type="application/json",
    ),

}



MAX_ATTEMPTS_PER_MODEL = 3
BASE_DELAY_SECONDS = 2


def get_response(prompt: str) -> str:
    """
    Calls Gemini with automatic retry (for transient 503s) and
    fallback across multiple models. Requests structured JSON output
    and a token budget sized per model so multi-story responses aren't
    truncated. Raises a clean, user-friendly exception if everything
    fails, instead of letting the raw google.genai error (or a
    downstream JSONDecodeError) crash the app.
    """
    last_error = None

    for model_name in MODELS:
        config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["gemini-2.0-flash"])

        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )

                if not response or not response.text:
                    raise RuntimeError("Empty response from Gemini.")

                finish_reason = _get_finish_reason(response)
                if finish_reason == "MAX_TOKENS":
                    raise RuntimeError(
                        "Gemini's response was cut off before it finished "
                        "generating (output token limit reached). Try a "
                        "shorter or more focused requirement, or split it "
                        "into smaller parts and generate them separately."
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

            except RuntimeError as e:
               
                last_error = e
                break

            except Exception as e:
                last_error = e
                break

    if isinstance(last_error, RuntimeError):
        raise last_error

    raise RuntimeError(
        "Gemini is temporarily unavailable due to high demand. "
        "Please wait a minute and try again."
    ) from last_error


def _get_finish_reason(response) -> str:
    """Best-effort extraction of the finish reason string (e.g.
    'MAX_TOKENS', 'STOP') from a genai response, without blowing up if
    the SDK's response shape doesn't have candidates for some reason."""
    try:
        candidate = response.candidates[0]
        reason = candidate.finish_reason
        return reason.name if hasattr(reason, "name") else str(reason)
    except Exception:
        return ""