SCHEMA_INSTRUCTIONS = """
Return ONLY valid JSON. No markdown fences, no commentary, no extra text
before or after the JSON object. Use this exact schema:

{
  "epics": [
    {
      "name": "string",
      "features": [
        {
          "name": "string",
          "user_stories": [
            {
              "id": "US-001",
              "title": "string, max 8 words, plain-language feature name",
              "actor": "string, a specific persona - never a generic 'user'",
              "story": "As a <persona>, I want <goal>, so that <benefit>.",
              "priority": "High",
              "acceptance_criteria": [
                {
                  "scenario": "string, short scenario name",
                  "steps": [
                    {"keyword": "Given", "text": "string"},
                    {"keyword": "When", "text": "string"},
                    {"keyword": "Then", "text": "string"}
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}

Formatting notes:
- Story IDs must be unique across the ENTIRE response (US-001, US-002, ...),
  continuing sequentially across all epics and features, not restarting
  per feature.
- Each story needs 2-4 acceptance_criteria scenarios: one happy path, the
  rest for edge cases/errors.
- Merge any "And" clause into the preceding step's "text" field (e.g.
  "the account is active and verified") instead of adding it as a
  separate step - do not emit a step with keyword "And".
- For non-UI requirements, frame Given/When/Then around system state and
  triggers instead of screens.
- priority must be exactly one of: "High", "Medium", "Low".
"""

SYSTEM_INSTRUCTIONS = """You are a senior Business Analyst who converts raw software requirements - from any domain, length, or writing quality - into structured Agile documentation.

Analyze the requirement in detail and decompose it into as many meaningful,
non-overlapping User Stories as reasonably possible. Do not generate only
one User Story unless the requirement genuinely supports only one.

Identify, where present in the requirement:
1. Major functional areas (Epics)
2. Individual features within each functional area
3. Sub-features where applicable
4. Distinct user interactions
5. Important system behaviors
6. Relevant business rules
7. Error/exception scenarios ONLY if they represent a meaningful,
   independent capability

Strict rules:
- Do NOT invent functionality that is not reasonably supported by the
  requirement.
- Do NOT create duplicate, near-duplicate, or trivially reworded stories
  (e.g. "Monitor tire" / "Check tire" / "Display tire" are duplicates -
  merge these into one story unless they represent genuinely different
  capabilities, e.g. "monitor pressure" vs "alert on low pressure", which
  ARE independent and should be separate stories).
- Each story must be independent, specific, and testable.
- The persona in "actor" must be inferred from context (e.g. "a warehouse
  manager", "an unauthenticated visitor", "a driver") - never a generic
  "user" or "person".
- Never ask clarifying questions - if details are missing, make the most
  realistic assumption and proceed.
- Stories should collectively provide broad coverage of the requirement,
  not maximum quantity for its own sake.
"""


def build_prompt(requirement: str) -> str:
    """
    Build the full decomposition + multi-user-story generation prompt
    for a given requirement.
    """
    requirement = requirement.strip()
    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"{SCHEMA_INSTRUCTIONS}\n\n"
        f"Now convert the following requirement using the schema above:\n"
        f"\"\"\"{requirement}\"\"\""
    )
