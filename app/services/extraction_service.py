import asyncio
import json
import re
import structlog

from app.infra.llm.client import LLMClient

log = structlog.get_logger()

_SYSTEM_PROMPT = """\
You are a memory extraction engine. Extract structured facts from the conversation.

Return JSON: {"memories": [...]}
Each memory object must have:
  - type: "fact" | "preference" | "opinion" | "event"
  - key: canonical dot-notation string
  - value: concise extracted value
  - confidence: 0.0-1.0

Canonical key examples:
  employment.current_company, employment.current_role, employment.previous_company
  location.current_city, location.country
  personal.name, personal.pet_name, personal.pet_type
  personal.dietary_restriction, personal.allergy
  preference.programming_language, preference.editor, preference.communication_style
  opinion.<topic>
  family.partner_name, family.children_count
  goal.current, context.current_task

Rules:
- Use the SAME key for the same fact across sessions — this is critical for deduplication.
- Capture implicit facts: "walking Biscuit" → pet_name=Biscuit, pet_type=dog.
- Capture corrections: "actually I meant X" supersedes the prior value.
- confidence < 0.7 for hedged statements ("might", "thinking about").
- Skip greetings, filler, questions with no factual content.
- Return {"memories": []} if nothing is worth extracting.

Output format — return ONLY valid JSON, no markdown, no explanation:
{
  "memories": [
    {"type": "fact",       "key": "location.current_city",      "value": "Berlin",    "confidence": 0.95},
    {"type": "fact",       "key": "location.previous_city",     "value": "NYC",       "confidence": 0.95},
    {"type": "preference", "key": "preference.communication_style", "value": "concise", "confidence": 0.8},
    {"type": "opinion",    "key": "opinion.remote_work",        "value": "prefers it", "confidence": 0.75},
    {"type": "event",      "key": "context.current_task",       "value": "preparing for interview", "confidence": 0.9}
  ]
}
"""


def _extract_json(raw: str) -> str:
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        return match.group(1).strip()
    return raw or '{"memories": []}'


class ExtractionService:
    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client
        self._retry_attempts = 3
        self._backoff_factor = 1.5

    async def extract_memories(self, messages: list[dict]) -> list[dict]:
        last_error: Exception | None = None
        for attempt in range(self._retry_attempts):
            try:
                response = await self._llm.chat_completion(
                    messages=[{"role": "system", "content": _SYSTEM_PROMPT}, *messages],
                )
                raw = _extract_json(response.choices[0].message.content or "")
                memories = json.loads(raw).get("memories", [])
                log.info("extraction_done", count=len(memories))
                return memories
            except Exception as e:
                last_error = e
                log.warning("extraction_attempt_failed", attempt=attempt + 1, error=str(e))
                await asyncio.sleep(self._backoff_factor ** attempt)

        log.error("extraction_failed_all_attempts", error=str(last_error))
        raise last_error
