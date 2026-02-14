from __future__ import annotations

import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

from .model import ModelElement, ModelRelation, ParsedModel
from .semantics import SemanticsConfig

XML_SUFFIXES = (".xml", ".xmi", ".uml", ".mdxml")
ID_KEYS = ("xmi:id", "id")
TYPE_KEYS = ("xmi:type", "type")
NAME_KEYS = ("name",)


def parse_mdzip(mdzip_path: str | Path, semantics: SemanticsConfig | None = None) -> ParsedModel:
    path = Path(mdzip_path)
    if not path.exists():
        raise FileNotFoundError(f"Input archive does not exist: {path}")

    semantics_cfg = semantics or SemanticsConfig()
    elements: dict[str, ModelElement] = {}
    relations: dict[tuple[str, str, str], ModelRelation] = {}

    with zipfile.ZipFile(path, "r") as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(XML_SUFFIXES)]

        for name in names:
            raw = archive.read(name)
            try:
                root = ET.fromstring(raw)
            except ET.ParseError:
                continue

            _walk_xml(root, None, name, elements, relations, semantics_cfg)

    return ParsedModel(elements=list(elements.values()), relations=list(relations.values()))


def _walk_xml(
    node: ET.Element,
    owner_id: str | None,
    source_file: str,
    elements: dict[str, ModelElement],
    relations: dict[tuple[str, str, str], ModelRelation],
    semantics: SemanticsConfig,
) -> None:
    attrib = normalize_attrib(node.attrib)

    element_id = _first(attrib, ID_KEYS)
    metaclass = _first(attrib, TYPE_KEYS) or strip_ns(node.tag)
    element_kind = _normalize_kind(metaclass, node.tag, semantics)

    current_id = owner_id
    if element_id:
        element = elements.get(element_id)
        if element is None:
            element = ModelElement(
                element_id=element_id,
                name=_first(attrib, NAME_KEYS) or f"{element_kind}_{element_id}",
                kind=element_kind,
                metaclass=metaclass,
                source_file=source_file,
                owner_id=owner_id,
                type_id=attrib.get("type"),
                stereotype=attrib.get("stereotype") or attrib.get("appliedStereotype"),
                properties={
                    k: v
                    for k, v in attrib.items()
                    if k
                    not in {
                        "xmi:id",
                        "id",
                        "xmi:type",
                        "type",
                        "name",
                        "stereotype",
                        "appliedStereotype",
                        "client",
                        "supplier",
                        "source",
                        "target",
                    }
                },
            )
            elements[element_id] = element
        current_id = element_id

        if owner_id and owner_id != element_id:
            _add_relation(
                relations,
                relation_id=f"contain:{owner_id}:{element_id}",
                kind="contains",
                source_id=owner_id,
                target_id=element_id,
                source_file=source_file,
            )

    _extract_explicit_relation(node, attrib, metaclass, source_file, relations, semantics)

    for child in list(node):
        _walk_xml(child, current_id, source_file, elements, relations, semantics)


def _extract_explicit_relation(
    node: ET.Element,
    attrib: dict[str, str],
    metaclass: str,
    source_file: str,
    relations: dict[tuple[str, str, str], ModelRelation],
    semantics: SemanticsConfig,
) -> None:
    source_id = attrib.get("client") or attrib.get("source")
    target_id = attrib.get("supplier") or attrib.get("target")

    if not source_id:
        source_id = attrib.get("end1")
    if not target_id:
        target_id = attrib.get("end2")

    if source_id and target_id:
        relation_id = _first(attrib, ID_KEYS) or f"rel:{id(node)}"
        _add_relation(
            relations,
            relation_id=relation_id,
            kind=_normalize_relation_kind(metaclass, strip_ns(node.tag), semantics),
            source_id=source_id,
            target_id=target_id,
            source_file=source_file,
            properties={
                k: v
                for k, v in attrib.items()
                if k not in {"client", "supplier", "source", "target", "end1", "end2"}
            },
        )


def _add_relation(
    relations: dict[tuple[str, str, str], ModelRelation],
    relation_id: str,
    kind: str,
    source_id: str,
    target_id: str,
    source_file: str,
    properties: dict[str, str] | None = None,
) -> None:
    key = (kind, source_id, target_id)
    if key in relations:
        return
    relations[key] = ModelRelation(
        relation_id=relation_id,
        kind=kind,
        source_id=source_id,
        target_id=target_id,
        source_file=source_file,
        properties=properties or {},
    )


def _normalize_kind(metaclass: str, tag: str, semantics: SemanticsConfig) -> str:
    metaclass_l = metaclass.lower()
    for needle, mapped in semantics.kind_rules.items():
        if needle in metaclass_l:
            return mapped

    if "block" in metaclass_l:
        return "Block"
    if "requirement" in metaclass_l:
        return "Requirement"
    if "port" in metaclass_l:
        return "Port"
    if "interface" in metaclass_l:
        return "Interface"
    if "property" in metaclass_l:
        return "Property"
    if "connector" in metaclass_l:
        return "Connector"
    return strip_ns(tag)


def _normalize_relation_kind(metaclass: str, tag: str, semantics: SemanticsConfig) -> str:
    metaclass_l = metaclass.lower()
    for needle, mapped in semantics.relation_rules.items():
        if needle in metaclass_l:
            return mapped

    if "abstraction" in metaclass_l and "allocate" in metaclass_l:
        return "allocate"
    if "dependency" in metaclass_l:
        return "dependency"
    if "association" in metaclass_l:
        return "association"
    if "connector" in metaclass_l:
        return "connector"
    return tag


def normalize_attrib(raw: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in raw.items():
        local = strip_ns(key)
        out[local] = value
        if "}" in key and local in {"id", "type"}:
            out.setdefault(f"xmi:{local}", value)
    return out


def _first(attrib: dict[str, str], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        if key in attrib:
            return attrib[key]
        suffix = key.split(":", 1)[-1]
        if suffix in attrib:
            return attrib[suffix]
    return None


def strip_ns(value: str) -> str:
    if "}" in value:
        return value.split("}", 1)[1]
    return value
