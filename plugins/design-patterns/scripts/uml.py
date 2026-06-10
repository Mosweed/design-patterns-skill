#!/usr/bin/env python3
"""UML class-diagram builder for the 23 GoF design patterns.

Each pattern's canonical structure lives as a small JSON file in
``uml_data/<NN>-<slug>.json`` (same numbering as the reference files). This
script renders that structure to four interchangeable formats, so Claude — or a
human — can drop a diagram straight into Markdown, a PlantUML renderer, draw.io,
or StarUML without hand-drawing it:

    mermaid   (default) a ```mermaid `classDiagram` block for Markdown/GitHub
    plantuml  an @startuml...@enduml block
    drawio    an .drawio (mxGraph XML) file, editable in diagrams.net
    staruml   an .mdj (StarUML JSON) file with a laid-out class diagram,
              opens straight in StarUML via File > Open

Usage:
    python uml.py observer                  # Mermaid for one pattern
    python uml.py "Observer Pattern" -f plantuml
    python uml.py observer -f drawio -o observer.drawio
    python uml.py observer -f staruml -o observer.mdj   # -o writes UTF-8 (Windows-safe)
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
        # abstract/interface labels carry a «stereotype» line above the name, so
        # they need one extra row of height or the last member clips.
        stereotype_lines = 1 if cls.get("kind", "class") in ("abstract", "interface") else 0
        height = max(40, 36 + 18 * (n_members + stereotype_lines))
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


# ---- StarUML (.mdj) -------------------------------------------------------

# StarUML stores models as JSON (.mdj): a semantic model tree (UMLModel ->
# classes -> attributes/operations/relationships) and a parallel view tree (a
# UMLClassDiagram of positioned UMLClassViews with compartment sub-views). Both
# are cross-referenced by _id/$ref. We emit both so the file opens straight into
# StarUML showing a laid-out class diagram, not just a bare model tree. The
# structure here mirrors a real StarUML-saved file so its loader accepts it.

_STARUML_VIS = {"+": "public", "-": "private", "#": "protected", "~": "package"}
_STARUML_AGG = {"aggregation": "shared", "composition": "composite"}
# relation type -> (model element, diagram edge view). The relation's `from` is
# the edge tail (start), `to` is the head (the arrow/triangle/diamond end).
_STARUML_REL = {
    "inheritance": ("UMLGeneralization", "UMLGeneralizationView"),
    "realization": ("UMLInterfaceRealization", "UMLInterfaceRealizationView"),
    "dependency": ("UMLDependency", "UMLDependencyView"),
    "association": ("UMLAssociation", "UMLAssociationView"),
    "aggregation": ("UMLAssociation", "UMLAssociationView"),
    "composition": ("UMLAssociation", "UMLAssociationView"),
}


def to_staruml(spec: dict) -> str:
    counter = [0]

    def nid() -> str:                       # deterministic ids -> reproducible output
        counter[0] += 1
        return f"dp{counter[0]:04d}"

    def ref(i: str) -> dict:
        return {"$ref": i}

    classes = spec["classes"]
    project_id, model_id, diagram_id = nid(), nid(), nid()
    diagram_name = f"{spec['title']} Pattern"
    cls_id = {c["name"]: nid() for c in classes}

    # ---- model: classes / interfaces with their members ----
    model_classes: list[dict] = []
    attr_ids: dict[str, list[str]] = {}
    op_ids: dict[str, list[str]] = {}
    by_id: dict[str, dict] = {}

    for cls in classes:
        cid = cls_id[cls["name"]]
        kind = cls.get("kind", "class")
        ctype = "UMLInterface" if kind == "interface" else "UMLClass"
        obj = {"_type": ctype, "_id": cid, "_parent": ref(model_id), "name": cls["name"]}
        if kind == "abstract":
            obj["isAbstract"] = True            # StarUML italicises abstract names

        attrs, attr_ids[cls["name"]] = [], []
        for a in cls.get("attributes", []):
            aid = nid()
            attr_ids[cls["name"]].append(aid)
            am = {"_type": "UMLAttribute", "_id": aid, "_parent": ref(cid),
                  "name": a["name"],
                  "visibility": _STARUML_VIS.get(a.get("vis", "+"), "public")}
            if a.get("type"):
                am["type"] = a["type"]
            attrs.append(am)
        if attrs:
            obj["attributes"] = attrs

        ops, op_ids[cls["name"]] = [], []
        for m in cls.get("methods", []):
            oid = nid()
            op_ids[cls["name"]].append(oid)
            params = []
            for p in m.get("params", []):
                pm = {"_type": "UMLParameter", "_id": nid(), "_parent": ref(oid),
                      "name": p["name"]}
                if p.get("type"):
                    pm["type"] = p["type"]
                params.append(pm)
            if m.get("returns"):                # return type is a directed parameter
                params.append({"_type": "UMLParameter", "_id": nid(),
                               "_parent": ref(oid),
                               "type": m["returns"], "direction": "return"})
            om = {"_type": "UMLOperation", "_id": oid, "_parent": ref(cid),
                  "name": m["name"],
                  "visibility": _STARUML_VIS.get(m.get("vis", "+"), "public")}
            if params:
                om["parameters"] = params
            ops.append(om)
        if ops:
            obj["operations"] = ops

        by_id[cid] = obj
        model_classes.append(obj)

    # ---- model: relationships, each owned by its source class ----
    rel_specs: list[tuple[dict, str, str, tuple | None]] = []
    for rel in spec.get("relations", []):
        mtype, vtype = _STARUML_REL[rel["type"]]
        rid, src, tgt = nid(), rel["from"], rel["to"]
        end_ids = None
        if mtype == "UMLAssociation":
            e1id, e2id = nid(), nid()
            end1 = {"_type": "UMLAssociationEnd", "_id": e1id, "_parent": ref(rid),
                    "reference": ref(cls_id[src])}
            end2 = {"_type": "UMLAssociationEnd", "_id": e2id, "_parent": ref(rid),
                    "reference": ref(cls_id[tgt])}
            if rel["type"] in _STARUML_AGG:     # diamond sits on the whole (the tail)
                end1["aggregation"] = _STARUML_AGG[rel["type"]]
            mobj = {"_type": mtype, "_id": rid, "_parent": ref(cls_id[src]),
                    "end1": end1, "end2": end2}
            end_ids = (e1id, e2id)
        else:
            mobj = {"_type": mtype, "_id": rid, "_parent": ref(cls_id[src]),
                    "source": ref(cls_id[src]), "target": ref(cls_id[tgt])}
        if rel.get("label"):
            mobj["name"] = rel["label"]
        by_id[cls_id[src]].setdefault("ownedElements", []).append(mobj)
        rel_specs.append((rel, rid, vtype, end_ids))

    # ---- view: a class box per class, on a simple grid ----
    COLS, COL_W, ROW_H = 4, 220, 260
    X0, Y0, W, NAME_H, ROW = 40, 40, 170, 25, 15
    geo: dict[str, tuple[int, int, int, int]] = {}
    cls_view_id = {c["name"]: nid() for c in classes}
    owned_views: list[dict] = []

    def label(parent_id: str, text: str, x: int, y: int, w: int,
              bold: bool = False, visible: bool = True) -> dict:
        lv = {"_type": "LabelView", "_id": nid(), "_parent": ref(parent_id),
              "font": f"Arial;13;{1 if bold else 0}", "parentStyle": True,
              "left": x, "top": y, "width": w, "height": 13, "text": text}
        if not visible:
            lv["visible"] = False
        return lv

    for idx, cls in enumerate(classes):
        name = cls["name"]
        cvid, cmodel = cls_view_id[name], ref(cls_id[name])
        col, row = idx % COLS, idx // COLS
        x, y = X0 + col * COL_W, Y0 + row * ROW_H
        n_attr, n_op = len(cls.get("attributes", [])), len(cls.get("methods", []))
        attr_h = ROW * n_attr if n_attr else 10
        op_h = ROW * n_op if n_op else 10
        total_h = NAME_H + attr_h + op_h
        geo[name] = (x, y, W, total_h)

        ncid = nid()
        st_l = label(ncid, "", x + 5, y + 6, W - 10, visible=False)
        nm_l = label(ncid, name, x + 5, y + 6, W - 10, bold=True)
        ns_l = label(ncid, f"(from {diagram_name})", x + 5, y + 6, W - 10, visible=False)
        pr_l = label(ncid, "", x + 5, y + 6, W - 10, visible=False)
        name_comp = {"_type": "UMLNameCompartmentView", "_id": ncid, "_parent": ref(cvid),
                     "model": cmodel, "font": "Arial;13;0", "parentStyle": True,
                     "left": x, "top": y, "width": W, "height": NAME_H,
                     "stereotypeLabel": ref(st_l["_id"]), "nameLabel": ref(nm_l["_id"]),
                     "namespaceLabel": ref(ns_l["_id"]), "propertyLabel": ref(pr_l["_id"]),
                     "subViews": [st_l, nm_l, ns_l, pr_l]}

        acid = nid()
        attr_views = [{
            "_type": "UMLAttributeView", "_id": nid(), "_parent": ref(acid),
            "model": ref(attr_ids[name][i]), "font": "Arial;13;0", "parentStyle": True,
            "left": x + 5, "top": y + NAME_H + 5 + i * ROW, "width": W - 10,
            "height": 13, "text": _plant_member(a, False), "horizontalAlignment": 0,
        } for i, a in enumerate(cls.get("attributes", []))]
        attr_comp = {"_type": "UMLAttributeCompartmentView", "_id": acid, "_parent": ref(cvid),
                     "model": cmodel, "font": "Arial;13;0", "parentStyle": True,
                     "left": x, "top": y + NAME_H, "width": W,
                     "height": attr_h, "subViews": attr_views}

        ocid = nid()
        op_views = [{
            "_type": "UMLOperationView", "_id": nid(), "_parent": ref(ocid),
            "model": ref(op_ids[name][i]), "font": "Arial;13;0", "parentStyle": True,
            "left": x + 5, "top": y + NAME_H + attr_h + 5 + i * ROW, "width": W - 10,
            "height": 13, "text": _plant_member(m, True), "horizontalAlignment": 0,
        } for i, m in enumerate(cls.get("methods", []))]
        op_comp = {"_type": "UMLOperationCompartmentView", "_id": ocid, "_parent": ref(cvid),
                   "model": cmodel, "font": "Arial;13;0", "parentStyle": True,
                   "left": x, "top": y + NAME_H + attr_h, "width": W,
                   "height": op_h, "subViews": op_views}

        rcid, tcid = nid(), nid()
        reception_comp = {"_type": "UMLReceptionCompartmentView", "_id": rcid,
                          "_parent": ref(cvid), "model": cmodel, "visible": False,
                          "font": "Arial;13;0", "parentStyle": True,
                          "width": 10, "height": 10}
        template_comp = {"_type": "UMLTemplateParameterCompartmentView", "_id": tcid,
                         "_parent": ref(cvid), "model": cmodel, "visible": False,
                         "font": "Arial;13;0", "parentStyle": True,
                         "width": 10, "height": 10}

        owned_views.append({
            "_type": "UMLClassView", "_id": cvid, "_parent": ref(diagram_id),
            "model": cmodel, "font": "Arial;13;0", "parentStyle": True,
            "left": x, "top": y, "width": W, "height": total_h,
            "containerChangeable": True,
            "nameCompartment": ref(ncid), "attributeCompartment": ref(acid),
            "operationCompartment": ref(ocid), "receptionCompartment": ref(rcid),
            "templateParameterCompartment": ref(tcid),
            "subViews": [name_comp, attr_comp, op_comp, reception_comp, template_comp],
        })

    # ---- view: one edge per relationship ----
    def center(name: str) -> tuple[int, int]:
        x, y, w, h = geo[name]
        return x + w // 2, y + h // 2

    def edge_label(edge_id: str, model_ref: dict, text: str = "",
                   visible: bool = False) -> dict:
        el = {"_type": "EdgeLabelView", "_id": nid(), "_parent": ref(edge_id),
              "model": model_ref, "font": "Arial;13;0", "alpha": 1.5707963267948966,
              "distance": 15, "edgePosition": 1, "hostEdge": ref(edge_id), "text": text}
        if not visible:
            el["visible"] = False
        return el

    for rel, rid, vtype, end_ids in rel_specs:
        src, tgt, eid, rmodel = rel["from"], rel["to"], nid(), ref(rid)
        sx, sy = center(src)
        hx, hy = center(tgt)
        name_text = rel.get("label", "")
        nl = edge_label(eid, rmodel, name_text, visible=bool(name_text))
        sl, pl = edge_label(eid, rmodel), edge_label(eid, rmodel)
        sub = [nl, sl, pl]
        edge = {"_type": vtype, "_id": eid, "_parent": ref(diagram_id), "model": rmodel,
                "font": "Arial;13;0", "parentStyle": False,
                "tail": ref(cls_view_id[src]), "head": ref(cls_view_id[tgt]),
                "lineStyle": 1, "points": f"{sx}:{sy};{hx}:{hy}",
                "nameLabel": ref(nl["_id"]), "stereotypeLabel": ref(sl["_id"]),
                "propertyLabel": ref(pl["_id"])}
        if vtype == "UMLAssociationView":
            for key in ("tailRoleNameLabel", "tailPropertyLabel", "tailMultiplicityLabel",
                        "headRoleNameLabel", "headPropertyLabel", "headMultiplicityLabel"):
                lbl = edge_label(eid, rmodel)
                sub.append(lbl)
                edge[key] = ref(lbl["_id"])
            e1id, e2id = end_ids                 # qualifier compartments hang off the ends
            tq = {"_type": "UMLQualifierCompartmentView", "_id": nid(), "_parent": ref(eid),
                  "model": ref(e1id), "visible": False, "font": "Arial;13;0",
                  "parentStyle": True, "width": 10, "height": 10}
            hq = {"_type": "UMLQualifierCompartmentView", "_id": nid(), "_parent": ref(eid),
                  "model": ref(e2id), "visible": False, "font": "Arial;13;0",
                  "parentStyle": True, "width": 10, "height": 10}
            sub += [tq, hq]
            edge["tailQualifiersCompartment"] = ref(tq["_id"])
            edge["headQualifiersCompartment"] = ref(hq["_id"])
            edge["showEndOrder"] = "hide"
            edge["showVisibility"] = True
        edge["subViews"] = sub
        owned_views.append(edge)

    diagram = {"_type": "UMLClassDiagram", "_id": diagram_id, "_parent": ref(model_id),
               "name": diagram_name, "ownedViews": owned_views}
    model = {"_type": "UMLModel", "_id": model_id, "_parent": ref(project_id),
             "name": diagram_name, "ownedElements": model_classes + [diagram]}
    project = {"_type": "Project", "_id": project_id, "name": diagram_name,
               "documentVersion": 1, "ownedElements": [model]}
    return json.dumps(project, indent=2, ensure_ascii=False)


RENDERERS = {"mermaid": to_mermaid, "plantuml": to_plantuml,
             "drawio": to_drawio, "staruml": to_staruml}


def render(slug: str, fmt: str) -> str:
    return RENDERERS[fmt](load(slug))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pattern", nargs="?", help="pattern slug or title (e.g. observer)")
    parser.add_argument("-f", "--format", choices=RENDERERS, default="mermaid")
    parser.add_argument("-o", "--out", metavar="FILE",
                        help="write the diagram to FILE as UTF-8 (no BOM) instead of "
                             "printing it. Use this for .drawio/.mdj on Windows, where "
                             "PowerShell's '>' would write UTF-16 and break the file.")
    parser.add_argument("--list", action="store_true", help="list available patterns")
    parser.add_argument("--all", action="store_true", help="render every pattern")
    args = parser.parse_args()

    def emit(text: str) -> None:
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")  # UTF-8, no BOM
            print(f"Wrote {args.out}", file=sys.stderr)
        else:
            print(text)

    files = available()
    if args.list:
        for slug in files:
            print(slug)
        return

    if args.all:
        chunks = [f"# {slug}\n{render(slug, args.format)}" for slug in files]
        emit("\n\n".join(chunks))
        return

    if not args.pattern:
        parser.error("give a pattern slug/title, or use --list or --all")

    slug = slugify(args.pattern)
    if slug not in files:
        print(f"Unknown pattern: {args.pattern!r} (slug {slug!r}). "
              f"Try --list.", file=sys.stderr)
        raise SystemExit(1)
    emit(render(slug, args.format))


if __name__ == "__main__":
    main()
