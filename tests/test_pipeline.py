from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from sysml_migration.mdzip_reader import parse_mdzip
from sysml_migration.render import write_dot_graph, write_open_json, write_sysml_v2_text
from sysml_migration.semantics import load_semantics
from sysml_migration.transform import to_open_model


class PipelineTests(unittest.TestCase):
    def test_end_to_end_from_mdzip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive = root / "sample.mdzip"
            out_dir = root / "out"
            out_dir.mkdir()

            xml_payload = """
            <root xmlns:xmi="http://www.omg.org/XMI">
              <packagedElement xmi:type="sysml:Block" xmi:id="A1" name="Vehicle" />
              <packagedElement xmi:type="sysml:Block" xmi:id="A2" name="Engine" />
              <connector xmi:type="uml:Association" xmi:id="R1" client="A1" supplier="A2" />
            </root>
            """.strip()

            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("model.xml", xml_payload)

            parsed = parse_mdzip(archive)
            self.assertEqual(len(parsed.elements), 3)
            self.assertEqual(len(parsed.relations), 1)
            self.assertEqual(parsed.relations[0].kind, "association")

            chunked = to_open_model(parsed, model_id="sample", chunk_size=2)
            self.assertEqual(chunked.element_count, 3)
            self.assertEqual(len(chunked.chunks), 2)

            open_path = write_open_json(chunked, out_dir)
            txt_path = write_sysml_v2_text(parsed, namespace="Demo", out_dir=out_dir)
            dot_path = write_dot_graph(parsed, out_dir)

            self.assertTrue(open_path.exists())
            self.assertTrue(txt_path.exists())
            self.assertTrue(dot_path.exists())

            payload = json.loads(open_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["model_id"], "sample")
            self.assertEqual(payload["relation_count"], 1)
            self.assertEqual(payload["chunks"][0]["stats"]["element_kinds"]["Block"], 2)

    def test_extracts_containment_and_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "nested.mdzip"
            xml_payload = """
            <root xmlns:xmi="http://www.omg.org/XMI">
              <packagedElement xmi:type="sysml:Block" xmi:id="B1" name="System">
                <ownedAttribute xmi:type="uml:Port" xmi:id="P1" name="InputPort" type="IF1"/>
              </packagedElement>
              <packagedElement xmi:type="uml:Interface" xmi:id="IF1" name="DataIf"/>
              <packagedElement xmi:type="uml:Dependency" xmi:id="D1" client="B1" supplier="IF1"/>
            </root>
            """.strip()

            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("model.xmi", xml_payload)

            parsed = parse_mdzip(archive)
            by_id = {e.element_id: e for e in parsed.elements}
            rel_kinds = {r.kind for r in parsed.relations}

            self.assertIn("B1", by_id)
            self.assertIn("P1", by_id)
            self.assertEqual(by_id["P1"].owner_id, "B1")
            self.assertEqual(by_id["P1"].kind, "Port")
            self.assertIn("contains", rel_kinds)
            self.assertIn("dependency", rel_kinds)

    def test_applies_uploaded_semantics_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            semantics_path = root / "semantics.json"
            semantics_path.write_text(
                json.dumps(
                    {
                        "kind_rules": {"constraintblock": "ConstraintDefinition"},
                        "relation_rules": {"satisfy": "satisfy"},
                        "text_keywords": {"ConstraintDefinition": "constraint def"},
                    }
                ),
                encoding="utf-8",
            )
            semantics = load_semantics(semantics_path)

            archive = root / "semantics.mdzip"
            xml_payload = """
            <root xmlns:xmi="http://www.omg.org/XMI">
              <packagedElement xmi:type="sysml:ConstraintBlock" xmi:id="C1" name="MassBalance" />
              <packagedElement xmi:type="uml:Dependency" xmi:id="S1" client="C1" supplier="C1" stereotype="satisfy" />
            </root>
            """.strip()

            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("model.xml", xml_payload)

            parsed = parse_mdzip(archive, semantics=semantics)
            self.assertEqual(parsed.elements[0].kind, "ConstraintDefinition")

            out_dir = root / "out"
            out_dir.mkdir()
            text_path = write_sysml_v2_text(parsed, "Demo", out_dir, semantics=semantics)
            text = text_path.read_text(encoding="utf-8")
            self.assertIn("constraint def MassBalance", text)


if __name__ == "__main__":
    unittest.main()
