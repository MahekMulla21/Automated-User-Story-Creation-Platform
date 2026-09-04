import os
import time
import random
from google import genai
from google.genai import errors, types
from dotenv import load_dotenv



load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. "
        "Please add GEMINI_API_KEY to your .env file."
    )




client = genai.Client(
    api_key=API_KEY
)




MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]



MODEL_CONFIGS = {

    "gemini-3.5-flash-lite": types.GenerateContentConfig(
        response_mime_type="application/json",
        max_output_tokens=32768,
        temperature=0.4,
    ),

    "gemini-2.5-flash": types.GenerateContentConfig(
        response_mime_type="application/json",
        max_output_tokens=32768,
        temperature=0.4,
    ),

}


MAX_ATTEMPTS_PER_MODEL = 2

BASE_DELAY_SECONDS = 2



def get_response(prompt: str) -> str:
    """
    Generate a response from Gemini.

    Model behavior:
        1. Try gemini-3.5-flash-lite.
        2. If unavailable/quota exceeded, move to gemini-2.5-flash.
        3. Retry temporary 503 errors.
        4. Return the generated response as text.
        5. Raise a clean error if all models fail.

    The API is configured to return JSON.
    """

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    last_error = None

    

    for model_name in MODELS:

       
        if model_name not in MODEL_CONFIGS:
            print(
                f"WARNING: No configuration found for {model_name}. "
                f"Skipping this model."
            )
            continue

        config = MODEL_CONFIGS[model_name]

        print(f"\nTrying Gemini model: {model_name}")

     

        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):

            try:

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )

              

                if not response:
                    raise RuntimeError(
                        f"Empty response object from {model_name}."
                    )

                if not response.text:
                    raise RuntimeError(
                        f"Gemini returned an empty response from "
                        f"{model_name}."
                    )

               

                finish_reason = _get_finish_reason(response)

                if finish_reason == "MAX_TOKENS":

                    raise RuntimeError(
                        "Gemini's response was cut off before it "
                        "finished generating because the output "
                        "token limit was reached. "
                        "Try a shorter requirement or split the "
                        "generation into smaller parts."
                    )

                print(
                    f"Successfully generated response using "
                    f"{model_name}"
                )

                return response.text


            except errors.ClientError as e:

                error_text = str(e)

                print("\n===== GEMINI CLIENT ERROR =====")
                print(error_text)
                print("===============================\n")

                last_error = e

                

                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:

                    print(
                        f"Quota/rate limit reached for {model_name}."
                    )

                    print(
                        "Skipping this model and trying the next "
                        "available model..."
                    )

                    # Do NOT retry this model.
                    # Move directly to next model.
                    break

             

                if (
                    "404" in error_text
                    or "NOT_FOUND" in error_text
                ):

                    print(
                        f"Model {model_name} is unavailable "
                        f"for this API account."
                    )

                    print(
                        "Skipping this model and trying the "
                        "next model..."
                    )

                    break

           

                print(
                    f"Client error with {model_name}. "
                    f"Trying the next model..."
                )

                break


            except errors.ServerError as e:

                last_error = e

                print(
                    f"\nGemini server error using {model_name} "
                    f"(attempt {attempt}/"
                    f"{MAX_ATTEMPTS_PER_MODEL})"
                )

                print(str(e))

             

                if attempt < MAX_ATTEMPTS_PER_MODEL:

                    delay = BASE_DELAY_SECONDS * (
                        2 ** (attempt - 1)
                    )

                    delay += random.uniform(0, 1)

                    print(
                        f"Retrying in {delay:.1f} seconds..."
                    )

                    time.sleep(delay)

                    continue


                print(
                    f"Maximum retries reached for {model_name}."
                )

                print(
                    "Trying the next available model..."
                )

                break


            except RuntimeError as e:

                last_error = e

                print(
                    f"\nRuntime error from {model_name}:"
                )

                print(str(e))

                # Runtime errors generally won't be fixed by
                # retrying the same request.
                break

         

            except Exception as e:

                last_error = e

                print(
                    f"\nUnexpected error from {model_name}:"
                )

                print(str(e))

                print(
                    "Trying the next available model..."
                )

                break


    if last_error is not None:

        error_text = str(last_error)


        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
        ):

            raise RuntimeError(
                "All configured Gemini models have reached "
                "their current API quota/rate limit. "
                "Please check your Gemini API quota or billing "
                "status and try again later."
            ) from last_error

       

        if (
            "404" in error_text
            or "NOT_FOUND" in error_text
        ):

            raise RuntimeError(
                "None of the configured Gemini models are "
                "available for this API account."
            ) from last_error

     

        raise RuntimeError(
            "Gemini could not generate a response using "
            "any of the configured models."
        ) from last_error

    raise RuntimeError(
        "No valid Gemini models are configured."
    )



def _get_finish_reason(response) -> str:
    """
    Safely extract the finish reason from a Gemini response.

    Possible values include:
        STOP
        MAX_TOKENS

    Returns an empty string if the response structure does
    not contain a finish reason.
    """

    try:

        if not response.candidates:
            return ""

        candidate = response.candidates[0]

        reason = candidate.finish_reason

        if hasattr(reason, "name"):
            return reason.name

        return str(reason)

    except Exception:
        return ""


