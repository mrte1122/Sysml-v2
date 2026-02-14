from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class SemanticsConfig:
    kind_rules: dict[str, str] = field(default_factory=dict)
    relation_rules: dict[str, str] = field(default_factory=dict)
    text_keywords: dict[str, str] = field(default_factory=dict)


def load_semantics(path: str | Path | None) -> SemanticsConfig:
    if path is None:
        return SemanticsConfig()

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Semantics file does not exist: {p}")

    payload = json.loads(p.read_text(encoding="utf-8"))
    return SemanticsConfig(
        kind_rules={k.lower(): v for k, v in payload.get("kind_rules", {}).items()},
        relation_rules={k.lower(): v for k, v in payload.get("relation_rules", {}).items()},
        text_keywords=payload.get("text_keywords", {}),
    )
