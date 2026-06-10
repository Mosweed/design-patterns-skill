#!/usr/bin/env python3
"""UML class-diagram builder for the 23 GoF design patterns.

Each pattern's canonical structure lives as a small JSON file in
``uml_data/<NN>-<slug>.json`` (same numbering as the reference files). This
script renders that structure to Mermaid (default) or PlantUML, so Claude — or
a human — can drop a diagram straight into Markdown or a PlantUML renderer
without hand-drawing it.

Usage:
    python uml.py observer                  # Mermaid for one pattern
    python uml.py "Observer Pattern" -f plantuml
    python uml.py --list                    # list available pattern slugs
    python uml.py --all                     # every pattern, Mermaid
    python uml.py --all -f plantuml         # every pattern, PlantUML

The data model (one JSON file per pattern):
    {
      "title": "Observer",
      "intent": "one-line intent",
      "classes": [
        {
          "name": "Subject",
          "kind": "abstract",            # "class" | "abstract" | "interface"
          "attributes": [{"vis": "-", "name": "observers", "type": "List<Observer>"}],
          "methods": [{"vis": "+", "name": "attach",
                       "params": [{"name": "o", "type": "Observer"}],
                       "returns": null}]
        }
      ],
      "relations": [
        {"from": "ConcreteSubject", "to": "Subject", "type": "inheritance"},
        {"from": "Subject", "to": "Observer", "type": "aggregation", "label": "observers"}
      ]
    }

Relation types: inheritance, realization, association, aggregation,
composition, dependency. ``label`` is optional.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "uml_data"

# Arrow tokens are the same in Mermaid and PlantUML; only the member syntax and
# class headers differ between the two.
RELATION_ARROWS = {
    "inheritance": "<|--",   # rendered as: parent <|-- child
    "realization": "<|..",   # interface <|.. implementor
    "association": "-->",    # source --> target
    "aggregation": "o--",    # whole o-- part
    "composition": "*--",    # whole *-- part
    "dependency": "..>",     # source ..> target
}
# inheritance/realization read parent-first; the rest read source-first.
PARENT_FIRST = {"inheritance", "realization"}


def slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\bpattern\b", "", name)
    name = name.strip().replace("&", "and")
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    return name


def available() -> dict[str, Path]:
    """Map slug -> json path, derived from the NN-slug.json filenames."""
    out: dict[str, Path] = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        slug = re.sub(r"^\d+-", "", path.stem)
        out[slug] = path
    return out


def load(slug: str) -> dict:
    files = available()
    if slug not in files:
        raise KeyError(slug)
    return json.loads(files[slug].read_text(encoding="utf-8"))


# ---- Mermaid --------------------------------------------------------------

def _mermaid_type(type_str: str | None) -> str:
    # Mermaid expresses generics with tildes: List<Observer> -> List~Observer~
    return (type_str or "").replace("<", "~").replace(">", "~")


def _mermaid_member(member: dict, is_method: bool) -> str:
    vis = member.get("vis", "+")
    if is_method:
        params = ", ".join(
            f"{_mermaid_type(p.get('type'))} {p['name']}".strip()
            for p in member.get("params", [])
        )
        ret = _mermaid_type(member.get("returns"))
        tail = f" {ret}" if ret else ""
        return f"{vis}{member['name']}({params}){tail}"
    type_str = _mermaid_type(member.get("type"))
    return f"{vis}{type_str} {member['name']}".strip()


def to_mermaid(spec: dict) -> str:
    lines = ["classDiagram"]
    for cls in spec["classes"]:
        lines.append(f"    class {cls['name']} {{")
        kind = cls.get("kind", "class")
        if kind in ("abstract", "interface"):
            lines.append(f"        <<{kind}>>")
        for attr in cls.get("attributes", []):
            lines.append(f"        {_mermaid_member(attr, is_method=False)}")
        for method in cls.get("methods", []):
            lines.append(f"        {_mermaid_member(method, is_method=True)}")
        lines.append("    }")
    for rel in spec.get("relations", []):
        arrow = RELATION_ARROWS[rel["type"]]
        if rel["type"] in PARENT_FIRST:
            left, right = rel["to"], rel["from"]
        else:
            left, right = rel["from"], rel["to"]
        line = f"    {left} {arrow} {right}"
        if rel.get("label"):
            line += f" : {rel['label']}"
        lines.append(line)
    return "\n".join(lines)


# ---- PlantUML -------------------------------------------------------------

def _plant_member(member: dict, is_method: bool) -> str:
    vis = member.get("vis", "+")
    if is_method:
        params = ", ".join(
            f"{p['name']}: {p['type']}" if p.get("type") else p["name"]
            for p in member.get("params", [])
        )
        ret = member.get("returns")
        tail = f": {ret}" if ret else ""
        return f"{vis}{member['name']}({params}){tail}"
    type_str = member.get("type")
    return f"{vis}{member['name']}: {type_str}" if type_str else f"{vis}{member['name']}"


def to_plantuml(spec: dict) -> str:
    header = {"class": "class", "abstract": "abstract class", "interface": "interface"}
    lines = ["@startuml", f"title {spec['title']} Pattern", ""]
    for cls in spec["classes"]:
        kind = header.get(cls.get("kind", "class"), "class")
        lines.append(f"{kind} {cls['name']} {{")
        for attr in cls.get("attributes", []):
            lines.append(f"  {_plant_member(attr, is_method=False)}")
        for method in cls.get("methods", []):
            lines.append(f"  {_plant_member(method, is_method=True)}")
        lines.append("}")
    lines.append("")
    for rel in spec.get("relations", []):
        arrow = RELATION_ARROWS[rel["type"]]
        if rel["type"] in PARENT_FIRST:
            left, right = rel["to"], rel["from"]
        else:
            left, right = rel["from"], rel["to"]
        line = f"{left} {arrow} {right}"
        if rel.get("label"):
            line += f" : {rel['label']}"
        lines.append(line)
    lines.append("@enduml")
    return "\n".join(lines)


# ---- draw.io (diagrams.net) -----------------------------------------------

# Edge styles per relation type. draw.io reads the arrow at source/target ends.
# inheritance/realization: hollow triangle at the parent end (the "to").
# aggregation/composition: diamond at the whole end (the "from").
_DRAWIO_EDGE = {
    "inheritance": "endArrow=block;endFill=0;html=1;",
    "realization": "endArrow=block;endFill=0;dashed=1;html=1;",
    "association": "endArrow=open;html=1;",
    "aggregation": "startArrow=diamondThin;startFill=0;endArrow=none;html=1;",
    "composition": "startArrow=diamondThin;startFill=1;endArrow=none;html=1;",
    "dependency": "endArrow=open;dashed=1;html=1;",
}


def _xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _html_escape(text: str) -> str:
    # So generics like List<Observer> show as literal text inside the HTML label
    # instead of being read as an HTML tag by draw.io's renderer.
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _drawio_label(cls: dict) -> str:
    """An HTML label (stereotype + bold name, a rule, then members). draw.io
    stores HTML labels XML-escaped in the cell's value attribute, so the caller
    runs the whole string through _xml_escape once — hence the double escaping
    of member text (HTML-escaped here, XML-escaped by the caller)."""
    name = _html_escape(cls["name"])
    kind = cls.get("kind", "class")
    if kind in ("abstract", "interface"):
        # &#171;/&#187; are guillemets («»); kept as numeric refs to stay ASCII.
        name = f"&#171;{kind}&#187;<br>{name}"
    members = [_plant_member(a, is_method=False) for a in cls.get("attributes", [])]
    members += [_plant_member(m, is_method=True) for m in cls.get("methods", [])]
    body = "<br>".join(_html_escape(m) for m in members)
    label = f"<b>{name}</b>"
    if body:
        label += f'<hr size="1">{body}'
    return label


def to_drawio(spec: dict) -> str:
    cells: list[str] = []
    ids: dict[str, str] = {}
    # Lay classes out in a grid, ~3 columns.
    cols = 3
    col_w, row_h, x0, y0 = 240, 200, 40, 40
    for i, cls in enumerate(spec["classes"]):
        cid = f"n{i}"
        ids[cls["name"]] = cid
        col, row = i % cols, i // cols
        n_members = len(cls.get("attributes", [])) + len(cls.get("methods", []))
        height = max(40, 36 + 18 * n_members)
        x, y = x0 + col * col_w, y0 + row * row_h
        style = ("rounded=0;whiteSpace=wrap;html=1;verticalAlign=top;"
                 "align=left;spacingLeft=6;spacingRight=6;overflow=hidden;")
        cells.append(
            f'        <mxCell id="{cid}" value="{_xml_escape(_drawio_label(cls))}" '
            f'style="{style}" vertex="1" parent="1">\n'
            f'          <mxGeometry x="{x}" y="{y}" width="200" height="{height}" as="geometry"/>\n'
            f'        </mxCell>'
        )
    for j, rel in enumerate(spec.get("relations", [])):
        src, tgt = ids.get(rel["from"]), ids.get(rel["to"])
        if not src or not tgt:
            continue  # relation references a class not in the diagram
        style = _DRAWIO_EDGE.get(rel["type"], "endArrow=open;html=1;")
        label = _xml_escape(rel.get("label", ""))
        cells.append(
            f'        <mxCell id="e{j}" value="{label}" style="{style}" '
            f'edge="1" parent="1" source="{src}" target="{tgt}">\n'
            f'          <mxGeometry relative="1" as="geometry"/>\n'
            f'        </mxCell>'
        )
    body = "\n".join(cells)
    title = _xml_escape(spec["title"])
    return (
        '<mxfile host="design-patterns-uml">\n'
        f'  <diagram name="{title} Pattern">\n'
        '    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" '
        'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        'pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">\n'
        '      <root>\n'
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f'{body}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>'
    )


RENDERERS = {"mermaid": to_mermaid, "plantuml": to_plantuml, "drawio": to_drawio}


def render(slug: str, fmt: str) -> str:
    return RENDERERS[fmt](load(slug))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pattern", nargs="?", help="pattern slug or title (e.g. observer)")
    parser.add_argument("-f", "--format", choices=RENDERERS, default="mermaid")
    parser.add_argument("--list", action="store_true", help="list available patterns")
    parser.add_argument("--all", action="store_true", help="render every pattern")
    args = parser.parse_args()

    files = available()
    if args.list:
        for slug in files:
            print(slug)
        return

    if args.all:
        chunks = []
        for slug in files:
            chunks.append(f"# {slug}\n{render(slug, args.format)}")
        print("\n\n".join(chunks))
        return

    if not args.pattern:
        parser.error("give a pattern slug/title, or use --list or --all")

    slug = slugify(args.pattern)
    if slug not in files:
        print(f"Unknown pattern: {args.pattern!r} (slug {slug!r}). "
              f"Try --list.", file=sys.stderr)
        raise SystemExit(1)
    print(render(slug, args.format))


if __name__ == "__main__":
    main()
