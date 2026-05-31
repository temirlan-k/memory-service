from typing import Literal
from pydantic import BaseModel, field_validator, model_validator

_TYPE_BY_PREFIX = {
    "opinion": "opinion",
    "preference": "preference",
    "goal": "event",
    "context": "event",
}

_CATEGORY_PREFIX = {
    "LOCATION": "location",
    "ORGANIZATION": "employment",
    "ANIMAL": "personal",
    "PERSON": "personal",
    "PREFERENCE": "preference",
    "OPINION": "opinion",
    "GOAL": "goal",
    "ATTRIBUTE": "personal",
}


class ExtractedEntity(BaseModel):
    value: str
    category: Literal["LOCATION", "ORGANIZATION", "ANIMAL", "PERSON", "PREFERENCE", "OPINION", "GOAL", "ATTRIBUTE"]
    attribute: str
    confidence: float = 1.0

    @field_validator("attribute")
    @classmethod
    def normalise_attribute(cls, v: str) -> str:
        return v.strip().lower().replace(" ", "_")

    @field_validator("confidence")
    @classmethod
    def clamp(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    def to_memory(self) -> "ExtractedMemory":
        prefix = _CATEGORY_PREFIX[self.category]
        key = f"{prefix}.{self.attribute}"
        return ExtractedMemory(key=key, value=self.value, confidence=self.confidence)


class EntityList(BaseModel):
    entities: list[ExtractedEntity]


class ExtractedMemory(BaseModel):
    type: str = "fact"
    key: str
    value: str
    confidence: float = 1.0

    @field_validator("key")
    @classmethod
    def normalise_key(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("confidence")
    @classmethod
    def clamp(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    @model_validator(mode="after")
    def infer_type(self) -> "ExtractedMemory":
        prefix = self.key.split(".")[0] if self.key else ""
        self.type = _TYPE_BY_PREFIX.get(prefix, "fact")
        return self


class ObservationList(BaseModel):
    observations: list[str]
