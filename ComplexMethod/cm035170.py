def _build_numbering_map(doc) -> dict:
    """Parse numbering.xml and return {numId: {ilvl: numFmt}} mapping."""
    numbering_map = {}
    try:
        numbering_part = doc.part.numbering_part
    except Exception:
        return numbering_map
    numbering_elem = numbering_part._element

    # Build abstractNumId -> {ilvl: numFmt}
    abstract = {}
    for abs_num in numbering_elem.findall(f"{_W}abstractNum"):
        abs_id = abs_num.get(f"{_W}abstractNumId")
        levels = {}
        for lvl in abs_num.findall(f"{_W}lvl"):
            ilvl = int(lvl.get(f"{_W}ilvl", "0"))
            fmt_elem = lvl.find(f"{_W}numFmt")
            fmt = (
                fmt_elem.get(f"{_W}val", "bullet") if fmt_elem is not None else "bullet"
            )
            levels[ilvl] = fmt
        abstract[abs_id] = levels

    # Map numId -> abstractNumId
    for num in numbering_elem.findall(f"{_W}num"):
        num_id = num.get(f"{_W}numId")
        abs_ref = num.find(f"{_W}abstractNumId")
        if abs_ref is not None:
            abs_id = abs_ref.get(f"{_W}val")
            if abs_id in abstract:
                numbering_map[num_id] = abstract[abs_id]
    return numbering_map