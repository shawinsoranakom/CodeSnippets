def _resort_page_with_layout(page_blocks: list[dict], layout_regions: list[dict]) -> list[dict]:
    if not page_blocks:
        return []

    if not layout_regions:
        return sorted(page_blocks, key=lambda b: (
            (b.get("top", 0) + b.get("bottom", 0)) / 2,
            (b.get("x0", 0) + b.get("x1", 0)) / 2,
        ))

    type_groups: dict[str, list] = {}
    for lt in layout_regions:
        tp = lt.get("type", "")
        type_groups.setdefault(tp, []).append(lt)
    entries = []
    for tp, group in type_groups.items():
        for idx, lt in enumerate(group):
            key = f"{tp}-{idx}"
            x0, x1 = lt.get("x0", 0), lt.get("x1", 0)
            top, bottom = lt.get("top", 0), lt.get("bottom", 0)
            entries.append({
                "key": key, "type": tp,
                "x0": x0, "top": top, "x1": x1, "bottom": bottom,
                "cy": (top + bottom) / 2, "cx": (x0 + x1) / 2,
            })

    for b in page_blocks:
        if b.get("layoutno"):
            continue
        b_cx = (b.get("x0", 0) + b.get("x1", 0)) / 2
        b_cy = (b.get("top", 0) + b.get("bottom", 0)) / 2
        for entry in entries:
            if (entry["x0"] <= b_cx <= entry["x1"]
                    and entry["top"] <= b_cy <= entry["bottom"]):
                b["layoutno"] = entry["key"]
                b["layout_type"] = entry["type"]
                break

    for entry in entries:
        layout_key = entry["key"]
        layout_area = (entry["x1"] - entry["x0"]) * (entry["bottom"] - entry["top"])
        if layout_area <= 0:
            continue
        layout_blocks = [b for b in page_blocks if b.get("layoutno") == layout_key]
        if not layout_blocks:
            continue
        text_total_area = sum(
            (b.get("x1", 0) - b.get("x0", 0)) * (b.get("bottom", 0) - b.get("top", 0))
            for b in layout_blocks
        )
        if text_total_area / layout_area < 0.075:
            for b in layout_blocks:
                b["layoutno"] = ""
                b["layout_type"] = ""

    entry_map = {e["key"]: e for e in entries}
    for b in page_blocks:
        b_cx = (b.get("x0", 0) + b.get("x1", 0)) / 2
        b_cy = (b.get("top", 0) + b.get("bottom", 0)) / 2
        b["_x_center"] = b_cx
        b["_y_center"] = b_cy
        layoutno = b.get("layoutno", "")
        if layoutno and layoutno in entry_map:
            b["_lx_center"] = entry_map[layoutno]["cx"]
            b["_ly_center"] = entry_map[layoutno]["cy"]
        else:
            b["_lx_center"] = b_cx
            b["_ly_center"] = b_cy

    active_keys = {b.get("layoutno") for b in page_blocks if b.get("layoutno")}
    active_entries = [e for e in entries if e["key"] in active_keys]

    for b in page_blocks:
        if b.get("layoutno"):
            continue
        if not active_entries:
            continue
        b_cx, b_cy = b["_x_center"], b["_y_center"]
        min_dist = float("inf")
        best_cx, best_cy = b_cx, b_cy
        for ae in active_entries:
            lx1, ly1, lx2, ly2 = ae["x0"], ae["top"], ae["x1"], ae["bottom"]
            if b_cy < ly1:
                dy = ly1 - b_cy
            elif b_cy > ly2:
                dy = b_cy - ly2
            else:
                dy = 0
            if b_cx < lx1:
                dx = lx1 - b_cx
            elif b_cx > lx2:
                dx = b_cx - lx2
            else:
                dx = 0
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                best_cx, best_cy = ae["cx"], ae["cy"]
        b["_lx_center"] = best_cx
        b["_ly_center"] = best_cy

    sorted_blocks = sorted(page_blocks, key=lambda b: (
        b.get("_ly_center", 0),
        b.get("_lx_center", 0),
        b.get("_y_center", 0),
        b.get("_x_center", 0),
    ))

    for b in sorted_blocks:
        b.pop("_ly_center", None)
        b.pop("_lx_center", None)
        b.pop("_y_center", None)
        b.pop("_x_center", None)

    return sorted_blocks