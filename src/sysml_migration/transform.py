from __future__ import annotations

from collections import Counter

from .model import ChunkedModel, ParsedModel


def to_open_model(model: ParsedModel, model_id: str, chunk_size: int = 250) -> ChunkedModel:
    serialized_elements = [
        {
            "id": e.element_id,
            "name": e.name,
            "kind": e.kind,
            "metaclass": e.metaclass,
            "owner": e.owner_id,
            "type": e.type_id,
            "stereotype": e.stereotype,
            "source_file": e.source_file,
            "properties": e.properties,
        }
        for e in model.elements
    ]
    serialized_relations = [
        {
            "id": r.relation_id,
            "kind": r.kind,
            "source": r.source_id,
            "target": r.target_id,
            "source_file": r.source_file,
            "properties": r.properties,
        }
        for r in model.relations
    ]

    kind_counts = Counter(e["kind"] for e in serialized_elements)
    chunks: list[dict] = []
    for i in range(0, len(serialized_elements), chunk_size):
        element_chunk = serialized_elements[i : i + chunk_size]
        element_ids = {e["id"] for e in element_chunk}
        relation_chunk = [
            r
            for r in serialized_relations
            if r["source"] in element_ids or r["target"] in element_ids
        ]

        chunks.append(
            {
                "chunk_id": f"chunk-{(i // chunk_size) + 1}",
                "elements": element_chunk,
                "relations": relation_chunk,
            }
        )

    if not chunks:
        chunks.append({"chunk_id": "chunk-1", "elements": [], "relations": []})

    chunks[0]["stats"] = {"element_kinds": dict(kind_counts)}

    return ChunkedModel(
        model_id=model_id,
        chunks=chunks,
        element_count=len(serialized_elements),
        relation_count=len(serialized_relations),
    )
