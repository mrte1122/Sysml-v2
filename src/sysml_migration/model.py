from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ModelElement:
    element_id: str
    name: str
    kind: str
    source_file: str
    metaclass: str | None = None
    owner_id: str | None = None
    type_id: str | None = None
    stereotype: str | None = None
    properties: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ModelRelation:
    relation_id: str
    kind: str
    source_id: str
    target_id: str
    source_file: str
    properties: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedModel:
    elements: list[ModelElement]
    relations: list[ModelRelation]


@dataclass(slots=True)
class ChunkedModel:
    model_id: str
    chunks: list[dict]
    element_count: int
    relation_count: int
