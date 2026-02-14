from __future__ import annotations

import argparse
from pathlib import Path

from .mdzip_reader import parse_mdzip
from .render import write_dot_graph, write_open_json, write_sysml_v2_text
from .semantics import load_semantics
from .transform import to_open_model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sysml-migrate-v1",
        description="Convert SysML v1 .mdzip model content into open JSON + SysML v2 text + graph",
    )
    parser.add_argument("input_mdzip", help="Path to input .mdzip file")
    parser.add_argument("--out", default="out", help="Output directory")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=250,
        help="Maximum elements per chunk in open JSON output",
    )
    parser.add_argument(
        "--namespace",
        default="MigratedModel",
        help="Namespace/package name used in SysML v2 text output",
    )
    parser.add_argument(
        "--semantics",
        default=None,
        help="Optional JSON semantics mapping file with kind/relation/text keyword overrides",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    semantics = load_semantics(args.semantics)
    model = parse_mdzip(args.input_mdzip, semantics=semantics)
    open_model = to_open_model(
        model=model,
        model_id=Path(args.input_mdzip).stem,
        chunk_size=args.chunk_size,
    )

    open_json_path = write_open_json(open_model, out_dir)
    text_path = write_sysml_v2_text(
        model,
        namespace=args.namespace,
        out_dir=out_dir,
        semantics=semantics,
    )
    dot_path = write_dot_graph(model, out_dir)

    print(f"Converted: {args.input_mdzip}")
    if args.semantics:
        print(f"- semantics file:   {args.semantics}")
    print(f"- open model json: {open_json_path}")
    print(f"- sysml v2 text:   {text_path}")
    print(f"- graph dot:       {dot_path}")


if __name__ == "__main__":
    main()
