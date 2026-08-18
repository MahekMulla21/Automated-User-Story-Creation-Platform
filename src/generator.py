import json
from src.model import get_response
from src.prompt import build_prompt


def _strip_code_fences(text: str) -> str:
    """Remove ```json / ``` fences if the model wraps its output despite
    the response_mime_type setting."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


def _extract_json_object(text: str) -> str:
    """Best-effort trim to the outermost { ... } in case the model added
    any stray commentary before/after the JSON despite instructions.
    This only trims surrounding text - it never modifies the JSON
    content itself, so a genuinely malformed payload still fails
    json.loads() the same way it did before."""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text


def _flatten(parsed: dict):
    """Walk epics -> features -> user_stories and produce two flat lists:
    stories (for the User Stories section) and criteria (for the
    Acceptance Criteria section), linked by story id."""
    stories = []
    criteria = []

    for epic in parsed.get("epics", []):
        epic_name = epic.get("name", "Unnamed Epic")

        for feature in epic.get("features", []):
            feature_name = feature.get("name", "Unnamed Feature")

            for story in feature.get("user_stories", []):
                story_id = story.get("id", f"US-{len(stories) + 1:03d}")

                stories.append({
                    "id": story_id,
                    "epic": epic_name,
                    "feature": feature_name,
                    "title": story.get("title", ""),
                    "actor": story.get("actor", ""),
                    "story": story.get("story", ""),
                    "priority": story.get("priority", "Medium"),
                })

                criteria.append({
                    "id": story_id,
                    "scenarios": story.get("acceptance_criteria", []),
                })

    return stories, criteria


def _deduplicate(stories: list, criteria: list):
    """Drop stories whose normalized text is identical to one already
    kept, and keep the matching criteria list in sync."""
    seen = set()
    kept_ids = set()
    deduped_stories = []

    for s in stories:
        normalized = s["story"].strip().lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        kept_ids.add(s["id"])
        deduped_stories.append(s)

    deduped_criteria = [c for c in criteria if c["id"] in kept_ids]
    return deduped_stories, deduped_criteria


def generate(requirement: str) -> dict:
    """
    Main entry point used by app.py.

    Returns:
        {
            "raw": <full nested epics/features/user_stories JSON>,
            "stories": [ {id, epic, feature, title, actor, story, priority}, ... ],
            "criteria": [ {id, scenarios: [{scenario, steps:[...]}]}, ... ],
            "coverage": {epics, features, stories}
        }

    Raises:
        RuntimeError: if the requirement is empty, the model call fails,
        or the model output cannot be parsed as valid JSON. app.py already
        catches RuntimeError around its call to generate(), so this keeps
        the existing error-handling path in the UI working unchanged.
    """
    if not requirement or not requirement.strip():
        raise RuntimeError("Requirement text is empty.")

    prompt = build_prompt(requirement)
    raw_text = get_response(prompt)  # may raise RuntimeError on API failure

    cleaned = _strip_code_fences(raw_text)
    cleaned = _extract_json_object(cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned a response that could not be parsed as JSON. "
            "Please try again."
        ) from exc

    if "epics" not in parsed or not isinstance(parsed["epics"], list):
        raise RuntimeError(
            "Gemini response is missing the expected 'epics' structure."
        )

    stories, criteria = _flatten(parsed)
    if not stories:
        raise RuntimeError(
            "No User Stories could be generated from this requirement."
        )

    stories, criteria = _deduplicate(stories, criteria)

    coverage = {
        "epics": len(parsed.get("epics", [])),
        "features": sum(len(e.get("features", [])) for e in parsed.get("epics", [])),
        "stories": len(stories),
    }

    return {
        "raw": parsed,
        "stories": stories,
        "criteria": criteria,
        "coverage": coverage,
    }
