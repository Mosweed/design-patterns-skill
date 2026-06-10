#!/usr/bin/env python3
"""Tests for the UML builder (``uml.py``) and its ``uml_data/`` data files.

Dependency-free: run it directly and it exits non-zero on the first failing
suite, printing which test and why —

    python3 scripts/test_uml.py

It is also a valid pytest module (every check is a ``test_*`` function), so
``pytest scripts/test_uml.py`` works if you have pytest installed. CI and the
pre-commit hook call it as a plain script, so no extra dependency is needed.

What it guards:
  * every ``uml_data/*.json`` parses and matches the documented schema;
  * every relation's endpoints name a class defined in the same file (a typo
    would otherwise invent a phantom class in Mermaid or silently vanish in
    draw.io);
  * the 23 reference patterns and the 23 data files line up one-to-one;
  * all three renderers produce sane output for all 23 patterns (Mermaid is a
    ``classDiagram`` with tilde generics; PlantUML keeps angle generics; draw.io
    is well-formed XML whose HTML labels are double-escaped as draw.io expects);
  * the CLI's ``--list``/``--all``/unknown-slug paths behave.
"""
from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import uml  # noqa: E402  (path set up just above)

ROOT = SCRIPT_DIR.parent                      # plugins/design-patterns
REFERENCES = ROOT / "references"
DATA_DIR = uml.DATA_DIR

VALID_KINDS = {"class", "abstract", "interface"}
VALID_VIS = {"+", "-", "#", "~"}
VALID_RELATIONS = set(uml.RELATION_ARROWS)    # the renderer's own arrow table

EXPECTED_PATTERN_COUNT = 23
EXPECTED_FORMATS = set(uml.RENDERERS)


def _slugs() -> list[str]:
    return list(uml.available())


def _specs():
    """Yield (slug, path, spec) for every data file."""
    for slug, path in uml.available().items():
        yield slug, path, json.loads(path.read_text(encoding="utf-8"))


# ---- data-file schema ------------------------------------------------------

def test_pattern_count():
    slugs = _slugs()
    assert len(slugs) == EXPECTED_PATTERN_COUNT, (
        f"expected {EXPECTED_PATTERN_COUNT} data files, found {len(slugs)}: {slugs}"
    )


def test_data_schema():
    for slug, path, spec in _specs():
        where = path.name
        assert isinstance(spec.get("title"), str) and spec["title"].strip(), \
            f"{where}: missing/empty 'title'"
        assert spec.get("intent"), f"{where}: missing/empty 'intent'"
        assert isinstance(spec.get("classes"), list) and spec["classes"], \
            f"{where}: 'classes' must be a non-empty list"
        for cls in spec["classes"]:
            name = cls.get("name")
            assert name, f"{where}: a class is missing 'name'"
            kind = cls.get("kind", "class")
            assert kind in VALID_KINDS, f"{where}: {name} has bad kind {kind!r}"
            for attr in cls.get("attributes", []):
                assert attr.get("name"), f"{where}: {name} has an unnamed attribute"
                assert attr.get("vis", "+") in VALID_VIS, \
                    f"{where}: {name}.{attr.get('name')} bad visibility {attr.get('vis')!r}"
            for meth in cls.get("methods", []):
                assert meth.get("name"), f"{where}: {name} has an unnamed method"
                assert meth.get("vis", "+") in VALID_VIS, \
                    f"{where}: {name}.{meth.get('name')} bad visibility {meth.get('vis')!r}"
                for param in meth.get("params", []):
                    assert param.get("name"), \
                        f"{where}: {name}.{meth['name']} has an unnamed param"


def test_relation_integrity():
    """Every relation endpoint must name a class defined in the same file."""
    for slug, path, spec in _specs():
        names = {c["name"] for c in spec["classes"]}
        for rel in spec.get("relations", []):
            assert rel.get("type") in VALID_RELATIONS, \
                f"{path.name}: bad relation type {rel.get('type')!r}"
            for end in ("from", "to"):
                assert rel.get(end) in names, (
                    f"{path.name}: relation {end}={rel.get(end)!r} is not a "
                    f"defined class (have {sorted(names)})"
                )


def test_reference_coverage():
    """The numbered reference files and the data files line up one-to-one, by
    their ``NN-slug`` stem — so adding a pattern can't leave a missing diagram."""
    ref_stems = {p.stem for p in REFERENCES.glob("*/[0-9]*-*.md")}
    data_stems = {p.stem for p in DATA_DIR.glob("[0-9]*-*.json")}
    assert ref_stems == data_stems, (
        "reference files and uml_data files disagree.\n"
        f"  only in references: {sorted(ref_stems - data_stems)}\n"
        f"  only in uml_data:   {sorted(data_stems - ref_stems)}"
    )


# ---- renderers -------------------------------------------------------------

def test_all_formats_render_nonempty():
    for slug in _slugs():
        for fmt in EXPECTED_FORMATS:
            out = uml.render(slug, fmt)
            assert isinstance(out, str) and out.strip(), \
                f"{slug} -> {fmt} produced empty output"


def test_mermaid_structure():
    for slug, path, spec in _specs():
        out = uml.to_mermaid(spec)
        assert out.startswith("classDiagram"), f"{slug}: mermaid lacks classDiagram header"
        for cls in spec["classes"]:
            assert f"class {cls['name']}" in out, \
                f"{slug}: mermaid missing class {cls['name']}"
        # Generics must use tildes, never angle brackets, in Mermaid.
        for cls in spec["classes"]:
            for member in cls.get("attributes", []) + cls.get("methods", []):
                tp = member.get("type") or member.get("returns") or ""
                if "<" in tp:
                    angle = tp
                    tilde = tp.replace("<", "~").replace(">", "~")
                    assert angle not in out, f"{slug}: mermaid leaked angle generic {angle!r}"
                    assert tilde in out, f"{slug}: mermaid missing tilde generic {tilde!r}"


def test_plantuml_structure():
    for slug, path, spec in _specs():
        out = uml.to_plantuml(spec)
        assert out.startswith("@startuml") and out.rstrip().endswith("@enduml"), \
            f"{slug}: plantuml not wrapped in @startuml/@enduml"
        assert f"title {spec['title']} Pattern" in out, f"{slug}: plantuml missing title"
        for cls in spec["classes"]:
            assert cls["name"] in out, f"{slug}: plantuml missing class {cls['name']}"


def test_drawio_is_valid_xml():
    for slug in _slugs():
        out = uml.render(slug, "drawio")
        try:
            ET.fromstring(out)
        except ET.ParseError as exc:  # pragma: no cover - only on regression
            raise AssertionError(f"{slug}: draw.io output is not valid XML: {exc}")


def test_drawio_edges_match_relations():
    """One vertex per class, one edge per relation — proves draw.io drops
    nothing (its renderer silently skips edges whose endpoints it can't find)."""
    for slug, path, spec in _specs():
        root = ET.fromstring(uml.render(slug, "drawio"))
        vertices = [c for c in root.iter("mxCell") if c.get("vertex") == "1"]
        edges = [c for c in root.iter("mxCell") if c.get("edge") == "1"]
        assert len(vertices) == len(spec["classes"]), \
            f"{slug}: {len(vertices)} draw.io vertices for {len(spec['classes'])} classes"
        assert len(edges) == len(spec.get("relations", [])), \
            f"{slug}: {len(edges)} draw.io edges for {len(spec.get('relations', []))} relations"


def test_drawio_box_height_includes_stereotype():
    """Each draw.io box is tall enough for its members, plus one extra row for
    the «stereotype» line on abstract/interface boxes (else it clips)."""
    for slug, path, spec in _specs():
        root = ET.fromstring(uml.render(slug, "drawio"))
        vertices = [c for c in root.iter("mxCell") if c.get("vertex") == "1"]
        assert len(vertices) == len(spec["classes"])
        # Vertices are emitted in class order, so zip is safe.
        for cls, cell in zip(spec["classes"], vertices):
            geom = cell.find("mxGeometry")
            height = float(geom.get("height"))
            members = len(cls.get("attributes", [])) + len(cls.get("methods", []))
            stereotype = 1 if cls.get("kind", "class") in ("abstract", "interface") else 0
            expected = max(40, 36 + 18 * (members + stereotype))
            assert height == expected, (
                f"{slug}: {cls['name']} box height {height} != {expected} "
                f"(members={members}, stereotype={stereotype})"
            )


def test_drawio_generics_are_html_escaped():
    """draw.io HTML labels are stored XML-escaped; a generic like List<Observer>
    must survive as the HTML entity form, never as a raw tag that the label
    renderer would swallow."""
    root = ET.fromstring(uml.render("observer", "drawio"))
    values = [c.get("value", "") for c in root.iter("mxCell")]
    subject = next(v for v in values if "observers" in v)
    assert "List&lt;Observer&gt;" in subject, \
        f"draw.io generic not HTML-escaped in label: {subject!r}"
    assert "List<Observer>" not in subject, \
        "draw.io label contains a raw <Observer> tag"


# ---- StarUML (.mdj) --------------------------------------------------------

def _walk_mdj(node, ids, refs, types):
    """Collect every _id, every $ref target, and a _type histogram."""
    if isinstance(node, dict):
        if "_id" in node:
            ids.append(node["_id"])
        if set(node.keys()) == {"$ref"}:
            refs.append(node["$ref"])
        if node.get("_type"):
            types[node["_type"]] = types.get(node["_type"], 0) + 1
        for value in node.values():
            _walk_mdj(value, ids, refs, types)
    elif isinstance(node, list):
        for value in node:
            _walk_mdj(value, ids, refs, types)


def test_staruml_is_valid_json():
    for slug in _slugs():
        data = json.loads(uml.render(slug, "staruml"))  # raises on bad JSON
        assert data.get("_type") == "Project", f"{slug}: root is not a StarUML Project"


def test_staruml_ids_unique_and_refs_resolve():
    """Every $ref must point at a defined _id and ids must be unique — a dangling
    or duplicated reference makes StarUML refuse to open the file."""
    for slug in _slugs():
        data = json.loads(uml.render(slug, "staruml"))
        ids, refs, _ = [], [], {}
        _walk_mdj(data, ids, refs, _)
        assert len(ids) == len(set(ids)), f"{slug}: duplicate _id in .mdj"
        dangling = [r for r in refs if r not in set(ids)]
        assert not dangling, f"{slug}: dangling $ref(s) {dangling[:3]}"


def test_staruml_covers_model_and_diagram():
    """One model classifier and one class-view per class, one edge-view per
    relation — nothing dropped between data, model, and diagram."""
    for slug, path, spec in _specs():
        data = json.loads(uml.render(slug, "staruml"))
        types: dict[str, int] = {}
        _walk_mdj(data, [], [], types)
        classifiers = types.get("UMLClass", 0) + types.get("UMLInterface", 0)
        assert classifiers == len(spec["classes"]), \
            f"{slug}: {classifiers} model classifiers for {len(spec['classes'])} classes"
        assert types.get("UMLClassView", 0) == len(spec["classes"]), \
            f"{slug}: class-view count != class count"
        edge_views = sum(types.get(t, 0) for t in (
            "UMLGeneralizationView", "UMLInterfaceRealizationView",
            "UMLDependencyView", "UMLAssociationView"))
        assert edge_views == len(spec.get("relations", [])), \
            f"{slug}: {edge_views} edge views for {len(spec.get('relations', []))} relations"


def test_staruml_interface_and_abstract_kinds():
    """`interface` classes become UMLInterface; `abstract` classes carry
    isAbstract so StarUML renders them correctly."""
    for slug, path, spec in _specs():
        data = json.loads(uml.render(slug, "staruml"))
        by_name = {}

        def index(node):
            if isinstance(node, dict):
                if node.get("_type") in ("UMLClass", "UMLInterface") and "name" in node:
                    by_name[node["name"]] = node
                for v in node.values():
                    index(v)
            elif isinstance(node, list):
                for v in node:
                    index(v)
        index(data)
        for cls in spec["classes"]:
            obj = by_name.get(cls["name"])
            assert obj, f"{slug}: class {cls['name']} missing from .mdj model"
            kind = cls.get("kind", "class")
            if kind == "interface":
                assert obj["_type"] == "UMLInterface", \
                    f"{slug}: {cls['name']} should be a UMLInterface"
            else:
                assert obj["_type"] == "UMLClass", \
                    f"{slug}: {cls['name']} should be a UMLClass"
                if kind == "abstract":
                    assert obj.get("isAbstract") is True, \
                        f"{slug}: abstract {cls['name']} missing isAbstract"


# ---- slug handling & CLI ---------------------------------------------------

def test_title_slug_roundtrip():
    """slugify(title) lands back on the same data file, so a user can ask for a
    pattern by its human title."""
    available = uml.available()
    for slug, path, spec in _specs():
        assert uml.slugify(spec["title"]) in available, \
            f"{path.name}: slugify({spec['title']!r}) not found in available patterns"


def test_slugify_examples():
    assert uml.slugify("Observer Pattern") == "observer"
    assert uml.slugify("Chain of Responsibility") == "chain-of-responsibility"
    assert uml.slugify("Template Method") == "template-method"
    assert uml.slugify("A & B") == "a-and-b"


def test_unknown_slug_raises():
    try:
        uml.load("does-not-exist")
    except KeyError:
        return
    raise AssertionError("uml.load() should raise KeyError on an unknown slug")


def test_cli_paths():
    script = str(uml.__file__)

    listing = subprocess.run([sys.executable, script, "--list"],
                             capture_output=True, text=True, check=True)
    listed = [ln for ln in listing.stdout.splitlines() if ln.strip()]
    assert len(listed) == EXPECTED_PATTERN_COUNT, \
        f"--list printed {len(listed)} slugs, expected {EXPECTED_PATTERN_COUNT}"

    one = subprocess.run([sys.executable, script, "Observer Pattern"],
                         capture_output=True, text=True, check=True)
    assert one.stdout.startswith("classDiagram"), "CLI default format should be Mermaid"

    bad = subprocess.run([sys.executable, script, "no-such-pattern"],
                         capture_output=True, text=True)
    assert bad.returncode != 0, "unknown pattern should exit non-zero"


def test_cli_out_writes_utf8_file():
    """`-o` writes the diagram as UTF-8 (no BOM) so .mdj/.drawio survive on
    Windows, where '>' in PowerShell would emit UTF-16."""
    import tempfile
    script = str(uml.__file__)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "observer.mdj"
        res = subprocess.run([sys.executable, script, "observer", "-f", "staruml",
                              "-o", str(out)], capture_output=True, text=True, check=True)
        assert out.exists(), "-o did not create the file"
        raw = out.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), "file has a UTF-8 BOM"
        assert not raw.startswith(b"\xff\xfe"), "file is UTF-16, not UTF-8"
        json.loads(raw.decode("utf-8"))  # parses as JSON
        assert res.stdout.strip() == "", "with -o nothing should print to stdout"


# ---- standalone runner -----------------------------------------------------

def main() -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    failures: list[str] = []
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - report any failure uniformly
            failures.append(f"{name}: {exc}")
            print(f"  FAIL  {name}")
        else:
            print(f"  ok    {name}")
    print()
    if failures:
        print(f"UML tests FAILED ({len(failures)}/{len(tests)}):")
        for f in failures:
            print(f"  - {f}")
        raise SystemExit(1)
    print(f"UML tests passed: {len(tests)} checks over "
          f"{EXPECTED_PATTERN_COUNT} patterns x {len(EXPECTED_FORMATS)} formats.")


if __name__ == "__main__":
    main()
