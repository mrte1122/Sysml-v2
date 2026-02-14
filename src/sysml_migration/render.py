from __future__ import annotations

import json
from pathlib import Path

from .model import ChunkedModel, ParsedModel
from .semantics import SemanticsConfig


def write_open_json(open_model: ChunkedModel, out_dir: str | Path) -> Path:
    out_path = Path(out_dir) / "model.open.json"
    payload = {
        "model_id": open_model.model_id,
        "element_count": open_model.element_count,
        "relation_count": open_model.relation_count,
        "chunks": open_model.chunks,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def write_sysml_v2_text(
    model: ParsedModel,
    namespace: str,
    out_dir: str | Path,
    semantics: SemanticsConfig | None = None,
) -> Path:
    out_path = Path(out_dir) / "model.sysmlv2.kerml"
    by_id = {e.element_id: e for e in model.elements}
    semantics_cfg = semantics or SemanticsConfig()

    lines = [f"package {namespace} {{"]
    for e in model.elements:
        safe_name = _sanitize_name(e.name)
        keyword = _sysml_keyword(e.kind, semantics_cfg)
        lines.append(f"  {keyword} {safe_name} {{")
        lines.append(f"    // id: {e.element_id}")
        if e.type_id:
            target = by_id.get(e.type_id)
            target_name = _sanitize_name(target.name) if target else e.type_id
            lines.append(f"    // typed by: {target_name}")
        if e.owner_id:
            lines.append(f"    // owner: {e.owner_id}")
        if e.stereotype:
            lines.append(f"    // stereotype: {e.stereotype}")
        for key, value in sorted(e.properties.items()):
            lines.append(f"    // {key}: {value}")
        lines.append("  }")

    for r in model.relations:
        lines.append(
            f"  // {r.kind} {r.source_id} -> {r.target_id} (id: {r.relation_id})"
        )

    lines.append("}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def write_dot_graph(model: ParsedModel, out_dir: str | Path) -> Path:
    out_path = Path(out_dir) / "model.graph.dot"
    lines = ["digraph SysMLModel {", "  rankdir=LR;", '  node [shape=record];']

    for e in model.elements:
        label = e.name.replace('"', "'")
        lines.append(f'  "{e.element_id}" [label="{{{label}|{e.kind}}}"];')

    for r in model.relations:
        rel = r.kind.replace('"', "'")
        lines.append(f'  "{r.source_id}" -> "{r.target_id}" [label="{rel}"];')

    lines.append("}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def _sysml_keyword(kind: str, semantics: SemanticsConfig) -> str:
    if kind in semantics.text_keywords:
        return semantics.text_keywords[kind]
    if kind == "Requirement":
        return "requirement def"
    if kind in {"Port", "Interface"}:
        return "port def"
    if kind in {"Property", "Connector"}:
        return "item def"
    return "part def"


def _sanitize_name(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
    safe = safe.strip("_") or "UnnamedElement"
    if safe[0].isdigit():
        safe = f"E_{safe}"
    return safe
