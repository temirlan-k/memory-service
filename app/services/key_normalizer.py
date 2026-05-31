import structlog
from pydantic import BaseModel

from app.infra.llm.client import LLMClient

log = structlog.get_logger()

_PROMPT = """\
You are a memory key deduplication engine.

Given a new memory key and a list of existing keys, determine if the new key represents
the same concept as any existing key.

Rules:
- Match only if they clearly represent the same real-world fact about the user.
- "employment.current_employer" == "employment.current_company" → MATCH
- "goal.interview_prep" == "goal.upcoming_interview" → MATCH
- "personal.pet_name" == "employment.current_company" → NO MATCH
- Different fields of the same domain (current_city vs previous_city) → NO MATCH
- If uncertain → NO MATCH

Return the matching existing key, or null if no match.
"""


class _NormResult(BaseModel):
    matched_key: str | None


class KeyNormalizer:
    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client

    async def normalize(self, new_key: str, existing_keys: list[str]) -> str:
        if not existing_keys:
            return new_key

        same_prefix = [k for k in existing_keys if k.split(".")[0] == new_key.split(".")[0]]
        if not same_prefix:
            return new_key

        try:
            result: _NormResult = await self._llm.extract(
                messages=[
                    {"role": "system", "content": _PROMPT},
                    {"role": "user", "content": f"New key: {new_key}\nExisting keys: {same_prefix}"},
                ],
                response_model=_NormResult,
            )
            if result.matched_key and result.matched_key in existing_keys:
                log.info("key_normalized", original=new_key, normalized=result.matched_key)
                return result.matched_key
        except Exception as e:
            log.warning("key_normalization_failed", key=new_key, error=str(e))

        return new_key

    async def normalize_all(self, memories: list[dict], existing_keys: list[str]) -> list[dict]:
        for m in memories:
            m["key"] = await self.normalize(m["key"], existing_keys)
        return memories
