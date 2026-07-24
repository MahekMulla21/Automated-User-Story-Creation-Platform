from src.model import get_response
from src.prompt import SYSTEM_PROMPT

def generate(requirement):

    prompt = SYSTEM_PROMPT + "\n\nRequirement:\n" + requirement

    return get_response(prompt)