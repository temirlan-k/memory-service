import asyncio
import structlog

from app.infra.llm.client import LLMClient
from app.services.schemas import EntityList, ObservationList

log = structlog.get_logger()

_OBSERVATION_PROMPT = """\
You are observing a conversation. Extract every atomic observation about the user.

Include:
- Explicit statements by the USER ("I work at Notion")
- Actions the USER takes that imply facts ("walking Biscuit" → user walks an entity named Biscuit)
- Corrections the USER makes ("actually I meant X")
- Preferences the USER mentions in passing

Do NOT include:
- Assumptions or guesses made by the assistant ("you seem like a Python developer")
- Facts stated BY the assistant about the user
- Questions without factual content

Do NOT interpret or infer yet — only observe what the USER says or does.
Return a flat list of short factual sentences about the user.
"""

_ENTITY_PROMPT = """\
You are an entity extractor. Given observations about a user, extract structured entities.

For each entity return:
- value: the concise extracted value ("Berlin", "Notion", "Python", "Biscuit")
- category: one of LOCATION | ORGANIZATION | ANIMAL | PERSON | PREFERENCE | OPINION | GOAL | ATTRIBUTE
- attribute: free-form snake_case descriptor of what this is ("current_city", "pet_name", "programming_language")
- confidence: 0.0–1.0

Category rules (strict):
- LOCATION: any place, city, country, region
- ORGANIZATION: any company, employer, institution
- ANIMAL: any pet or animal the user owns or interacts with
- PERSON: any person's name
- PREFERENCE: something the user likes, prefers, or chooses
- OPINION: what the user thinks or feels about a topic
- GOAL: what the user is working toward or planning
- ATTRIBUTE: personal characteristics (dietary restrictions, allergies, etc.)

Examples:
- "User moved from NYC to Berlin" → LOCATION/previous_city=NYC, LOCATION/current_city=Berlin
- "User works at Notion" → ORGANIZATION/current_company=Notion
- "User walks Biscuit" → ANIMAL/pet_name=Biscuit (confidence 0.85)
- "User prefers Python" → PREFERENCE/programming_language=Python
- "User is vegetarian" → ATTRIBUTE/dietary_restriction=vegetarian
- "User is allergic to shellfish" → ATTRIBUTE/allergy=shellfish

confidence < 0.7 for uncertain inferences.
Return empty list if nothing stable to extract.
"""


class ExtractionService:
    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client

    async def _extract(self, messages: list[dict], response_model):
        last_error = None
        for attempt in range(3):
            try:
                return await self._llm.extract(messages=messages, response_model=response_model)
            except Exception as e:
                last_error = e
                if attempt < 2:
                    await asyncio.sleep(1.5 ** attempt)
        raise last_error

    async def extract_memories(self, messages: list[dict]) -> list[dict]:
        obs_result = await self._extract(
            messages=[{"role": "system", "content": _OBSERVATION_PROMPT}, *messages],
            response_model=ObservationList,
        )
        log.info("observations_done", count=len(obs_result.observations))

        if not obs_result.observations:
            return []

        observation_text = "\n".join(f"- {o}" for o in obs_result.observations)
        entity_result = await self._extract(
            messages=[
                {"role": "system", "content": _ENTITY_PROMPT},
                {"role": "user", "content": f"Observations:\n{observation_text}"},
            ],
            response_model=EntityList,
        )

        memories = [e.to_memory().model_dump() for e in entity_result.entities]
        log.info("extraction_done", count=len(memories))
        return memories
