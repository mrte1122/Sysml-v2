# SysML v1 `.mdzip` to SysML v2 Migration Tool

This repository contains a CLI that converts SysML v1 `.mdzip` archives into three synchronized outputs:

1. `model.open.json` (chunked open exchange payload)
2. `model.sysmlv2.kerml` (SysML v2-style text)
3. `model.graph.dot` (graph view for visualization)

The parser recognizes common UML/SysML semantics (blocks, requirements, ports, connectors, dependencies, associations, containment), and you can now provide your **uploaded language semantics** as a JSON mapping file.

## How it works

```text
.mdzip (zip archive)
  └─ XML/XMI/UML files
      └─ semantic extraction
          ├─ elements (id, kind, name, owner, type, stereotype, properties)
          ├─ relations (contains, dependency, association, connector, ...)
          └─ chunked open model
              ├─ model.open.json
              ├─ model.sysmlv2.kerml
              └─ model.graph.dot
```

## Semantics mapping input

You can supply a JSON file with three optional sections:

- `kind_rules`: substring match on source metaclass/type to mapped kind
- `relation_rules`: substring match on relation metaclass/type to mapped relation
- `text_keywords`: mapped kind to SysML v2 text keyword used in `.kerml` rendering

Example mapping file:

`semantics/sysmlv2-language-semantics.example.json`

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

sysml-migrate-v1 ./path/to/model.mdzip \
  --out ./out \
  --chunk-size 250 \
  --namespace MyModel \
  --semantics ./semantics/sysmlv2-language-semantics.example.json
```

## CLI

```bash
sysml-migrate-v1 INPUT_MDZIP --out OUTPUT_DIR [--chunk-size 250] [--namespace MyModel] [--semantics FILE.json]
```

## Testing

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```
