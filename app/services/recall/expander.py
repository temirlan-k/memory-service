import structlog
from pydantic import BaseModel
from app.infra.llm.client import LLMClient

log = structlog.get_logger()

_EXPAND_PROMPT = """\
Expand the search query into 2-3 short keyword phrases to improve search recall.
Focus on synonyms, related terms, and different ways to express the same concept.

Examples:
"Where does the user live?" → ["current city", "location residence", "city where user lives"]
"What is the pet's name?" → ["pet name", "dog cat animal name", "pet owner"]
"Where does the user work?" → ["current employer", "job company", "employment workplace"]
"What does the user prefer?" → ["preference favorite", "likes enjoys", "user choice"]

Return only short keyword phrases, no full sentences.\
"""


class _QueryExpansion(BaseModel):
    queries: list[str]


class QueryExpander:
    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client

    async def expand(self, query: str) -> list[str]:
        try:
            result: _QueryExpansion = await self._llm.extract(
                messages=[
                    {"role": "system", "content": _EXPAND_PROMPT},
                    {"role": "user", "content": query},
                ],
                response_model=_QueryExpansion,
            )
            return result.queries[:3]
        except Exception as e:
            log.warning("query_expand_failed", error=str(e))
            return []
