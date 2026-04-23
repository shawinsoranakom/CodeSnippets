def _extract_drawing_math(zf, sheet_index: int) -> list:
    """Extract LaTeX formulas from drawing layer of an xlsx sheet.

    Args:
        zf: An already-opened zipfile.ZipFile object.
        sheet_index: Zero-based sheet index.
    """
    from lxml import etree

    results = []
    rels_path = f"xl/worksheets/_rels/sheet{sheet_index + 1}.xml.rels"

    # Read rels (file may not exist if sheet has no drawing)
    try:
        rels_data = zf.read(rels_path)
    except KeyError:
        return results

    # Find drawing relationship targets
    rels_root = etree.fromstring(rels_data)
    drawing_targets = []
    for rel in rels_root.findall(f"{{{_REL_NS}}}Relationship"):
        if rel.get("Type") == _REL_DRAWING:
            target = rel.get("Target", "")
            # "../drawings/drawingX.xml" → "xl/drawings/drawingX.xml"
            if target.startswith("../"):
                target = "xl/" + target[3:]
            elif not target.startswith("xl/"):
                target = "xl/worksheets/" + target
            drawing_targets.append(target)

    for drawing_path in drawing_targets:
        try:
            drawing_data = zf.read(drawing_path)
            drawing_root = etree.fromstring(drawing_data)
        except Exception:
            continue  # silently skip corrupted or missing drawing

        # Iterate over a:p paragraphs under mc:AlternateContent/mc:Choice
        for alt in drawing_root.iter(f"{_MC}AlternateContent"):
            choice = alt.find(f"{_MC}Choice")
            if choice is None:
                continue
            for para in choice.iter(f"{_A}p"):
                if _paragraph_has_math(para):
                    results.extend(_extract_math_from_paragraph(para))

    return results