import structlog
from pydantic import BaseModel

from app.api.schemas.recall import Citation, RecallResponse
from app.infra.db.models.memory import Memory
from app.infra.llm.client import LLMClient

log = structlog.get_logger()

_STABLE_PREFIXES = {"personal", "employment", "location", "family"}
_MIN_RRF_SCORE = 0.02

_FORMAT_PROMPT = """\
Convert these memory key=value pairs into concise readable sentences for an AI assistant context.
One sentence per fact. Be brief and natural.

Examples:
employment.current_company=Notion → Works at Notion
location.current_city=Berlin → Currently lives in Berlin
location.previous_city=NYC → Previously lived in NYC
personal.pet_name=Biscuit → Has a pet named Biscuit
personal.dietary_restriction=vegetarian → Is vegetarian
personal.allergy=shellfish → Allergic to shellfish
goal.upcoming_interview=system design interview → Preparing for a system design interview
preference.programming_language=Python → Prefers Python
"""


class _FormattedMemories(BaseModel):
    lines: list[str]


_FORMAT_OVERHEAD = 4


def _approx_tokens(text: str) -> int:
    return (len(text) * _FORMAT_OVERHEAD) // 4


def _is_stable(key: str) -> bool:
    return key.split(".")[0] in _STABLE_PREFIXES


class ContextAssembler:
    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client

    async def assemble(
        self,
        stable_facts: list[Memory],
        candidates: list[tuple[Memory, float]],
        max_tokens: int,
    ) -> RecallResponse:
        stable_ids = {str(m.id) for m in stable_facts}
        relevant = [
            (m, score) for m, score in candidates
            if str(m.id) not in stable_ids and score >= _MIN_RRF_SCORE
        ]

        selected_stable, selected_relevant = self._select_within_budget(stable_facts, relevant, max_tokens)

        all_memories = selected_stable + [m for m, _ in selected_relevant]
        formatted = await self._format_memories(all_memories)

        citations = self._build_citations(selected_stable, selected_relevant)
        context = self._build_context(formatted, len(selected_stable), len(selected_relevant))

        return RecallResponse(context=context, citations=citations)

    def _select_within_budget(
        self,
        stable: list[Memory],
        relevant: list[tuple[Memory, float]],
        max_tokens: int,
    ) -> tuple[list[Memory], list[tuple[Memory, float]]]:
        used = 0
        sel_stable, sel_relevant = [], []

        for m in stable:
            if used + _approx_tokens(m.value) > max_tokens:
                break
            sel_stable.append(m)
            used += _approx_tokens(m.value)

        for m, score in relevant:
            if used + _approx_tokens(m.value) > max_tokens:
                break
            sel_relevant.append((m, score))
            used += _approx_tokens(m.value)

        return sel_stable, sel_relevant

    async def _format_memories(self, memories: list[Memory]) -> list[str]:
        if not memories:
            return []
        raw = "\n".join(f"{m.key}={m.value}" for m in memories)
        try:
            result: _FormattedMemories = await self._llm.extract(
                messages=[
                    {"role": "system", "content": _FORMAT_PROMPT},
                    {"role": "user", "content": raw},
                ],
                response_model=_FormattedMemories,
            )
            return result.lines
        except Exception as e:
            log.warning("format_memories_failed", error=str(e))
            return [f"{m.key}: {m.value}" for m in memories]

    def _build_citations(
        self,
        stable: list[Memory],
        relevant: list[tuple[Memory, float]],
    ) -> list[Citation]:
        citations = []
        for m in stable:
            citations.append(Citation(turn_id=str(m.source_turn_id), score=round(m.confidence, 3), snippet=f"{m.key}: {m.value}"))
        for m, score in relevant:
            citations.append(Citation(turn_id=str(m.source_turn_id), score=round(score, 4), snippet=f"{m.key}: {m.value}"))
        return citations

    def _build_context(self, formatted: list[str], stable_count: int, relevant_count: int) -> str:
        sections = []
        if stable_count:
            lines = ["## Known facts about this user"] + [f"- {l}" for l in formatted[:stable_count]]
            sections.append("\n".join(lines))
        if relevant_count:
            lines = ["## Relevant from recent conversations"] + [f"- {l}" for l in formatted[stable_count:]]
            sections.append("\n".join(lines))
        return "\n\n".join(sections)
